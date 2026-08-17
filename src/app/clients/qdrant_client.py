from __future__ import annotations

from qdrant_client import AsyncQdrantClient
from qdrant_client.http import models as qdrant_models

from app.domain.models import RetrievedChunk


class QdrantVectorStore:
    def __init__(self, url: str, collection_name: str, api_key: str | None = None) -> None:
        self._client = AsyncQdrantClient(url=url, api_key=api_key)
        self._collection_name = collection_name
        self._ensured = False
        self._document_hashes: dict[tuple[str, str], str] = {}
        self._documents: dict[tuple[str, str], dict] = {}

    async def ensure_collection(self, vector_size: int) -> None:
        """Create the collection if it does not already exist. Idempotent after first success."""
        if self._ensured:
            return
        existing = await self._client.get_collections()
        names = {c.name for c in existing.collections}
        if self._collection_name not in names:
            await self._client.create_collection(
                collection_name=self._collection_name,
                vectors_config=qdrant_models.VectorParams(
                    size=vector_size,
                    distance=qdrant_models.Distance.COSINE,
                ),
            )
        self._ensured = True

    async def upsert(self, chunks: list[dict]) -> None:
        """
        Insert or update chunks in the collection.

        Each dict must contain:
          - chunk_id (str)
          - vector (list[float])
          - payload (dict) with provenance metadata
        """
        points = [
            qdrant_models.PointStruct(
                id=_chunk_id_to_int(item["chunk_id"]),
                vector=item["vector"],
                payload={**item["payload"], "chunk_id": item["chunk_id"]},
            )
            for item in chunks
        ]
        await self._client.upsert(collection_name=self._collection_name, points=points)

    async def search(self, query_vector: list[float], limit: int = 5, workspace_id: str | None = None) -> list[RetrievedChunk]:
        """Return the top-k most similar chunks for a query embedding."""
        response = await self._client.query_points(
            collection_name=self._collection_name,
            query=query_vector,
            limit=limit,
            with_payload=True,
            query_filter=qdrant_models.Filter(must=[qdrant_models.FieldCondition(key="workspace_id", match=qdrant_models.MatchValue(value=workspace_id or "local"))]),
        )
        chunks = []
        for hit in response.points:
            p = hit.payload or {}
            chunks.append(
                RetrievedChunk(
                    chunk_id=p.get("chunk_id", str(hit.id)),
                    doc_id=p.get("doc_id", ""),
                    source_path=p.get("source_path", ""),
                    text=p.get("text", ""),
                    score=hit.score,
                    title=p.get("title"),
                    page=p.get("page"),
                    section=p.get("section"),
                )
            )
        return chunks

    async def health_check(self) -> bool:
        """Return True if Qdrant is reachable."""
        try:
            await self._client.get_collections()
            return True
        except Exception:
            return False

    async def get_document_hash(self, doc_id: str, workspace_id: str) -> str | None:
        return self._document_hashes.get((workspace_id, doc_id))

    async def replace_document(self, document: dict, chunks: list[dict]) -> None:
        await self._client.delete(
            collection_name=self._collection_name,
            points_selector=qdrant_models.Filter(
                must=[
                    qdrant_models.FieldCondition(key="doc_id", match=qdrant_models.MatchValue(value=document["doc_id"])),
                    qdrant_models.FieldCondition(key="workspace_id", match=qdrant_models.MatchValue(value=document["workspace_id"])),
                ]
            ),
        )
        await self.upsert(chunks)
        key = (document["workspace_id"], document["doc_id"])
        self._document_hashes[key] = document["content_hash"]
        self._documents[key] = document

    async def delete_missing_documents(self, root_path: str, workspace_id: str, present_doc_ids: list[str]) -> int:
        stale = [key for key, document in self._documents.items() if document.get("root_path") == root_path and key[0] == workspace_id and key[1] not in present_doc_ids]
        for key in stale:
            document = self._documents.pop(key)
            await self._client.delete(
                collection_name=self._collection_name,
                points_selector=qdrant_models.Filter(
                    must=[qdrant_models.FieldCondition(key="doc_id", match=qdrant_models.MatchValue(value=document["doc_id"]))],
                ),
            )
            self._document_hashes.pop(key, None)
        return len(stale)


def _chunk_id_to_int(chunk_id: str) -> int:
    """Convert a hex chunk ID (sha256 prefix) to an integer Qdrant point ID."""
    hex_part = chunk_id.replace("-", "")[:16]
    return int(hex_part, 16)

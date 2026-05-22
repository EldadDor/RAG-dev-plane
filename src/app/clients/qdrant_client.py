from __future__ import annotations

from qdrant_client import AsyncQdrantClient
from qdrant_client.http import models as qdrant_models

from app.domain.models import RetrievedChunk


_VECTOR_SIZE_CACHE: dict[str, int] = {}


class QdrantVectorStore:
    def __init__(self, url: str, collection_name: str, api_key: str | None = None) -> None:
        self._client = AsyncQdrantClient(url=url, api_key=api_key)
        self._collection_name = collection_name

    async def ensure_collection(self, vector_size: int) -> None:
        """Create the collection if it does not already exist."""
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

    async def search(self, query_vector: list[float], limit: int = 5) -> list[RetrievedChunk]:
        """Return the top-k most similar chunks for a query embedding."""
        results = await self._client.search(
            collection_name=self._collection_name,
            query_vector=query_vector,
            limit=limit,
            with_payload=True,
        )
        chunks = []
        for hit in results:
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


def _chunk_id_to_int(chunk_id: str) -> int:
    """Convert a hex chunk ID (sha256 prefix) to an integer Qdrant point ID."""
    # Use the first 16 hex chars of the chunk_id as an unsigned 64-bit integer
    hex_part = chunk_id.replace("-", "")[:16]
    return int(hex_part, 16)

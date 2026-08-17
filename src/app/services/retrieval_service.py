from app.clients.embedding_client import EmbeddingClient
from app.clients.vector_store import LexicalSearchVectorStore, VectorStore
from app.config import Settings
from app.domain.models import RetrievedChunk


class RetrievalService:
    def __init__(self, settings: Settings, embedding_client: EmbeddingClient, vector_store: VectorStore) -> None:
        self._settings = settings
        self._embedding_client = embedding_client
        self._vector_store = vector_store

    async def retrieve(self, question: str, top_k: int | None = None, workspace_id: str | None = None) -> list[RetrievedChunk]:
        embedding = await self._embedding_client.create_embedding(self._settings.embedding_model, question)
        limit = top_k or self._settings.top_k
        candidate_limit = max(limit, self._settings.retrieval_candidate_k)
        semantic = await self._vector_store.search(embedding, limit=candidate_limit, workspace_id=workspace_id or self._settings.default_workspace_id)
        # Avoid treating unrelated semantic matches as grounded evidence.
        semantic = [item for item in semantic if item.score >= self._settings.min_retrieval_score]

        if not self._settings.hybrid_search_enabled or not isinstance(self._vector_store, LexicalSearchVectorStore):
            return semantic[:limit]

        lexical = await self._vector_store.search_text(question, limit=candidate_limit, workspace_id=workspace_id or self._settings.default_workspace_id)
        return self._reciprocal_rank_fusion(semantic, lexical, limit)

    def _reciprocal_rank_fusion(
        self,
        semantic: list[RetrievedChunk],
        lexical: list[RetrievedChunk],
        limit: int,
    ) -> list[RetrievedChunk]:
        """Fuse semantic and keyword rankings without comparing incompatible scores."""
        scores: dict[str, float] = {}
        chunks: dict[str, RetrievedChunk] = {}
        for results in (semantic, lexical):
            for rank, chunk in enumerate(results, start=1):
                scores[chunk.chunk_id] = scores.get(chunk.chunk_id, 0.0) + 1.0 / (self._settings.rrf_k + rank)
                chunks.setdefault(chunk.chunk_id, chunk)

        ranked_ids = sorted(scores, key=lambda chunk_id: scores[chunk_id], reverse=True)[:limit]
        return [chunks[chunk_id] for chunk_id in ranked_ids]

import logging

from app.clients.embedding_client import EmbeddingClient
from app.clients.vector_store import LexicalSearchVectorStore, VectorStore
from app.config import Settings
from app.domain.models import RetrievedChunk
from app.rerankers import LocalCrossEncoderReranker, Reranker, RerankerUnavailable
from app.services.model_profiles import (
    CachedEmbeddingClient,
    EmbeddingCache,
    InMemoryEmbeddingCache,
    ModelProfileStore,
    ModelProfileUnavailable,
)


logger = logging.getLogger(__name__)


class RetrievalService:
    def __init__(
        self,
        settings: Settings,
        embedding_client: EmbeddingClient,
        vector_store: VectorStore,
        reranker: Reranker | None = None,
        model_profile_store: ModelProfileStore | None = None,
        embedding_cache: EmbeddingCache | None = None,
    ) -> None:
        self._settings = settings
        self._embedding_client = embedding_client
        self._vector_store = vector_store
        self._reranker = reranker or LocalCrossEncoderReranker(settings.rerank_model)
        self._model_profile_store = model_profile_store
        self._embedding_cache = embedding_cache

    async def retrieve(self, question: str, top_k: int | None = None, workspace_id: str | None = None, chunking_profile: str | None = None, model_profile: str | None = None) -> list[RetrievedChunk]:
        vector_store = self._vector_store
        if self._model_profile_store is None:
            embedding = await self._embedding_client.create_embedding(self._settings.embedding_model, question)
        else:
            profile_name = model_profile or self._settings.model_profile
            profile = await self._model_profile_store.get(profile_name)
            if profile is None:
                raise ModelProfileUnavailable(f"Unknown model profile: {profile_name}")
            if profile.status != "ready":
                raise ModelProfileUnavailable(f"Model profile {profile_name!r} is not ready")
            if profile.provider != self._settings.embedding_provider:
                raise ModelProfileUnavailable(
                    f"Model profile {profile_name!r} requires provider {profile.provider!r}"
                )
            if not hasattr(vector_store, "for_profile"):
                raise ModelProfileUnavailable("Per-request model profiles require PostgreSQL storage")
            vector_store = await vector_store.for_profile(profile.storage_target, profile.dimensions)
            cache = self._embedding_cache or InMemoryEmbeddingCache()
            embedding = await CachedEmbeddingClient(
                self._embedding_client, cache, profile
            ).create_query_embedding(question)
        limit = top_k or self._settings.top_k
        candidate_limit = max(
            limit,
            self._settings.retrieval_candidate_k,
            self._settings.rerank_candidate_k if self._settings.rerank_enabled else 0,
        )
        profile_name, _ = self._settings.chunking_profile(chunking_profile)
        semantic = await vector_store.search(embedding, limit=candidate_limit, workspace_id=workspace_id or self._settings.default_workspace_id, chunking_profile=profile_name)
        # Avoid treating unrelated semantic matches as grounded evidence.
        semantic = [item for item in semantic if item.score >= self._settings.min_retrieval_score]

        if not self._settings.hybrid_search_enabled or not isinstance(vector_store, LexicalSearchVectorStore):
            return await self._rerank_or_trim(question, semantic, limit)

        lexical = await vector_store.search_text(question, limit=candidate_limit, workspace_id=workspace_id or self._settings.default_workspace_id, chunking_profile=profile_name)
        fused = self._reciprocal_rank_fusion(semantic, lexical, candidate_limit)
        return await self._rerank_or_trim(question, fused, limit)

    async def _rerank_or_trim(
        self, question: str, candidates: list[RetrievedChunk], limit: int
    ) -> list[RetrievedChunk]:
        """Apply the optional stage without changing disabled-mode behavior."""
        if not self._settings.rerank_enabled:
            return candidates[:limit]
        try:
            return (await self._reranker.rerank(question, candidates))[:limit]
        except RerankerUnavailable as exc:
            logger.warning("Reranking unavailable; returning fused candidate order: %s", exc)
            return candidates[:limit]

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

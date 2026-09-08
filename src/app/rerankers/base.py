from __future__ import annotations

from typing import Protocol

from app.domain.models import RetrievedChunk


class RerankerUnavailable(RuntimeError):
    """The configured optional reranker cannot be used in this environment."""


class Reranker(Protocol):
    """Ranks already-authorized candidates for one retrieval request."""

    async def rerank(self, question: str, chunks: list[RetrievedChunk]) -> list[RetrievedChunk]: ...

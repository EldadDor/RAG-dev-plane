from __future__ import annotations

import asyncio
from dataclasses import replace
from typing import Any

from app.domain.models import RetrievedChunk
from app.rerankers.base import RerankerUnavailable


class LocalCrossEncoderReranker:
    """Lazy sentence-transformers cross-encoder adapter.

    Importing this module neither imports torch nor downloads a model. Loading
    occurs only after reranking has been explicitly enabled for a request.
    """

    def __init__(self, model_name: str) -> None:
        self._model_name = model_name
        self._model: Any | None = None

    def _load_model(self) -> Any:
        if self._model is not None:
            return self._model
        try:
            from sentence_transformers import CrossEncoder
        except ImportError as exc:
            raise RerankerUnavailable(
                "Local reranking requires the optional 'rerank' dependency. "
                "Install it with: uv sync --extra rerank"
            ) from exc
        try:
            self._model = CrossEncoder(self._model_name)
        except Exception as exc:
            raise RerankerUnavailable(
                f"Unable to load local reranker model {self._model_name!r}: {exc}"
            ) from exc
        return self._model

    def _rerank_sync(self, question: str, chunks: list[RetrievedChunk]) -> list[RetrievedChunk]:
        model = self._load_model()
        try:
            scores = model.predict([(question, chunk.text) for chunk in chunks])
        except Exception as exc:
            raise RerankerUnavailable(f"Local reranker prediction failed: {exc}") from exc
        scored = [(index, chunk, float(score)) for index, (chunk, score) in enumerate(zip(chunks, scores, strict=True))]
        scored.sort(key=lambda item: (-item[2], item[0]))
        return [replace(chunk, score=score) for _, chunk, score in scored]

    async def rerank(self, question: str, chunks: list[RetrievedChunk]) -> list[RetrievedChunk]:
        if not chunks:
            return []
        return await asyncio.to_thread(self._rerank_sync, question, chunks)

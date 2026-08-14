import logging
import time
from typing import Protocol

import httpx

logger = logging.getLogger(__name__)


class EmbeddingClient(Protocol):
    async def create_embedding(self, model: str, text: str) -> list[float]: ...


class OllamaEmbeddingClient:
    def __init__(self, base_url: str, timeout: float = 120.0) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout

    async def create_embedding(self, model: str, text: str) -> list[float]:
        started = time.perf_counter()
        logger.info("Embedding request started | provider=ollama model=%s input_chars=%d timeout_seconds=%.1f", model, len(text), self._timeout)
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.post(
                    f"{self._base_url}/api/embed", json={"model": model, "input": text}
                )
                response.raise_for_status()
                payload = response.json()
            if "embeddings" in payload and payload["embeddings"]:
                embedding = payload["embeddings"][0]
            elif "embedding" in payload:
                embedding = payload["embedding"]
            else:
                raise ValueError("Unexpected Ollama embedding response format")
        except Exception as exc:
            logger.warning("Embedding request failed | provider=ollama model=%s duration_ms=%d error_type=%s", model, (time.perf_counter() - started) * 1000, type(exc).__name__)
            raise
        logger.info("Embedding request completed | provider=ollama model=%s status=%d duration_ms=%d dimensions=%d", model, response.status_code, (time.perf_counter() - started) * 1000, len(embedding))
        return embedding

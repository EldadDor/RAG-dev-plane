from typing import Protocol

import httpx


class EmbeddingClient(Protocol):
    async def create_embedding(self, model: str, text: str) -> list[float]: ...


class OllamaEmbeddingClient:
    def __init__(self, base_url: str, timeout: float = 30.0) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout

    async def create_embedding(self, model: str, text: str) -> list[float]:
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.post(
                f"{self._base_url}/api/embed",
                json={"model": model, "input": text},
            )
            response.raise_for_status()
            payload = response.json()
            if "embeddings" in payload and payload["embeddings"]:
                return payload["embeddings"][0]
            if "embedding" in payload:
                return payload["embedding"]
            raise ValueError("Unexpected Ollama embedding response format")

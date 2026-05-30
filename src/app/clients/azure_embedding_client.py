"""Azure OpenAI embedding client.

Calls: POST {endpoint}/openai/deployments/{model}/embeddings?api-version=...

Auth:
  - api-key header  (AZURE_OPENAI_USE_ENTRA=false, default)
  - Bearer Entra token  (AZURE_OPENAI_USE_ENTRA=true, Managed Identity / az login)
"""

from __future__ import annotations

import httpx


class AzureOpenAIEmbeddingClient:
    def __init__(
        self,
        endpoint: str,
        api_version: str,
        api_key: str | None = None,
        use_entra: bool = False,
        timeout: float = 30.0,
    ) -> None:
        self._endpoint = endpoint.rstrip("/")
        self._api_version = api_version
        self._api_key = api_key
        self._use_entra = use_entra
        self._timeout = timeout

    def _headers(self) -> dict[str, str]:
        if self._use_entra:
            from app.clients.azure_auth import get_azure_openai_token
            return {"Authorization": f"Bearer {get_azure_openai_token()}", "Content-Type": "application/json"}
        return {"api-key": self._api_key or "", "Content-Type": "application/json"}

    async def create_embedding(self, model: str, text: str) -> list[float]:
        url = (
            f"{self._endpoint}/openai/deployments/{model}"
            f"/embeddings?api-version={self._api_version}"
        )
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.post(url, headers=self._headers(), json={"input": text})
            response.raise_for_status()
            return response.json()["data"][0]["embedding"]

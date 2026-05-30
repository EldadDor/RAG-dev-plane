"""Azure OpenAI chat completion client.

Calls: POST {endpoint}/openai/deployments/{deployment}/chat/completions?api-version=...

The `model` argument passed to create_chat_completion is the Azure *deployment name*
(configured via CHAT_MODEL). It goes in the URL path, not the request body.

Auth:
  - api-key header  (AZURE_OPENAI_USE_ENTRA=false, default)
  - Bearer Entra token  (AZURE_OPENAI_USE_ENTRA=true, Managed Identity / az login)
"""

from __future__ import annotations

from typing import Any

import httpx

from app.prompts.chat_prompt import SYSTEM_PROMPT


class AzureOpenAIChatClient:
    def __init__(
        self,
        endpoint: str,
        api_version: str,
        api_key: str | None = None,
        use_entra: bool = False,
        timeout: float = 60.0,
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

    async def create_chat_completion(self, model: str, prompt: str) -> dict[str, Any]:
        """Send a chat completion request. `model` is the Azure deployment name."""
        url = (
            f"{self._endpoint}/openai/deployments/{model}"
            f"/chat/completions?api-version={self._api_version}"
        )
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.post(
                url,
                headers=self._headers(),
                json={
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": 0,
                },
            )
            response.raise_for_status()
            return response.json()

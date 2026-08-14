"""Azure OpenAI chat completion client.

Calls: POST {endpoint}/openai/deployments/{deployment}/chat/completions?api-version=...

The `model` argument passed to create_chat_completion is the Azure *deployment name*
(configured via CHAT_MODEL). It goes in the URL path, not the request body.

Auth:
  - api-key header  (AZURE_OPENAI_USE_ENTRA=false, default)
  - Bearer Entra token  (AZURE_OPENAI_USE_ENTRA=true, Managed Identity / az login)
"""

from __future__ import annotations

import logging
import time
from typing import Any

import httpx

from app.prompts.chat_prompt import SYSTEM_PROMPT

logger = logging.getLogger(__name__)


class AzureOpenAIChatClient:
    def __init__(
        self,
        endpoint: str,
        api_version: str,
        api_key: str | None = None,
        use_entra: bool = False,
        timeout: float = 240.0,
        max_tokens: int = 400,
    ) -> None:
        self._endpoint = endpoint.rstrip("/")
        self._api_version = api_version
        self._api_key = api_key
        self._use_entra = use_entra
        self._timeout = timeout
        self._max_tokens = max_tokens

    def _headers(self) -> dict[str, str]:
        if self._use_entra:
            from app.clients.azure_auth import get_azure_openai_token
            return {"Authorization": f"Bearer {get_azure_openai_token()}", "Content-Type": "application/json"}
        return {"api-key": self._api_key or "", "Content-Type": "application/json"}

    async def create_chat_completion(
        self, model: str, prompt: str, system_prompt: str = SYSTEM_PROMPT
    ) -> dict[str, Any]:
        """Send a chat completion request. `model` is the Azure deployment name."""
        url = (
            f"{self._endpoint}/openai/deployments/{model}"
            f"/chat/completions?api-version={self._api_version}"
        )
        started = time.perf_counter()
        logger.info("Chat request started | provider=azure_openai model=%s prompt_chars=%d timeout_seconds=%.1f max_tokens=%d", model, len(prompt), self._timeout, self._max_tokens)
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.post(
                    url, headers=self._headers(), json={
                        "messages": [{"role": "system", "content": system_prompt}, {"role": "user", "content": prompt}],
                        "temperature": 0, "max_tokens": self._max_tokens,
                    },
                )
                response.raise_for_status()
                payload = response.json()
        except Exception as exc:
            logger.warning("Chat request failed | provider=azure_openai model=%s duration_ms=%d error_type=%s", model, (time.perf_counter() - started) * 1000, type(exc).__name__)
            raise
        logger.info("Chat request completed | provider=azure_openai model=%s status=%d duration_ms=%d output_chars=%d", model, response.status_code, (time.perf_counter() - started) * 1000, len(payload.get("choices", [{}])[0].get("message", {}).get("content", "")))
        return payload

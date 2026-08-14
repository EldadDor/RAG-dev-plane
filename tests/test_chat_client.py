import json

import pytest

from app.clients.chat_client import OpenAICompatibleChatClient


@pytest.mark.asyncio
async def test_ollama_compatible_chat_request_uses_limits_and_thinking_control(httpx_mock):
    httpx_mock.add_response(json={"choices": [{"message": {"content": "Answer"}}]})
    client = OpenAICompatibleChatClient(
        base_url="http://ollama.test/v1",
        api_key="dummy",
        timeout=240,
        max_tokens=400,
        think=False,
    )

    response = await client.create_chat_completion("llama3.2:3b", "What is RAG?")

    request = httpx_mock.get_request()
    assert request is not None
    payload = json.loads(request.content)
    assert payload["max_tokens"] == 400
    assert payload["think"] is False
    assert response["choices"][0]["message"]["content"] == "Answer"

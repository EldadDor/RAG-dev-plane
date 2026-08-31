import json
from unittest.mock import AsyncMock

import pytest

from app.config import Settings
from app.services.chat_service import ChatService


class _NoopRetrieval:
    async def retrieve(self, **_kwargs):
        return []


@pytest.mark.asyncio
async def test_answer_stream_uses_named_json_events_and_preserves_whitespace():
    service = ChatService(Settings(), _NoopRetrieval(), AsyncMock())

    events = [
        event
        async for event in service.answer_stream(
            question="What is the release procedure?", workspace_id="local"
        )
    ]

    answer_events = [event for event in events if event.startswith("event: answer\n")]
    assert answer_events
    answer = "".join(json.loads(event.split("data: ", 1)[1])['delta'] for event in answer_events)
    assert answer == "I don't know based on the indexed documents."
    assert events[-2].startswith("event: meta\n")
    assert events[-1] == 'event: done\ndata: {"reason":"completed"}\n\n'

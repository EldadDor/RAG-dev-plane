import pytest
from httpx import AsyncClient, ASGITransport

from unittest.mock import AsyncMock, patch

from app.main import app
from app.api.schemas import ChatResponse, SourceReference
from app.domain.models import RetrievedChunk
from app.api.schemas import WarmModelProfileResponse


@pytest.fixture
def mock_chat_service():
    return AsyncMock()


@pytest.mark.asyncio
async def test_health_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


@pytest.mark.asyncio
async def test_chat_returns_abstention_when_no_context():
    mock_service = AsyncMock()
    mock_service.answer.return_value = ChatResponse(
        answer="I don't have enough information in the indexed documents to answer this question.",
        sources=[],
        grounded=False,
    )

    with patch("app.api.routers.chat.get_chat_service", return_value=lambda: mock_service):
        from app.dependencies import get_chat_service
        app.dependency_overrides[get_chat_service] = lambda: mock_service
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/chat", json={"question": "What is Python?"})
        app.dependency_overrides.clear()

    assert response.status_code == 200
    data = response.json()
    assert data["grounded"] is False
    assert data["sources"] == []


@pytest.mark.asyncio
async def test_chat_returns_grounded_answer():
    mock_service = AsyncMock()
    mock_service.answer.return_value = ChatResponse(
        answer="Python is a programming language.",
        sources=[
            SourceReference(
                doc_id="doc1",
                chunk_id="chunk1",
                source_path="docs/python.md",
                score=0.95,
                snippet="Python is...",
            )
        ],
        grounded=True,
    )

    from app.dependencies import get_chat_service
    app.dependency_overrides[get_chat_service] = lambda: mock_service
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/chat", json={"question": "What is Python?"})
    app.dependency_overrides.clear()

    assert response.status_code == 200
    data = response.json()
    assert data["grounded"] is True
    assert len(data["sources"]) == 1


@pytest.mark.asyncio
async def test_chat_validation_rejects_empty_question():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/chat", json={"question": ""})
    assert response.status_code == 422
    assert response.json() == {
        "code": "invalid_request",
        "message": "The request is invalid.",
    }


@pytest.mark.asyncio
async def test_chat_provider_failure_has_safe_error_envelope():
    mock_service = AsyncMock()
    mock_service.answer.side_effect = RuntimeError("provider token: secret")
    from app.dependencies import get_chat_service

    app.dependency_overrides[get_chat_service] = lambda: mock_service
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/chat", json={"question": "What changed?"})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 502
    assert response.json() == {
        "code": "upstream_unavailable",
        "message": "The answer service is temporarily unavailable.",
    }


@pytest.mark.asyncio
async def test_local_profile_warm_endpoint_uses_workspace_scoped_dry_run():
    from app.dependencies import get_model_profile_warmer

    warmer = AsyncMock()
    warmer.warm.return_value = WarmModelProfileResponse(
        profile_name="bge-m3",
        source_model_profile="default",
        workspace_id="local",
        chunks=12,
        cache_hits=12,
        provider_calls=0,
        dry_run=True,
    )
    app.dependency_overrides[get_model_profile_warmer] = lambda: warmer
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/admin/model-profiles/bge-m3/warm", json={"dry_run": True}
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["provider_calls"] == 0
    warmer.warm.assert_awaited_once_with("bge-m3", "default", "local", dry_run=True)


@pytest.mark.asyncio
@pytest.mark.parametrize("route", ["/chat", "/chat/stream"])
@pytest.mark.parametrize("fields", [
    {"document_id": "bad"}, {"document_id": "A" * 64},
    {"document_id": "a" * 64, "session_id": "old"},
    {"document_id": "a" * 64, "session_id": ""},
])
async def test_scoped_chat_validation_rejects_before_streaming(route, fields):
    from app.dependencies import get_chat_service
    service = AsyncMock()
    app.dependency_overrides[get_chat_service] = lambda: service
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(route, json={"question": "Question", **fields})
    finally:
        app.dependency_overrides.clear()
    assert response.status_code == 422
    assert response.json()["code"] == "invalid_request"
    service.answer.assert_not_called()
    service.answer_stream.assert_not_called()


@pytest.mark.asyncio
@pytest.mark.parametrize("route", ["/chat", "/chat/stream"])
async def test_scoped_chat_routes_forward_document_and_return_stateless_response(route):
    from app.dependencies import get_chat_service
    service = AsyncMock()
    service.answer.return_value = ChatResponse(answer="Scoped", sources=[], grounded=False, session_id=None)

    async def stream(**kwargs):
        assert kwargs["document_id"] == "a" * 64
        yield 'event: meta\ndata: {"session_id": null}\n\n'
        yield 'event: done\ndata: {"reason":"completed"}\n\n'

    service.answer_stream = stream
    app.dependency_overrides[get_chat_service] = lambda: service
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(route, json={"question": "Question", "document_id": "a" * 64})
    finally:
        app.dependency_overrides.clear()
    assert response.status_code == 200
    if route == "/chat":
        assert response.json()["session_id"] is None
        assert service.answer.call_args.kwargs["document_id"] == "a" * 64
    else:
        assert '"session_id": null' in response.text

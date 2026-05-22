import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch

from app.main import app
from app.api.schemas import ChatResponse, SourceReference
from app.domain.models import RetrievedChunk


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

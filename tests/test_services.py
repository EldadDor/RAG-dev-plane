import pytest
from unittest.mock import AsyncMock, MagicMock

from app.services.retrieval_service import RetrievalService
from app.services.chat_service import ChatService
from app.domain.models import RetrievedChunk
from app.config import Settings


def _make_settings(**overrides) -> Settings:
    defaults = {
        "CHAT_BASE_URL": "http://localhost:8080/v1",
        "CHAT_MODEL": "test-model",
        "EMBEDDING_MODEL": "test-embed",
        "EMBEDDING_PROVIDER": "ollama",
        "EMBEDDING_BASE_URL": "http://localhost:11434",
        "VECTOR_STORE": "qdrant",
        "QDRANT_URL": "http://localhost:6333",
        "QDRANT_COLLECTION": "test",
        "TOP_K": "5",
        "CHUNK_SIZE": "800",
        "CHUNK_OVERLAP": "120",
    }
    defaults.update(overrides)
    return Settings(**{k: v for k, v in defaults.items()})


@pytest.mark.asyncio
async def test_retrieval_service_calls_embedding_then_vector_store():
    settings = _make_settings()
    embedding_client = AsyncMock()
    embedding_client.create_embedding.return_value = [0.1, 0.2, 0.3]
    vector_store = AsyncMock()
    vector_store.search.return_value = []

    service = RetrievalService(
        settings=settings,
        embedding_client=embedding_client,
        vector_store=vector_store,
    )
    result = await service.retrieve("What is Python?")

    embedding_client.create_embedding.assert_called_once_with("test-embed", "What is Python?")
    vector_store.search.assert_called_once()
    assert result == []


@pytest.mark.asyncio
async def test_chat_service_returns_abstention_when_no_chunks():
    settings = _make_settings()
    retrieval_service = AsyncMock()
    retrieval_service.retrieve.return_value = []
    chat_client = AsyncMock()

    service = ChatService(
        settings=settings,
        retrieval_service=retrieval_service,
        chat_client=chat_client,
    )
    response = await service.answer("What is Python?")

    assert response.grounded is False
    assert response.sources == []
    chat_client.create_chat_completion.assert_not_called()


@pytest.mark.asyncio
async def test_chat_service_returns_answer_with_sources():
    settings = _make_settings()
    chunk = RetrievedChunk(
        chunk_id="abc123",
        doc_id="doc1",
        source_path="docs/python.md",
        text="Python is a programming language.",
        score=0.95,
        title="Python Docs",
    )
    retrieval_service = AsyncMock()
    retrieval_service.retrieve.return_value = [chunk]

    chat_client = AsyncMock()
    chat_client.create_chat_completion.return_value = {
        "choices": [{"message": {"content": "Python is a high-level language."}}]
    }

    service = ChatService(
        settings=settings,
        retrieval_service=retrieval_service,
        chat_client=chat_client,
    )
    response = await service.answer("What is Python?")

    assert response.grounded is True
    assert "Python" in response.answer
    assert len(response.sources) == 1
    assert response.sources[0].doc_id == "doc1"
    assert response.sources[0].score == 0.95


@pytest.mark.asyncio
async def test_chat_service_debug_includes_model_metadata():
    settings = _make_settings()
    chunk = RetrievedChunk(
        chunk_id="abc123",
        doc_id="doc1",
        source_path="docs/python.md",
        text="Python is a programming language.",
        score=0.9,
    )
    retrieval_service = AsyncMock()
    retrieval_service.retrieve.return_value = [chunk]
    chat_client = AsyncMock()
    chat_client.create_chat_completion.return_value = {
        "choices": [{"message": {"content": "Answer."}}]
    }

    service = ChatService(
        settings=settings,
        retrieval_service=retrieval_service,
        chat_client=chat_client,
    )
    response = await service.answer("What is Python?", include_debug=True)

    assert response.debug is not None
    assert "chat_model" in response.debug
    assert "embedding_model" in response.debug
    assert "embedding_provider" in response.debug


@pytest.mark.asyncio
async def test_embedding_client_and_chat_client_are_independent():
    """Verify that retrieval only uses embedding, and chat only uses chat client."""
    settings = _make_settings()
    embedding_client = AsyncMock()
    embedding_client.create_embedding.return_value = [0.5] * 10
    vector_store = AsyncMock()
    vector_store.search.return_value = []

    retrieval_service = RetrievalService(
        settings=settings,
        embedding_client=embedding_client,
        vector_store=vector_store,
    )

    # Chat client should never be called during retrieval
    chat_client = AsyncMock()
    await retrieval_service.retrieve("test query")

    chat_client.create_chat_completion.assert_not_called()
    embedding_client.create_embedding.assert_called_once()

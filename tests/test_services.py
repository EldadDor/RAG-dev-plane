import pytest
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

from app.dependencies import get_chat_service
from app.services.retrieval_service import RetrievalService
from app.services.chat_service import ChatService
from app.domain.models import RetrievedChunk
from app.config import Settings
from app.rerankers import RerankerUnavailable


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
        "HYBRID_SEARCH_ENABLED": "false",
    }
    defaults.update(overrides)
    return Settings(**{k: v for k, v in defaults.items()})


def test_chat_service_dependency_returns_configured_service():
    conversation_store = MagicMock()
    request = SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(conversation_store=conversation_store)))
    retrieval_service = MagicMock()
    chat_client = MagicMock()

    service = get_chat_service(request, _make_settings(), retrieval_service, chat_client)

    assert isinstance(service, ChatService)
    assert service._conversation_store is conversation_store


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
        related_assets=({
            "asset_id": "asset-1", "media_type": "image/png", "width": None,
            "height": None, "alt_text": "Python console", "caption": None,
        },),
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
    assert response.sources[0].assets[0].content_url == "/workspaces/local/assets/asset-1"


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


@pytest.mark.asyncio
async def test_hybrid_retrieval_fuses_semantic_and_keyword_results():
    settings = _make_settings(HYBRID_SEARCH_ENABLED="true", RETRIEVAL_CANDIDATE_K="10")
    embedding_client = AsyncMock()
    embedding_client.create_embedding.return_value = [0.1, 0.2]

    class HybridStore:
        async def search(self, query_vector, limit, workspace_id=None, chunking_profile=None):
            return [
                RetrievedChunk("semantic", "doc-1", "docs/guide.md", "semantic", 0.9),
                RetrievedChunk("shared", "doc-2", "src/config.py", "shared", 0.8),
            ]

        async def search_text(self, query, limit, workspace_id=None, chunking_profile=None):
            return [
                RetrievedChunk("shared", "doc-2", "src/config.py", "shared", 0.2),
                RetrievedChunk("keyword", "doc-3", "src/config.py", "keyword", 0.1),
            ]

    result = await RetrievalService(settings, embedding_client, HybridStore()).retrieve("PG_HOST", top_k=3)

    assert [chunk.chunk_id for chunk in result] == ["shared", "semantic", "keyword"]


@pytest.mark.asyncio
async def test_reranking_uses_wider_candidates_then_trims_results():
    settings = _make_settings(
        HYBRID_SEARCH_ENABLED="false",
        RERANK_ENABLED="true",
        RERANK_CANDIDATE_K="4",
    )
    embedding_client = AsyncMock()
    embedding_client.create_embedding.return_value = [0.1, 0.2]
    vector_store = AsyncMock()
    candidates = [
        RetrievedChunk(f"chunk-{index}", "doc", "guide.md", f"text {index}", 0.9 - index / 10)
        for index in range(4)
    ]
    vector_store.search.return_value = candidates

    class ReverseReranker:
        async def rerank(self, question, chunks):
            assert question == "question"
            return list(reversed(chunks))

    result = await RetrievalService(
        settings, embedding_client, vector_store, reranker=ReverseReranker()
    ).retrieve("question", top_k=2)

    assert vector_store.search.call_args.kwargs["limit"] == 20
    assert [chunk.chunk_id for chunk in result] == ["chunk-3", "chunk-2"]


@pytest.mark.asyncio
async def test_disabled_reranking_preserves_candidate_order():
    settings = _make_settings(HYBRID_SEARCH_ENABLED="false", RERANK_ENABLED="false")
    embedding_client = AsyncMock()
    embedding_client.create_embedding.return_value = [0.1, 0.2]
    vector_store = AsyncMock()
    vector_store.search.return_value = [
        RetrievedChunk("first", "doc", "guide.md", "first", 0.9),
        RetrievedChunk("second", "doc", "guide.md", "second", 0.8),
    ]
    reranker = AsyncMock()

    result = await RetrievalService(settings, embedding_client, vector_store, reranker=reranker).retrieve("question")

    assert [chunk.chunk_id for chunk in result] == ["first", "second"]
    reranker.rerank.assert_not_called()


@pytest.mark.asyncio
async def test_unavailable_reranker_safely_returns_fused_candidate_order():
    settings = _make_settings(HYBRID_SEARCH_ENABLED="false", RERANK_ENABLED="true")
    embedding_client = AsyncMock()
    embedding_client.create_embedding.return_value = [0.1, 0.2]
    vector_store = AsyncMock()
    vector_store.search.return_value = [
        RetrievedChunk("first", "doc", "guide.md", "first", 0.9),
        RetrievedChunk("second", "doc", "guide.md", "second", 0.8),
    ]

    class UnavailableReranker:
        async def rerank(self, question, chunks):
            raise RerankerUnavailable("optional dependency is absent")

    result = await RetrievalService(
        settings, embedding_client, vector_store, reranker=UnavailableReranker()
    ).retrieve("question")

    assert [chunk.chunk_id for chunk in result] == ["first", "second"]


@pytest.mark.asyncio
@pytest.mark.parametrize("empty", [False, True])
async def test_document_chat_never_touches_memory_and_streams_null_session(empty):
    document_id = "a" * 64
    memory = MagicMock()
    retrieval = AsyncMock()
    retrieval.retrieve.return_value = [] if empty else [
        RetrievedChunk("one", document_id, "guide.pdf", "Scoped context", 0.9)
    ]
    chat = AsyncMock()
    chat.create_chat_completion.return_value = {"choices": [{"message": {"content": "Scoped answer"}}]}
    service = ChatService(_make_settings(), retrieval, chat, memory)
    response = await service.answer("Question", document_id=document_id, include_debug=True)
    assert response.session_id is None and response.grounded is not empty
    assert response.debug["rewritten_question"] == "Question"
    events = [e async for e in service.answer_stream("Question", document_id=document_id)]
    assert any('"session_id": null' in e for e in events)
    assert not memory.mock_calls
    assert retrieval.retrieve.call_args.kwargs["document_id"] == document_id
    if empty:
        chat.create_chat_completion.assert_not_called()


@pytest.mark.asyncio
async def test_document_chat_fails_before_generation_for_leaked_context_or_session():
    retrieval, chat, memory = AsyncMock(), AsyncMock(), MagicMock()
    retrieval.retrieve.return_value = [RetrievedChunk("bad", "b" * 64, "other.pdf", "secret", 0.9)]
    service = ChatService(_make_settings(), retrieval, chat, memory)
    with pytest.raises(ValueError, match="out-of-scope"):
        await service.answer("Question", document_id="a" * 64)
    with pytest.raises(ValueError, match="cannot use a session"):
        await service.answer("Question", document_id="a" * 64, session_id="old")
    chat.create_chat_completion.assert_not_called()
    assert not memory.mock_calls


@pytest.mark.asyncio
@pytest.mark.parametrize("leak", [None, "semantic", "lexical"])
async def test_document_filter_reaches_hybrid_candidates_and_rejects_leaks(leak):
    wanted = "a" * 64
    calls = []

    class Store:
        async def search(self, vector, **kwargs):
            calls.append(("semantic", kwargs))
            return [RetrievedChunk("s", "b" * 64 if leak == "semantic" else wanted, "guide.pdf", "s", 0.9)]

        async def search_text(self, query, **kwargs):
            calls.append(("lexical", kwargs))
            return [RetrievedChunk("l", "b" * 64 if leak == "lexical" else wanted, "guide.pdf", "l", 0.8)]

    embedding = AsyncMock()
    embedding.create_embedding.return_value = [0.1]
    reranker = AsyncMock()
    reranker.rerank.side_effect = lambda q, chunks: chunks
    service = RetrievalService(_make_settings(HYBRID_SEARCH_ENABLED="true", RERANK_ENABLED="true"), embedding, Store(), reranker)
    if leak:
        with pytest.raises(ValueError, match="out-of-scope"):
            await service.retrieve("Question", workspace_id="ws", document_id=wanted)
        reranker.rerank.assert_not_called()
    else:
        chunks = await service.retrieve("Question", workspace_id="ws", document_id=wanted)
        assert len(chunks) == 2
    assert all(c[1]["document_id"] == wanted and c[1]["workspace_id"] == "ws" for c in calls)


@pytest.mark.asyncio
async def test_scoped_retrieval_does_not_retry_legacy_adapter_unscoped():
    class OldStore:
        async def search(self, vector, limit, workspace_id=None, chunking_profile=None):
            pytest.fail("Must not fall back to unscoped search")

    with pytest.raises(TypeError):
        await RetrievalService(_make_settings(), AsyncMock(), OldStore()).retrieve("Question", document_id="a" * 64)

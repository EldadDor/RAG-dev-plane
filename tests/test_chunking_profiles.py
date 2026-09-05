from unittest.mock import AsyncMock

import pytest

from app.config import Settings
from app.domain.models import Document, SourceType
from app.services.ingestion_service import IngestionService
from app.services.retrieval_service import RetrievalService


def _settings(**overrides) -> Settings:
    defaults = {
        "CHAT_BASE_URL": "http://localhost:8080/v1",
        "VECTOR_STORE": "qdrant",
        "QDRANT_URL": "http://localhost:6333",
        "CHUNKING_PROFILES": {
            "experiment-small": {
                "provider": "recursive-character",
                "chunk_size": 40,
                "chunk_overlap": 10,
            }
        },
    }
    defaults.update(overrides)
    return Settings(**defaults)


def test_default_profile_inherits_the_legacy_chunking_settings():
    settings = _settings(CHUNK_SIZE=900, CHUNK_OVERLAP=100, CHUNKER_PROVIDER="recursive-character")

    name, profile = settings.chunking_profile()

    assert name == "default"
    assert profile.provider == "recursive-character"
    assert profile.chunk_size == 900
    assert profile.chunk_overlap == 100


@pytest.mark.asyncio
async def test_dry_run_reports_experiment_chunks_without_embedding_or_writes(monkeypatch):
    source = "guide.txt"
    document = Document("guide", source, SourceType.text, "One paragraph with enough text to make multiple chunks. " * 4)
    monkeypatch.setattr("app.services.ingestion_service.load_document", lambda _: document)

    embedding_client = AsyncMock()
    vector_store = AsyncMock()
    service = IngestionService(_settings(), embedding_client, vector_store)

    result = await service.ingest_path(source, chunking_profile="experiment-small", dry_run=True)

    assert result.dry_run is True
    assert result.chunking_profile == "experiment-small"
    assert result.chunks_indexed > 1
    embedding_client.create_embedding.assert_not_awaited()
    vector_store.get_document_hash.assert_not_awaited()
    vector_store.replace_document.assert_not_awaited()
    vector_store.delete_missing_documents.assert_not_awaited()


@pytest.mark.asyncio
async def test_experiment_ingestion_uses_profile_scoped_document_and_chunk_ids(monkeypatch):
    source = "guide.txt"
    document = Document("guide", source, SourceType.text, "Profile isolation test.")
    monkeypatch.setattr("app.services.ingestion_service.load_document", lambda _: document)

    embedding_client = AsyncMock()
    embedding_client.create_embedding.return_value = [0.1, 0.2]
    vector_store = AsyncMock()
    vector_store.get_document_hash.return_value = None
    service = IngestionService(_settings(), embedding_client, vector_store)

    await service.ingest_path(source, chunking_profile="experiment-small")

    stored_document, chunks = vector_store.replace_document.await_args.args
    assert stored_document["chunking_profile"] == "experiment-small"
    assert chunks[0]["chunk_id"] == "guide:experiment-small:0"
    assert chunks[0]["payload"]["chunking_profile"] == "experiment-small"
    vector_store.get_document_hash.assert_awaited_once_with("guide", "local", "experiment-small")


@pytest.mark.asyncio
async def test_retrieval_passes_only_the_selected_profile_to_both_search_lanes():
    settings = _settings(HYBRID_SEARCH_ENABLED=True)
    embedding_client = AsyncMock()
    embedding_client.create_embedding.return_value = [0.1]
    class ProfileStore:
        search = AsyncMock(return_value=[])
        search_text = AsyncMock(return_value=[])

    vector_store = ProfileStore()

    await RetrievalService(settings, embedding_client, vector_store).retrieve(
        "query", workspace_id="local", chunking_profile="experiment-small"
    )

    assert vector_store.search.await_args.kwargs["chunking_profile"] == "experiment-small"
    assert vector_store.search_text.await_args.kwargs["chunking_profile"] == "experiment-small"

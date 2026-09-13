from unittest.mock import AsyncMock

import pytest

from app.services.model_profiles import (
    CachedEmbeddingClient,
    InMemoryEmbeddingCache,
    InMemoryModelProfileStore,
    ModelProfile,
    embedding_cache_key,
)
from app.config import Settings
from app.services.retrieval_service import RetrievalService


def _profile(**overrides) -> ModelProfile:
    values = {
        "profile_name": "bge-m3",
        "provider": "ollama",
        "model": "bge-m3:latest",
        "dimensions": 3,
        "storage_target": "document_chunks_bge_m3",
        "query_prefix": "query: ",
        "document_prefix": "passage: ",
    }
    values.update(overrides)
    return ModelProfile(**values)


@pytest.mark.asyncio
async def test_profile_store_resolves_exact_name():
    profile = _profile()
    store = InMemoryModelProfileStore([profile])

    assert await store.get("bge-m3") == profile
    assert await store.get("missing") is None


def test_cache_key_changes_for_embedding_affecting_fields():
    profile = _profile()

    assert embedding_cache_key(profile, "same text", "query") != embedding_cache_key(
        profile, "same text", "document"
    )
    assert embedding_cache_key(profile, "same text", "query") != embedding_cache_key(
        _profile(model="another-model"), "same text", "query"
    )


@pytest.mark.asyncio
async def test_cached_client_applies_prefix_and_reuses_embedding():
    delegate = AsyncMock()
    delegate.create_embedding.return_value = [0.1, 0.2, 0.3]
    client = CachedEmbeddingClient(delegate, InMemoryEmbeddingCache(), _profile())

    first = await client.create_query_embedding("  soil   moisture ")
    second = await client.create_query_embedding("  soil   moisture ")

    assert first == second
    delegate.create_embedding.assert_awaited_once_with(
        "bge-m3:latest", "query:   soil   moisture "
    )


@pytest.mark.asyncio
async def test_cached_client_rejects_provider_dimension_mismatch():
    delegate = AsyncMock()
    delegate.create_embedding.return_value = [0.1, 0.2]
    client = CachedEmbeddingClient(delegate, InMemoryEmbeddingCache(), _profile())

    with pytest.raises(ValueError, match="requires 3"):
        await client.create_document_embedding("text")


@pytest.mark.asyncio
async def test_retrieval_resolves_profile_model_cache_and_storage():
    profile = _profile(query_prefix="")
    profile_store = InMemoryModelProfileStore([profile])
    cache = InMemoryEmbeddingCache()
    delegate = AsyncMock()
    delegate.create_embedding.return_value = [0.1, 0.2, 0.3]
    selected_store = AsyncMock()
    selected_store.search.return_value = []
    base_store = AsyncMock()
    base_store.for_profile.return_value = selected_store
    settings = Settings(
        CHAT_BASE_URL="http://localhost:8080/v1",
        VECTOR_STORE="qdrant",
        QDRANT_URL="http://localhost:6333",
        EMBEDDING_MODEL="legacy-model",
        MODEL_PROFILE="bge-m3",
        HYBRID_SEARCH_ENABLED=False,
    )
    service = RetrievalService(
        settings, delegate, base_store,
        model_profile_store=profile_store, embedding_cache=cache,
    )

    await service.retrieve("question")
    await service.retrieve("question")

    base_store.for_profile.assert_awaited_with("document_chunks_bge_m3", 3)
    delegate.create_embedding.assert_awaited_once_with("bge-m3:latest", "question")
    selected_store.search.assert_awaited()

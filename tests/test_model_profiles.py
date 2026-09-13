from unittest.mock import AsyncMock

import pytest

from app.services.model_profiles import (
    CachedEmbeddingClient,
    InMemoryEmbeddingCache,
    InMemoryModelProfileStore,
    ModelProfile,
    embedding_cache_key,
)
from app.services.model_profile_warmer import ModelProfileWarmer
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


class _WarmStore:
    def __init__(self, chunks=None):
        self.chunks = chunks or []
        self.upserted = []
        self.profiles = {}

    async def for_profile(self, storage_target, vector_dim):
        return self.profiles[storage_target]

    async def list_warmable_chunks(self, workspace_id):
        assert workspace_id == "workspace-a"
        return self.chunks

    async def upsert(self, chunks):
        self.upserted.extend(chunks)


def _warm_setup():
    target = _profile(status="draft", document_prefix="passage: ")
    source = _profile(profile_name="default", storage_target="document_chunks", document_prefix="")
    source_store = _WarmStore(
        [{"chunk_id": "chunk-1", "payload": {"text": "source text", "workspace_id": "workspace-a"}}]
    )
    target_store = _WarmStore()
    base_store = _WarmStore()
    base_store.profiles = {
        source.storage_target: source_store,
        target.storage_target: target_store,
    }
    return target, source, source_store, target_store, base_store


@pytest.mark.asyncio
async def test_warmer_dry_run_reports_cache_without_provider_or_storage_writes():
    target, source, _, target_store, base_store = _warm_setup()
    profile_store = InMemoryModelProfileStore([target, source])
    cache = InMemoryEmbeddingCache()
    await cache.put(
        embedding_cache_key(target, "passage: source text", "document"),
        target.provider, target.model, target.dimensions, [0.1, 0.2, 0.3],
    )
    delegate = AsyncMock()
    warmer = ModelProfileWarmer(base_store, delegate, profile_store, cache)

    result = await warmer.warm("bge-m3", "default", "workspace-a", dry_run=True)

    assert result.chunks == 1
    assert result.cache_hits == 1
    assert result.provider_calls == 0
    delegate.create_embedding.assert_not_awaited()
    assert target_store.upserted == []
    assert (await profile_store.get("bge-m3")).status == "draft"


@pytest.mark.asyncio
async def test_warmer_marks_target_warming_when_provider_dimensions_are_invalid():
    target, source, _, target_store, base_store = _warm_setup()
    profile_store = InMemoryModelProfileStore([target, source])
    delegate = AsyncMock()
    delegate.create_embedding.return_value = [0.1, 0.2]
    warmer = ModelProfileWarmer(base_store, delegate, profile_store, InMemoryEmbeddingCache())

    with pytest.raises(ValueError, match="requires 3"):
        await warmer.warm("bge-m3", "default", "workspace-a", dry_run=False)

    assert target_store.upserted == []
    assert (await profile_store.get("bge-m3")).status == "warming"


@pytest.mark.asyncio
async def test_cache_contains_many_rejects_mismatched_dimensions():
    cache = InMemoryEmbeddingCache()
    await cache.put("one", "ollama", "model", 3, [0.1, 0.2, 0.3])

    with pytest.raises(ValueError, match="dimension"):
        await cache.contains_many(["one", "missing"], 2)

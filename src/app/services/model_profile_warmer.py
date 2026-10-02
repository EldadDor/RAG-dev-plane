"""Workspace-scoped warming of an existing chunk corpus into a model profile."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from app.clients.embedding_client import EmbeddingClient
from app.services.model_profiles import (
    CachedEmbeddingClient,
    EmbeddingCache,
    ModelProfile,
    ModelProfileStore,
    ModelProfileUnavailable,
    embedding_cache_key,
)


class ProfileVectorStore(Protocol):
    async def for_profile(self, storage_target: str, vector_dim: int) -> "ProfileVectorStore": ...
    async def list_warmable_chunks(self, workspace_id: str) -> list[dict]: ...
    async def upsert(self, chunks: list[dict]) -> None: ...


@dataclass(frozen=True)
class WarmResult:
    profile_name: str
    source_model_profile: str
    workspace_id: str
    chunks: int
    cache_hits: int
    provider_calls: int
    dry_run: bool


class ModelProfileWarmer:
    """Copies text/provenance, never source vectors, into an isolated profile table."""

    def __init__(
        self,
        vector_store: ProfileVectorStore,
        embedding_client: EmbeddingClient,
        profile_store: ModelProfileStore,
        embedding_cache: EmbeddingCache,
        *,
        batch_size: int = 16,
        embedding_provider: str | None = None,
    ) -> None:
        self._vector_store = vector_store
        self._embedding_client = embedding_client
        self._profile_store = profile_store
        self._embedding_cache = embedding_cache
        self._batch_size = batch_size
        self._embedding_provider = embedding_provider

    async def warm(
        self,
        profile_name: str,
        source_model_profile: str,
        workspace_id: str,
        *,
        dry_run: bool,
    ) -> WarmResult:
        if profile_name == source_model_profile:
            raise ValueError("Target and source model profiles must differ")
        if getattr(type(self._vector_store), "supports_document_catalog", False):
            # Lock order is sorted in the store. Holding the source profile
            # lock prevents stale warm data from resurrecting deleted sources.
            async with self._vector_store.publication_session(profile_name, source_model_profile) as conn:
                return await self._warm_published(profile_name, source_model_profile, workspace_id, dry_run, conn)
        # Compatibility lane for adapters without durable document publication.
        target = await self._resolve_ready_or_draft(profile_name)
        if self._embedding_provider and target.provider != self._embedding_provider:
            raise ModelProfileUnavailable("Target profile requires a different embedding provider")
        source = await self._resolve_ready_or_draft(source_model_profile)
        source_store = await self._vector_store.for_profile(source.storage_target, source.dimensions)
        target_store = await self._vector_store.for_profile(target.storage_target, target.dimensions)
        chunks = await source_store.list_warmable_chunks(workspace_id)

        cache_keys: list[str] = []
        for item in chunks:
            effective_text = f"{target.document_prefix}{item['payload']['text']}"
            cache_keys.append(embedding_cache_key(target, effective_text, "document"))
        cached_keys = await self._embedding_cache.contains_many(cache_keys, target.dimensions)
        cache_hits = sum(cache_key in cached_keys for cache_key in cache_keys)
        result = WarmResult(
            profile_name=target.profile_name,
            source_model_profile=source.profile_name,
            workspace_id=workspace_id,
            chunks=len(chunks),
            cache_hits=cache_hits,
            provider_calls=len(set(cache_keys) - cached_keys),
            dry_run=dry_run,
        )
        if dry_run or not chunks:
            return result

        await self._profile_store.set_status(target.profile_name, "warming")
        client = CachedEmbeddingClient(self._embedding_client, self._embedding_cache, target)
        try:
            for index in range(0, len(chunks), self._batch_size):
                batch = chunks[index : index + self._batch_size]
                vectors = [await client.create_document_embedding(item["payload"]["text"]) for item in batch]
                await target_store.upsert(
                    [{**item, "vector": vector} for item, vector in zip(batch, vectors, strict=True)]
                )
        except Exception:
            # Keep "warming" to make a partial operation visible to operators.
            raise
        await self._profile_store.set_status(target.profile_name, "ready")
        return result

    async def _warm_published(self, profile_name, source_model_profile, workspace_id, dry_run, conn):
        profiles = (self._profile_store.with_connection(conn) if hasattr(type(self._profile_store), "with_connection")
                    else self._profile_store)
        cache = (self._embedding_cache.with_connection(conn) if hasattr(type(self._embedding_cache), "with_connection")
                 else self._embedding_cache)
        store = (self._vector_store.bound_to(conn) if hasattr(type(self._vector_store), "bound_to")
                 else self._vector_store)
        target = await self._resolve_ready_or_draft(profile_name, profiles)
        if self._embedding_provider and target.provider != self._embedding_provider:
            raise ModelProfileUnavailable("Target profile requires a different embedding provider")
        source = await self._resolve_ready_or_draft(source_model_profile, profiles)
        if source.status != "ready":
            raise ModelProfileUnavailable("Source profile must be ready")
        source_store = await store.for_profile(source.storage_target, source.dimensions)
        target_store = await store.for_profile(target.storage_target, target.dimensions)
        documents = await source_store.list_warmable_documents(workspace_id, conn)
        chunks = [chunk for document in documents for chunk in document["chunks"]]
        keys = [embedding_cache_key(target, f"{target.document_prefix}{chunk['payload']['text']}", "document")
                for chunk in chunks]
        cached = await cache.contains_many(keys, target.dimensions)
        result = WarmResult(target.profile_name, source.profile_name, workspace_id, len(chunks),
                            sum(key in cached for key in keys), len(set(keys) - cached), dry_run)
        if dry_run:
            return result
        await profiles.set_status(target.profile_name, "warming")
        client = CachedEmbeddingClient(self._embedding_client, cache, target)
        for document in documents:
            prepared = []
            # Embeddings finish before a per-document transaction opens. No
            # partially prepared document is published after provider failure.
            for item in document["chunks"]:
                vector = await client.create_document_embedding(item["payload"]["text"])
                prepared.append({**item, "vector": vector})
            await target_store.replace_document(document, prepared, document["assets"],
                                                connection=conn, preserve_time=True)
        await profiles.set_status(target.profile_name, "ready")
        return result

    async def _resolve_ready_or_draft(self, profile_name: str, store=None) -> ModelProfile:
        profile = await (store or self._profile_store).get(profile_name)
        if profile is None:
            raise ModelProfileUnavailable(f"Unknown model profile: {profile_name}")
        if profile.status not in {"draft", "ready", "warming"}:
            raise ModelProfileUnavailable(
                f"Model profile {profile_name!r} is not available for warming (status={profile.status})"
            )
        return profile

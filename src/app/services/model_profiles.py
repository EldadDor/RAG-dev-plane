from __future__ import annotations

import hashlib
import re
import struct
from dataclasses import dataclass
from typing import Protocol

import asyncpg

from app.clients.embedding_client import EmbeddingClient


_IDENTIFIER = re.compile(r"^[a-z_][a-z0-9_]*$")


@dataclass(frozen=True)
class ModelProfile:
    profile_name: str
    provider: str
    model: str
    dimensions: int
    storage_target: str
    query_prefix: str = ""
    document_prefix: str = ""
    status: str = "ready"


class ModelProfileUnavailable(ValueError):
    pass


class ModelProfileStore(Protocol):
    async def get(self, profile_name: str) -> ModelProfile | None: ...


class EmbeddingCache(Protocol):
    async def get(self, cache_key: str, dimensions: int) -> list[float] | None: ...

    async def put(
        self,
        cache_key: str,
        provider: str,
        model: str,
        dimensions: int,
        embedding: list[float],
    ) -> None: ...


class InMemoryModelProfileStore:
    def __init__(self, profiles: list[ModelProfile]) -> None:
        self._profiles = {profile.profile_name: profile for profile in profiles}

    async def get(self, profile_name: str) -> ModelProfile | None:
        return self._profiles.get(profile_name)


class InMemoryEmbeddingCache:
    def __init__(self) -> None:
        self._values: dict[str, list[float]] = {}

    async def get(self, cache_key: str, dimensions: int) -> list[float] | None:
        value = self._values.get(cache_key)
        if value is None:
            return None
        if len(value) != dimensions:
            raise ValueError("Cached embedding dimension does not match the model profile")
        return list(value)

    async def put(
        self,
        cache_key: str,
        provider: str,
        model: str,
        dimensions: int,
        embedding: list[float],
    ) -> None:
        if len(embedding) != dimensions:
            raise ValueError("Embedding dimension does not match the model profile")
        self._values.setdefault(cache_key, list(embedding))


class PostgresModelProfileStore:
    def __init__(self, pool: asyncpg.Pool, schema: str) -> None:
        if not _IDENTIFIER.fullmatch(schema):
            raise ValueError(f"Invalid PostgreSQL schema: {schema!r}")
        self._pool = pool
        self._schema = schema

    async def get(self, profile_name: str) -> ModelProfile | None:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                f"""SELECT profile_name, provider, model, dimensions, storage_target,
                    query_prefix, document_prefix, status
                    FROM {self._schema}.model_profiles WHERE profile_name=$1""",
                profile_name,
            )
        return ModelProfile(**dict(row)) if row is not None else None


class PostgresEmbeddingCache:
    def __init__(self, pool: asyncpg.Pool, schema: str) -> None:
        if not _IDENTIFIER.fullmatch(schema):
            raise ValueError(f"Invalid PostgreSQL schema: {schema!r}")
        self._pool = pool
        self._schema = schema

    async def get(self, cache_key: str, dimensions: int) -> list[float] | None:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                f"SELECT embedding, dimensions FROM {self._schema}.embedding_cache WHERE cache_key=$1",
                cache_key,
            )
            if row is None:
                return None
            if row["dimensions"] != dimensions:
                raise ValueError("Cached embedding dimension does not match the model profile")
            await conn.execute(
                f"UPDATE {self._schema}.embedding_cache SET hit_count=hit_count+1, last_hit_at=now() WHERE cache_key=$1",
                cache_key,
            )
        payload = bytes(row["embedding"])
        if len(payload) != dimensions * 4:
            raise ValueError("Cached embedding byte length does not match the model profile")
        return list(struct.unpack(f"<{dimensions}f", payload))

    async def put(
        self,
        cache_key: str,
        provider: str,
        model: str,
        dimensions: int,
        embedding: list[float],
    ) -> None:
        if len(embedding) != dimensions:
            raise ValueError("Embedding dimension does not match the model profile")
        payload = struct.pack(f"<{dimensions}f", *embedding)
        async with self._pool.acquire() as conn:
            await conn.execute(
                f"""INSERT INTO {self._schema}.embedding_cache
                    (cache_key, provider, model, dimensions, embedding)
                    VALUES ($1, $2, $3, $4, $5)
                    ON CONFLICT (cache_key) DO NOTHING""",
                cache_key, provider, model, dimensions, payload,
            )


def embedding_cache_key(profile: ModelProfile, text: str, purpose: str) -> str:
    normalized = " ".join(text.split())
    material = (
        f"{profile.provider}\0{profile.model}\0{profile.dimensions}\0"
        f"{purpose}\0{normalized}"
    ).encode("utf-8")
    return hashlib.sha256(material).hexdigest()


class CachedEmbeddingClient:
    def __init__(
        self,
        delegate: EmbeddingClient,
        cache: EmbeddingCache,
        profile: ModelProfile,
    ) -> None:
        self._delegate = delegate
        self._cache = cache
        self.profile = profile

    async def create_query_embedding(self, text: str) -> list[float]:
        return await self._create(text, "query", self.profile.query_prefix)

    async def create_document_embedding(self, text: str) -> list[float]:
        return await self._create(text, "document", self.profile.document_prefix)

    async def _create(self, text: str, purpose: str, prefix: str) -> list[float]:
        effective_text = f"{prefix}{text}"
        cache_key = embedding_cache_key(self.profile, effective_text, purpose)
        cached = await self._cache.get(cache_key, self.profile.dimensions)
        if cached is not None:
            return cached
        embedding = await self._delegate.create_embedding(self.profile.model, effective_text)
        if len(embedding) != self.profile.dimensions:
            raise ValueError(
                f"Embedding model {self.profile.model!r} returned {len(embedding)} dimensions; "
                f"profile {self.profile.profile_name!r} requires {self.profile.dimensions}"
            )
        await self._cache.put(
            cache_key,
            self.profile.provider,
            self.profile.model,
            self.profile.dimensions,
            embedding,
        )
        return embedding

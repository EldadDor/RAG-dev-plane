"""Warm a provisioned embedding profile from an existing profile's chunk table.

The script is intentionally the only writer for non-default profile tables.
It never alters the source table or `rag.source_documents`; profile storage is
an additive copy of the chunk text and provenance metadata.
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import re
import struct
import sys
from pathlib import Path

import asyncpg

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from app.clients.embedding_client import OllamaEmbeddingClient
from app.config import get_settings


_IDENTIFIER = re.compile(r"^[a-z_][a-z0-9_]*$")


def _identifier(value: str, label: str) -> str:
    if not _IDENTIFIER.fullmatch(value):
        raise ValueError(f"Invalid {label}: {value!r}")
    return value


def _cache_key(provider: str, model: str, dimensions: int, text: str) -> str:
    normalized = " ".join(text.split())
    material = f"{provider}\0{model}\0{dimensions}\0{normalized}".encode("utf-8")
    return hashlib.sha256(material).hexdigest()


def _encode_embedding(embedding: list[float]) -> bytes:
    return struct.pack(f"<{len(embedding)}f", *embedding)


def _decode_embedding(payload: bytes, dimensions: int) -> list[float]:
    if len(payload) != dimensions * 4:
        raise ValueError("Cached embedding has an unexpected byte length")
    return list(struct.unpack(f"<{dimensions}f", payload))


def _vector_literal(embedding: list[float]) -> str:
    return f"[{','.join(map(str, embedding))}]"


async def _embedding_for(
    conn: asyncpg.Connection,
    client: OllamaEmbeddingClient,
    *,
    schema: str,
    provider: str,
    model: str,
    dimensions: int,
    document_prefix: str,
    text: str,
    write: bool,
) -> tuple[list[float], bool]:
    prefixed = f"{document_prefix}{text}"
    cache_key = _cache_key(provider, model, dimensions, prefixed)
    row = await conn.fetchrow(
        f"SELECT embedding FROM {schema}.embedding_cache WHERE cache_key=$1", cache_key
    )
    if row is not None:
        if write:
            await conn.execute(
                f"UPDATE {schema}.embedding_cache SET hit_count=hit_count+1, last_hit_at=now() WHERE cache_key=$1",
                cache_key,
            )
        return _decode_embedding(row["embedding"], dimensions), True

    # A dry run reports the cache-miss work without contacting the model.
    if not write:
        return [], False

    embedding = await client.create_embedding(model, prefixed)
    if len(embedding) != dimensions:
        raise ValueError(f"{model} returned {len(embedding)} dimensions; profile requires {dimensions}")
    if write:
        await conn.execute(
            f"""INSERT INTO {schema}.embedding_cache
                (cache_key, provider, model, dimensions, embedding)
                VALUES ($1, $2, $3, $4, $5)
                ON CONFLICT (cache_key) DO NOTHING""",
            cache_key, provider, model, dimensions, _encode_embedding(embedding),
        )
    return embedding, False


async def warm(profile_name: str, source_profile: str, dry_run: bool) -> dict[str, int]:
    settings = get_settings()
    if settings.vector_store != "postgres":
        raise ValueError("Profile warming requires VECTOR_STORE=postgres")
    schema = _identifier(settings.pg_schema, "schema")
    source_table = _identifier(settings.pg_table, "source table")
    ssl = True if settings.pg_sslmode != "disable" else None
    pool = await asyncpg.create_pool(
        host=settings.pg_host or "", port=settings.pg_port, database=settings.pg_database,
        user=settings.pg_user or "", password=settings.pg_password, ssl=ssl, min_size=1, max_size=1,
    )
    try:
        async with pool.acquire() as conn:
            profile = await conn.fetchrow(
                f"""SELECT provider, model, dimensions, document_prefix, storage_target, status
                    FROM {schema}.model_profiles WHERE profile_name=$1""",
                profile_name,
            )
            if profile is None:
                raise ValueError(f"Unknown model profile: {profile_name}")
            if profile["provider"] != "ollama":
                raise ValueError("Only Ollama model profiles are supported by this warmer")
            target_table = _identifier(profile["storage_target"], "profile storage target")
            exists = await conn.fetchval("SELECT to_regclass($1)", f"{schema}.{target_table}")
            if exists is None:
                raise ValueError(f"Profile table {schema}.{target_table} is not provisioned")
            rows = await conn.fetch(
                f"""SELECT id, content, metadata, source, page_number, chunk_index
                    FROM {schema}.{source_table}
                    WHERE COALESCE(metadata->>'chunking_profile', 'default')=$1
                    ORDER BY id""",
                source_profile,
            )
            if not dry_run:
                await conn.execute(
                    f"UPDATE {schema}.model_profiles SET status='warming', updated_at=now() WHERE profile_name=$1",
                    profile_name,
                )
            client = OllamaEmbeddingClient(settings.embedding_base_url, settings.embedding_timeout_seconds)
            hits = misses = 0
            prepared: list[tuple[asyncpg.Record, list[float] | None, str]] = []
            for row in rows:
                text = f"{profile['document_prefix']}{row['content']}"
                cache_key = _cache_key(profile["provider"], profile["model"], profile["dimensions"], text)
                cached = await conn.fetchrow(
                    f"SELECT embedding FROM {schema}.embedding_cache WHERE cache_key=$1", cache_key
                )
                if cached is None:
                    prepared.append((row, None, cache_key))
                    misses += 1
                else:
                    prepared.append((row, _decode_embedding(cached["embedding"], profile["dimensions"]), cache_key))
                    hits += 1
                    if not dry_run:
                        await conn.execute(
                            f"UPDATE {schema}.embedding_cache SET hit_count=hit_count+1, last_hit_at=now() WHERE cache_key=$1",
                            cache_key,
                        )
            if not dry_run:
                for start in range(0, len(prepared), 16):
                    batch = prepared[start:start + 16]
                    misses_in_batch = [item for item in batch if item[1] is None]
                    if misses_in_batch:
                        embeddings = await client.create_embeddings(
                            profile["model"], [f"{profile['document_prefix']}{item[0]['content']}" for item in misses_in_batch]
                        )
                        for item, embedding in zip(misses_in_batch, embeddings):
                            if len(embedding) != profile["dimensions"]:
                                raise ValueError(f"{profile['model']} returned {len(embedding)} dimensions; profile requires {profile['dimensions']}")
                            index = prepared.index(item)
                            prepared[index] = (item[0], embedding, item[2])
                            await conn.execute(
                                f"""INSERT INTO {schema}.embedding_cache
                                    (cache_key, provider, model, dimensions, embedding)
                                    VALUES ($1, $2, $3, $4, $5) ON CONFLICT (cache_key) DO NOTHING""",
                                item[2], profile["provider"], profile["model"], profile["dimensions"], _encode_embedding(embedding),
                            )
                for row, embedding, _ in prepared:
                    assert embedding is not None
                    await conn.execute(
                        f"""INSERT INTO {schema}.{target_table}
                            (id, content, metadata, embedding, source, page_number, chunk_index)
                            VALUES ($1, $2, $3, $4::vector, $5, $6, $7)
                            ON CONFLICT (id) DO UPDATE SET content=EXCLUDED.content, metadata=EXCLUDED.metadata,
                              embedding=EXCLUDED.embedding, source=EXCLUDED.source, page_number=EXCLUDED.page_number,
                              chunk_index=EXCLUDED.chunk_index, created_at=now()""",
                        row["id"], row["content"], row["metadata"], _vector_literal(embedding),
                        row["source"], row["page_number"], row["chunk_index"],
                    )
            if not dry_run:
                await conn.execute(
                    f"UPDATE {schema}.model_profiles SET status='ready', updated_at=now() WHERE profile_name=$1",
                    profile_name,
                )
            return {"chunks": len(rows), "cache_hits": hits, "provider_calls": misses}
    finally:
        await pool.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Warm an additive PostgreSQL embedding model profile")
    parser.add_argument("profile_name")
    parser.add_argument("--source-profile", default="default")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    print(json.dumps(asyncio.run(warm(args.profile_name, args.source_profile, args.dry_run)), sort_keys=True))


if __name__ == "__main__":
    main()

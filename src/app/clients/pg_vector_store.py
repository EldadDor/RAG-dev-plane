"""PostgreSQL + pgvector vector store.

Uses asyncpg for async Postgres access. Vectors are encoded as PostgreSQL
text literals ('[0.1, 0.2, ...]') and cast to the `vector` type in SQL,
so no additional Python pgvector codec registration is required.

This implementation aligns with the RAG_Embabel-AI local profile schema:
  - schema/table : rag.document_chunks
  - id           : UUID PRIMARY KEY (deterministic UUID5 from chunk_id)
  - content      : chunk text
  - metadata     : JSONB with doc_id, source_path, source_type, title, section
  - embedding    : vector(PG_VECTOR_DIM)
  - source       : source path
  - page_number  : page number
  - chunk_index  : chunk index
  - created_at   : TIMESTAMPTZ DEFAULT now()

Score semantics: pgvector `<=>` returns cosine DISTANCE (lower = more similar).
Scores returned here are normalized to cosine SIMILARITY = 1 - distance,
matching the convention used by QdrantVectorStore.
"""

from __future__ import annotations

import json
import uuid
from typing import Any

import asyncpg

from app.domain.models import RetrievedChunk


_CREATE_EXT = "CREATE EXTENSION IF NOT EXISTS vector;"

_CREATE_SCHEMA = "CREATE SCHEMA IF NOT EXISTS {schema};"

_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS {schema}.{table} (
    id          UUID PRIMARY KEY,
    content     TEXT NOT NULL,
    metadata    JSONB NOT NULL DEFAULT '{{}}'::jsonb,
    embedding   vector({dim}) NOT NULL,
    source      VARCHAR(1000),
    page_number INTEGER,
    chunk_index INTEGER,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
"""

_CREATE_INDEX = """
CREATE INDEX IF NOT EXISTS {index_name}
    ON {schema}.{table}
    USING hnsw (embedding vector_cosine_ops);
"""

_UPSERT_SQL = """
INSERT INTO {schema}.{table}
    (id, content, metadata, embedding, source, page_number, chunk_index)
VALUES ($1, $2, $3, $4::vector, $5, $6, $7)
ON CONFLICT (id) DO UPDATE SET
    content     = EXCLUDED.content,
    metadata    = EXCLUDED.metadata,
    embedding   = EXCLUDED.embedding,
    source      = EXCLUDED.source,
    page_number = EXCLUDED.page_number,
    chunk_index = EXCLUDED.chunk_index,
    created_at  = now();
"""

_SEARCH_SQL = """
SELECT id, content, metadata, source, page_number, chunk_index,
       (1.0 - (embedding <=> $1::vector)) AS score
FROM {schema}.{table}
ORDER BY embedding <=> $1::vector
LIMIT $2;
"""


def _vec_str(vector: list[float]) -> str:
    """Encode a float list as a pgvector text literal: '[0.1,0.2,...]'."""
    return f"[{','.join(map(str, vector))}]"


def _chunk_id_to_uuid(chunk_id: str) -> uuid.UUID:
    """Generate a deterministic UUID5 from a chunk_id string."""
    return uuid.uuid5(uuid.NAMESPACE_URL, chunk_id)


def _index_name(schema: str, table: str) -> str:
    """Generate a Postgres-safe HNSW index name from schema and table."""
    return f"idx_{schema}_{table}_embedding_hnsw"


async def _init_connection(conn: asyncpg.Connection) -> None:
    """Register a codec so `jsonb` columns encode/decode as Python dicts.

    Without this, asyncpg treats `jsonb` values as opaque text: passing a
    dict as a query argument fails to encode, and reading a row back yields
    a raw JSON string instead of a dict (breaking `metadata.get(...)`).
    """
    await conn.set_type_codec(
        "jsonb",
        encoder=json.dumps,
        decoder=json.loads,
        schema="pg_catalog",
        format="text",
    )


class PgVectorStore:
    def __init__(self, pool: asyncpg.Pool, schema: str, table: str, vector_dim: int) -> None:
        self._pool = pool
        self._schema = schema
        self._table = table
        self._vector_dim = vector_dim
        self._ensured = False

    # ------------------------------------------------------------------
    # Factory — creates pool + runs one-time DDL at startup
    # ------------------------------------------------------------------

    @classmethod
    async def create(
        cls,
        *,
        host: str,
        port: int,
        database: str,
        user: str,
        password: str | None,
        sslmode: str,
        schema: str,
        table: str,
        vector_dim: int,
        min_size: int = 2,
        max_size: int = 10,
    ) -> "PgVectorStore":
        """Create the connection pool, register the vector extension, and ensure the schema."""
        # ssl=True: require TLS (Azure Postgres enforces it).
        # max_inactive_connection_lifetime=3000s (50 min) forces pool to recycle
        # connections before Entra tokens expire (~60 min).
        ssl: bool | None = True if sslmode != "disable" else None
        pool = await asyncpg.create_pool(
            host=host,
            port=port,
            database=database,
            user=user,
            password=password,
            ssl=ssl,
            min_size=min_size,
            max_size=max_size,
            max_inactive_connection_lifetime=3000.0,
            init=_init_connection,
        )
        store = cls(pool=pool, schema=schema, table=table, vector_dim=vector_dim)
        await store.ensure_collection(vector_dim)
        return store

    async def close(self) -> None:
        await self._pool.close()

    # ------------------------------------------------------------------
    # VectorStore protocol
    # ------------------------------------------------------------------

    async def ensure_collection(self, vector_size: int = 0) -> None:
        """Create the schema, table and HNSW index if they do not exist.

        Idempotent — subsequent calls are no-ops after the first success.
        If `vector_size` is provided and differs from the configured dimension,
        raises ValueError to prevent silent dimension mismatches.
        """
        if self._ensured:
            return
        if vector_size and vector_size != self._vector_dim:
            raise ValueError(
                f"Embedding dimension mismatch: PgVectorStore configured for {self._vector_dim} dims "
                f"but embedding model produced {vector_size} dims. "
                "Update PG_VECTOR_DIM or re-create the table with the correct dimension."
            )
        async with self._pool.acquire() as conn:
            await conn.execute(_CREATE_EXT)
            await conn.execute(_CREATE_SCHEMA.format(schema=self._schema))
            await conn.execute(_CREATE_TABLE.format(schema=self._schema, table=self._table, dim=self._vector_dim))
            await conn.execute(
                _CREATE_INDEX.format(
                    schema=self._schema,
                    table=self._table,
                    index_name=_index_name(self._schema, self._table),
                )
            )
        self._ensured = True

    async def upsert(self, chunks: list[dict]) -> None:
        if not self._ensured:
            await self.ensure_collection()

        sql = _UPSERT_SQL.format(schema=self._schema, table=self._table)
        records: list[tuple[Any, ...]] = []
        for item in chunks:
            payload = item["payload"]
            chunk_id = item["chunk_id"]
            metadata = {
                "doc_id": payload.get("doc_id", ""),
                "source_path": payload.get("source_path", ""),
                "source_type": payload.get("source_type", ""),
                "title": payload.get("title"),
                "section": payload.get("section"),
                "chunk_id": chunk_id,
            }
            records.append(
                (
                    _chunk_id_to_uuid(chunk_id),
                    payload.get("text", ""),
                    metadata,
                    _vec_str(item["vector"]),
                    payload.get("source_path", ""),
                    payload.get("page"),
                    payload.get("chunk_index"),
                )
            )

        async with self._pool.acquire() as conn:
            await conn.executemany(sql, records)

    async def search(self, query_vector: list[float], limit: int = 5) -> list[RetrievedChunk]:
        if not self._ensured:
            await self.ensure_collection()

        sql = _SEARCH_SQL.format(schema=self._schema, table=self._table)
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(sql, _vec_str(query_vector), limit)

        return [_row_to_retrieved_chunk(row) for row in rows]

    async def health_check(self) -> bool:
        try:
            async with self._pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
            return True
        except Exception:
            return False


def _row_to_retrieved_chunk(row: asyncpg.Record) -> RetrievedChunk:
    metadata = row["metadata"] or {}
    if isinstance(metadata, str):
        # Defensive fallback for rows written before the jsonb codec was
        # registered (or by any external process bypassing it).
        try:
            metadata = json.loads(metadata)
        except json.JSONDecodeError:
            metadata = {}
    return RetrievedChunk(
        chunk_id=metadata.get("chunk_id", str(row["id"])),
        doc_id=metadata.get("doc_id", ""),
        source_path=row["source"] or metadata.get("source_path", ""),
        text=row["content"],
        score=float(row["score"]),
        title=metadata.get("title"),
        page=row["page_number"],
        section=metadata.get("section"),
    )

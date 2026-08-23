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
WHERE metadata->>'workspace_id' = $3
ORDER BY embedding <=> $1::vector
LIMIT $2;
"""

_TEXT_SEARCH_SQL = """
SELECT id, content, metadata, source, page_number, chunk_index,
       ts_rank_cd(to_tsvector('simple', content), websearch_to_tsquery('simple', $1)) AS score
FROM {schema}.{table}
WHERE to_tsvector('simple', content) @@ websearch_to_tsquery('simple', $1)
  AND metadata->>'workspace_id' = $3
ORDER BY score DESC, id
LIMIT $2;
"""


def _vec_str(vector: list[float]) -> str:
    """Encode a float list as a pgvector text literal: '[0.1,0.2,...]'."""
    return f"[{','.join(map(str, vector))}]"


def _chunk_id_to_uuid(chunk_id: str) -> uuid.UUID:
    """Generate a deterministic UUID5 from a chunk_id string."""
    return uuid.uuid5(uuid.NAMESPACE_URL, chunk_id)


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

    @property
    def pool(self) -> asyncpg.Pool:
        """Pool shared with first-party persistence components."""
        return self._pool

    # ------------------------------------------------------------------
    # Factory — creates pool + validates externally managed SQL migrations
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
        """Create the connection pool and validate the externally migrated schema."""
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
        try:
            await store.ensure_collection(vector_dim)
        except Exception:
            await pool.close()
            raise
        return store

    async def close(self) -> None:
        await self._pool.close()

    # ------------------------------------------------------------------
    # VectorStore protocol
    # ------------------------------------------------------------------

    async def ensure_collection(self, vector_size: int = 0) -> None:
        """Validate the migrated schema and configured embedding dimension.

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
            required = [
                f"{self._schema}.{self._table}",
                f"{self._schema}.schema_migrations",
                f"{self._schema}.source_documents",
                f"{self._schema}.chat_sessions",
                f"{self._schema}.conversation_turns",
                f"{self._schema}.conversation_summaries",
                f"{self._schema}.workspaces",
                f"{self._schema}.workspace_members",
            ]
            missing = [name for name in required if await conn.fetchval("SELECT to_regclass($1)", name) is None]
            if missing:
                raise RuntimeError(
                    "PostgreSQL migrations are not applied; missing: "
                    f"{', '.join(missing)}. See database/README.md."
                )
            applied_versions = await conn.fetch(
                f"SELECT version FROM {self._schema}.schema_migrations WHERE version = ANY($1::text[])",
                ["001_baseline", "002_workspace_authorization"],
            )
            applied_version_names = {row["version"] for row in applied_versions}
            required_versions = {"001_baseline", "002_workspace_authorization"}
            if applied_version_names != required_versions:
                missing_versions = sorted(required_versions - applied_version_names)
                raise RuntimeError(
                    f"PostgreSQL migrations are not applied: {', '.join(missing_versions)}. "
                    "See database/README.md."
                )
            actual_type = await conn.fetchval(
                """
                SELECT format_type(attribute.atttypid, attribute.atttypmod)
                FROM pg_attribute attribute
                WHERE attribute.attrelid = to_regclass($1)
                  AND attribute.attname = 'embedding'
                  AND NOT attribute.attisdropped
                """,
                f"{self._schema}.{self._table}",
            )
            expected_type = f"vector({self._vector_dim})"
            if actual_type != expected_type:
                raise RuntimeError(
                    f"PostgreSQL embedding column is {actual_type!r}; expected {expected_type!r}. "
                    "Apply the correct migration or update PG_VECTOR_DIM."
                )
        self._ensured = True

    async def upsert(self, chunks: list[dict]) -> None:
        if not self._ensured:
            await self.ensure_collection()
        async with self._pool.acquire() as conn:
            await self._upsert_on_connection(conn, chunks)

    async def _upsert_on_connection(self, conn: asyncpg.Connection, chunks: list[dict]) -> None:
        sql = _UPSERT_SQL.format(schema=self._schema, table=self._table)
        records: list[tuple[Any, ...]] = []
        for item in chunks:
            payload = item["payload"]
            chunk_id = item["chunk_id"]
            # Keep all provenance metadata. This supports repository, revision,
            # workspace and future ACL filters without a schema migration.
            metadata = {key: value for key, value in payload.items() if key != "text"}
            metadata["chunk_id"] = chunk_id
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

        if records:
            await conn.executemany(sql, records)

    async def search(self, query_vector: list[float], limit: int = 5, workspace_id: str | None = None) -> list[RetrievedChunk]:
        if not self._ensured:
            await self.ensure_collection()

        sql = _SEARCH_SQL.format(schema=self._schema, table=self._table)
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(sql, _vec_str(query_vector), limit, workspace_id or "local")

        return [_row_to_retrieved_chunk(row) for row in rows]

    async def search_text(self, query: str, limit: int = 5, workspace_id: str | None = None) -> list[RetrievedChunk]:
        """Return exact-term matches, optimized for symbols, paths and error text."""
        if not self._ensured:
            await self.ensure_collection()

        sql = _TEXT_SEARCH_SQL.format(schema=self._schema, table=self._table)
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(sql, query, limit, workspace_id or "local")
        return [_row_to_retrieved_chunk(row) for row in rows]

    async def get_document_hash(self, doc_id: str, workspace_id: str) -> str | None:
        async with self._pool.acquire() as conn:
            return await conn.fetchval(
                f"SELECT content_hash FROM {self._schema}.source_documents WHERE doc_id = $1 AND workspace_id = $2",
                doc_id, workspace_id,
            )

    async def replace_document(self, document: dict, chunks: list[dict]) -> None:
        """Atomically replace a document's chunks only after embeddings are ready."""
        async with self._pool.acquire() as conn:
            async with conn.transaction():
                await conn.execute(
                    f"""DELETE FROM {self._schema}.{self._table}
                    WHERE metadata->>'doc_id' = $1
                      AND (metadata->>'workspace_id' = $2 OR NOT (metadata ? 'workspace_id'))""",
                    document["doc_id"], document["workspace_id"],
                )
                await conn.execute(
                    f"""INSERT INTO {self._schema}.source_documents
                    (doc_id, workspace_id, root_path, source_path, source_type, content_hash, metadata)
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                    ON CONFLICT (workspace_id, doc_id) DO UPDATE SET
                      root_path=EXCLUDED.root_path, source_path=EXCLUDED.source_path, source_type=EXCLUDED.source_type,
                      content_hash=EXCLUDED.content_hash, metadata=EXCLUDED.metadata, updated_at=now()""",
                    document["doc_id"], document["workspace_id"], document.get("root_path"), document["source_path"],
                    document["source_type"], document["content_hash"], document.get("metadata", {}),
                )
                await self._upsert_on_connection(conn, chunks)

    async def delete_missing_documents(self, root_path: str, workspace_id: str, present_doc_ids: list[str]) -> int:
        async with self._pool.acquire() as conn:
            async with conn.transaction():
                rows = await conn.fetch(
                    f"SELECT doc_id FROM {self._schema}.source_documents WHERE root_path=$1 AND workspace_id=$2 AND NOT (doc_id = ANY($3::text[]))",
                    root_path, workspace_id, present_doc_ids,
                )
                doc_ids = [row["doc_id"] for row in rows]
                if not doc_ids:
                    return 0
                await conn.execute(f"DELETE FROM {self._schema}.{self._table} WHERE metadata->>'doc_id' = ANY($1::text[]) AND metadata->>'workspace_id' = $2", doc_ids, workspace_id)
                await conn.execute(f"DELETE FROM {self._schema}.source_documents WHERE doc_id = ANY($1::text[]) AND workspace_id = $2", doc_ids, workspace_id)
                return len(doc_ids)

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

"""PostgreSQL + pgvector vector store.

Uses asyncpg for async Postgres access. Vectors are encoded as PostgreSQL
text literals ('[0.1, 0.2, ...]') and cast to the `vector` type in SQL,
so no additional Python pgvector codec registration is required.

Score semantics: pgvector `<=>` returns cosine DISTANCE (lower = more similar).
Scores returned here are normalized to cosine SIMILARITY = 1 - distance,
matching the convention used by QdrantVectorStore.
"""

from __future__ import annotations

import asyncpg

from app.domain.models import RetrievedChunk


_CREATE_EXT = "CREATE EXTENSION IF NOT EXISTS vector;"

_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS {table} (
    chunk_id    TEXT PRIMARY KEY,
    doc_id      TEXT NOT NULL,
    source_path TEXT NOT NULL,
    title       TEXT,
    section     TEXT,
    page        INT,
    source_type TEXT,
    chunk_index INT,
    text        TEXT NOT NULL,
    embedding   vector({dim}) NOT NULL
);
"""

_CREATE_INDEX = """
CREATE INDEX IF NOT EXISTS idx_{table}_embedding
    ON {table}
    USING hnsw (embedding vector_cosine_ops);
"""

_UPSERT_SQL = """
INSERT INTO {table}
    (chunk_id, doc_id, source_path, title, section, page,
     source_type, chunk_index, text, embedding)
VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10::vector)
ON CONFLICT (chunk_id) DO UPDATE SET
    doc_id      = EXCLUDED.doc_id,
    source_path = EXCLUDED.source_path,
    title       = EXCLUDED.title,
    section     = EXCLUDED.section,
    page        = EXCLUDED.page,
    source_type = EXCLUDED.source_type,
    chunk_index = EXCLUDED.chunk_index,
    text        = EXCLUDED.text,
    embedding   = EXCLUDED.embedding;
"""

_SEARCH_SQL = """
SELECT chunk_id, doc_id, source_path, text, title, page, section,
       (1.0 - (embedding <=> $1::vector)) AS score
FROM {table}
ORDER BY embedding <=> $1::vector
LIMIT $2;
"""


def _vec_str(vector: list[float]) -> str:
    """Encode a float list as a pgvector text literal: '[0.1,0.2,...]'."""
    return f"[{','.join(map(str, vector))}]"


class PgVectorStore:
    def __init__(self, pool: asyncpg.Pool, table: str, vector_dim: int) -> None:
        self._pool = pool
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
        )
        store = cls(pool=pool, table=table, vector_dim=vector_dim)
        await store.ensure_collection(vector_dim)
        return store

    async def close(self) -> None:
        await self._pool.close()

    # ------------------------------------------------------------------
    # VectorStore protocol
    # ------------------------------------------------------------------

    async def ensure_collection(self, vector_size: int = 0) -> None:
        """Create the table and HNSW index if they do not exist.

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
            await conn.execute(_CREATE_TABLE.format(table=self._table, dim=self._vector_dim))
            await conn.execute(_CREATE_INDEX.format(table=self._table))
        self._ensured = True

    async def upsert(self, chunks: list[dict]) -> None:
        if not self._ensured:
            await self.ensure_collection()

        sql = _UPSERT_SQL.format(table=self._table)
        records = [
            (
                item["chunk_id"],
                item["payload"].get("doc_id", ""),
                item["payload"].get("source_path", ""),
                item["payload"].get("title"),
                item["payload"].get("section"),
                item["payload"].get("page"),
                item["payload"].get("source_type"),
                item["payload"].get("chunk_index"),
                item["payload"].get("text", ""),
                _vec_str(item["vector"]),
            )
            for item in chunks
        ]
        async with self._pool.acquire() as conn:
            await conn.executemany(sql, records)

    async def search(self, query_vector: list[float], limit: int = 5) -> list[RetrievedChunk]:
        if not self._ensured:
            await self.ensure_collection()

        sql = _SEARCH_SQL.format(table=self._table)
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(sql, _vec_str(query_vector), limit)

        return [
            RetrievedChunk(
                chunk_id=row["chunk_id"],
                doc_id=row["doc_id"],
                source_path=row["source_path"],
                text=row["text"],
                score=float(row["score"]),
                title=row["title"],
                page=row["page"],
                section=row["section"],
            )
            for row in rows
        ]

    async def health_check(self) -> bool:
        try:
            async with self._pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
            return True
        except Exception:
            return False

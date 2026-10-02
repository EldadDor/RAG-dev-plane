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
import re
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

import asyncpg

from app.domain.models import RetrievedChunk
from app.services.document_catalog import PinnedConnectionPool, lock_publication, lock_document, profile_lock_key, publish_metadata, bump_revision


_IDENTIFIER = re.compile(r"^[a-z_][a-z0-9_]*$")


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
  AND COALESCE(metadata->>'chunking_profile', 'default') = $4
ORDER BY embedding <=> $1::vector
LIMIT $2;
"""

_TEXT_SEARCH_SQL = """
SELECT id, content, metadata, source, page_number, chunk_index,
       ts_rank_cd(to_tsvector('simple', content), websearch_to_tsquery('simple', $1)) AS score
FROM {schema}.{table}
WHERE to_tsvector('simple', content) @@ websearch_to_tsquery('simple', $1)
  AND metadata->>'workspace_id' = $3
  AND COALESCE(metadata->>'chunking_profile', 'default') = $4
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
    supports_document_catalog = True

    async def scan_clock(self):
        async with self._pool.acquire() as conn:
            return await conn.fetchval("SELECT clock_timestamp()")

    def __init__(self, pool: asyncpg.Pool, schema: str, table: str, vector_dim: int) -> None:
        if not _IDENTIFIER.fullmatch(schema) or not _IDENTIFIER.fullmatch(table):
            raise ValueError("Invalid PostgreSQL schema/table identifier")
        self._pool = pool
        self._schema = schema
        self._table = table
        self._vector_dim = vector_dim
        self._ensured = False
        self._profile_name: str | None = None

    @property
    def pool(self) -> asyncpg.Pool:
        """Pool shared with first-party persistence components."""
        return self._pool

    def bound_to(self, connection):
        store = type(self)(PinnedConnectionPool(connection), self._schema, self._table, self._vector_dim)
        store._ensured, store._profile_name = self._ensured, self._profile_name
        return store

    async def for_profile(self, storage_target: str, vector_dim: int) -> "PgVectorStore":
        """Return a validated view over a provisioned profile table."""
        if not _IDENTIFIER.fullmatch(storage_target):
            raise ValueError(f"Invalid model-profile storage target: {storage_target!r}")
        if storage_target == self._table and vector_dim == self._vector_dim:
            return self
        store = type(self)(self._pool, self._schema, storage_target, vector_dim)
        await store.ensure_collection(vector_dim)
        return store

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
                f"{self._schema}.document_assets",
                f"{self._schema}.chunk_assets",
                f"{self._schema}.model_profiles",
                f"{self._schema}.embedding_cache",
                f"{self._schema}.document_index_metadata",
                f"{self._schema}.document_index_assets",
                f"{self._schema}.document_list_revisions",
                f"{self._schema}.document_catalog_state",
            ]
            missing = [name for name in required if await conn.fetchval("SELECT to_regclass($1)", name) is None]
            if missing:
                raise RuntimeError(
                    "PostgreSQL migrations are not applied; missing: "
                    f"{', '.join(missing)}. See database/README.md."
                )
            applied_versions = await conn.fetch(
                f"SELECT version FROM {self._schema}.schema_migrations WHERE version = ANY($1::text[])",
                ["001_baseline", "002_workspace_authorization", "003_chunking_profiles", "004_document_assets", "005_model_profiles", "006_document_index_metadata", "007_powerpoint_document_type"],
            )
            applied_version_names = {row["version"] for row in applied_versions}
            required_versions = {"001_baseline", "002_workspace_authorization", "003_chunking_profiles", "004_document_assets", "005_model_profiles", "006_document_index_metadata", "007_powerpoint_document_type"}
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
            self._profile_name = await conn.fetchval(
                f"SELECT profile_name FROM {self._schema}.model_profiles WHERE storage_target=$1", self._table)
            if self._profile_name is None:
                raise RuntimeError("Vector table must have a registered model profile")
        self._ensured = True

    async def upsert(self, chunks: list[dict]) -> None:
        raise RuntimeError("PostgreSQL writes require atomic replace_document publication")

    async def list_warmable_chunks(self, workspace_id: str) -> list[dict[str, Any]]:
        """Return one workspace's text and provenance for profile-to-profile warming."""
        if not self._ensured:
            await self.ensure_collection()
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                f"""SELECT id, content, metadata, source, page_number, chunk_index
                    FROM {self._schema}.{self._table}
                    WHERE metadata->>'workspace_id'=$1
                    ORDER BY id""",
                workspace_id,
            )
        result: list[dict[str, Any]] = []
        for row in rows:
            metadata = row["metadata"] or {}
            payload = dict(metadata)
            payload.update(
                text=row["content"],
                source_path=row["source"] or metadata.get("source_path", ""),
                page=row["page_number"],
                chunk_index=row["chunk_index"],
            )
            result.append({"chunk_id": metadata.get("chunk_id", str(row["id"])), "payload": payload})
        return result

    async def list_warmable_documents(self, workspace_id: str, connection) -> list[dict]:
        """Source snapshot under publication_session, including zero-chunk rows."""
        rows = await connection.fetch(
            f"""SELECT * FROM {self._schema}.document_index_metadata
                WHERE workspace_id=$1 AND model_profile=$2 ORDER BY chunking_profile,doc_id""",
            workspace_id, self._profile_name)
        documents = {(r["chunking_profile"], r["doc_id"]): {**dict(r), "chunks": [], "assets": [], "metadata": {}}
                     for r in rows}
        chunks = await connection.fetch(
            f"""SELECT id,content,metadata,source,page_number,chunk_index FROM {self._schema}.{self._table}
                WHERE metadata->>'workspace_id'=$1 ORDER BY id""", workspace_id)
        for row in chunks:
            payload = row["metadata"] or {}
            if isinstance(payload, str):
                payload = json.loads(payload)
            payload = dict(payload)
            doc_id = payload.get("doc_id")
            if not doc_id:
                raise ValueError("Source chunk has no document identity")
            chunking = payload.get("chunking_profile") or "default"
            key = (chunking, doc_id)
            if key not in documents:
                documents[key] = {
                    "doc_id": doc_id, "workspace_id": workspace_id, "chunking_profile": chunking,
                    "source_path": row["source"] or payload.get("source_path") or "Untitled document",
                    "source_type": payload.get("source_type", "unknown"), "title": payload.get("title"),
                    "root_path": payload.get("root_path"), "content_hash": None,
                    "last_ingested_at": None, "chunks": [], "assets": [], "metadata": {},
                }
            document = documents[key]
            document.setdefault("source_type", document.get("document_type", "unknown"))
            payload.update(text=row["content"], source_path=row["source"] or payload.get("source_path", ""),
                           page=row["page_number"], chunk_index=row["chunk_index"])
            document["chunks"].append({"chunk_id": payload.get("chunk_id", str(row["id"])), "payload": payload})
        for document in documents.values():
            # Include assets from a certified publication (even zero chunks),
            # plus historical chunk references not yet backfilled.
            asset_ids = {asset_id for item in document["chunks"]
                         for asset_id in item["payload"].get("related_asset_ids", [])}
            refs = await connection.fetch(
                f"""SELECT asset_id FROM {self._schema}.document_index_assets
                    WHERE workspace_id=$1 AND model_profile=$2 AND chunking_profile=$3 AND doc_id=$4""",
                workspace_id, self._profile_name, document["chunking_profile"], document["doc_id"])
            asset_ids.update(row["asset_id"] for row in refs)
            assets = await connection.fetch(
                f"""SELECT * FROM {self._schema}.document_assets
                    WHERE asset_id=ANY($1::text[]) AND workspace_id=$2 AND chunking_profile=$3 AND doc_id=$4""",
                sorted(asset_ids), workspace_id, document["chunking_profile"], document["doc_id"])
            if len(assets) != len(asset_ids):
                raise ValueError("Source publication has unavailable asset metadata")
            document["assets"] = [{**dict(asset), "related_chunk_ids": [
                item["chunk_id"] for item in document["chunks"]
                if asset["asset_id"] in item["payload"].get("related_asset_ids", [])]} for asset in assets]
            document.setdefault("source_type", document.get("document_type", "unknown"))
        return list(documents.values())

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
                    _chunk_id_to_uuid(f"{payload.get('workspace_id', 'local')}:{chunk_id}"),
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

    async def search(self, query_vector: list[float], limit: int = 5, workspace_id: str | None = None, chunking_profile: str | None = None) -> list[RetrievedChunk]:
        if not self._ensured:
            await self.ensure_collection()

        sql = _SEARCH_SQL.format(schema=self._schema, table=self._table)
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(sql, _vec_str(query_vector), limit, workspace_id or "local", chunking_profile or "default")

        return [_row_to_retrieved_chunk(row) for row in rows]

    async def search_text(self, query: str, limit: int = 5, workspace_id: str | None = None, chunking_profile: str | None = None) -> list[RetrievedChunk]:
        """Return exact-term matches, optimized for symbols, paths and error text."""
        if not self._ensured:
            await self.ensure_collection()

        sql = _TEXT_SEARCH_SQL.format(schema=self._schema, table=self._table)
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(sql, query, limit, workspace_id or "local", chunking_profile or "default")
        return [_row_to_retrieved_chunk(row) for row in rows]

    async def get_document_hash(self, doc_id: str, workspace_id: str, chunking_profile: str = "default") -> str | None:
        if not self._ensured:
            await self.ensure_collection()
        async with self._pool.acquire() as conn:
            return await conn.fetchval(
                f"""SELECT content_hash FROM {self._schema}.document_index_metadata
                    WHERE doc_id=$1 AND workspace_id=$2 AND chunking_profile=$3 AND model_profile=$4""",
                doc_id, workspace_id, chunking_profile, self._profile_name,
            )

    @asynccontextmanager
    async def publication_session(self, *profiles: str):
        """Serialize warming/backfill against all commits in the affected profiles.

        Caller passes this same connection to document publication, avoiding
        self-deadlock while embeddings are prepared outside SQL transactions.
        """
        async with self._pool.acquire() as conn:
            locked = []
            try:
                for profile in sorted(set(profiles)):
                    key = profile_lock_key(self._schema, profile)
                    await conn.execute("SELECT pg_advisory_lock(hashtextextended($1,0))", key)
                    locked.append(key)
                yield conn
            finally:
                for key in reversed(locked):
                    await conn.execute("SELECT pg_advisory_unlock(hashtextextended($1,0))", key)

    async def replace_document(self, document: dict, chunks: list[dict], assets: list[dict] | None = None,
                               *, connection=None, preserve_time: bool = False) -> None:
        """Atomically replace a document's chunks only after embeddings are ready."""
        if not self._ensured:
            await self.ensure_collection()
        if connection is not None:
            await self._replace_on_connection(connection, document, chunks, assets, preserve_time)
            return
        async with self._pool.acquire() as conn:
            await self._replace_on_connection(conn, document, chunks, assets, preserve_time)

    async def _replace_on_connection(self, conn, document, chunks, assets, preserve_time):
        async with conn.transaction():
            await lock_publication(conn, self._schema, self._profile_name)
            await lock_document(conn, self._schema, document["workspace_id"], document["chunking_profile"], document["doc_id"])
            # A pending warm must not race a regular ingestion publication.
            if not preserve_time and await conn.fetchval(
                f"SELECT status FROM {self._schema}.model_profiles WHERE profile_name=$1",
                self._profile_name) != "ready":
                raise ValueError("Target model profile is not ready")
            if not preserve_time and document.get("content_hash") is not None:
                current_hash = await conn.fetchval(
                    f"""SELECT content_hash FROM {self._schema}.document_index_metadata
                        WHERE workspace_id=$1 AND model_profile=$2 AND chunking_profile=$3 AND doc_id=$4""",
                    document["workspace_id"], self._profile_name, document["chunking_profile"], document["doc_id"])
                if current_hash == document["content_hash"]:
                    # Another concurrent ingestion already published this
                    # version while this caller prepared embeddings.
                    return
            await conn.execute(
                f"""DELETE FROM {self._schema}.{self._table}
                WHERE metadata->>'doc_id' = $1
                  AND metadata->>'workspace_id' = $2
                  AND COALESCE(metadata->>'chunking_profile', 'default') = $3""",
                document["doc_id"], document["workspace_id"], document["chunking_profile"],
            )
            conflict = ("ON CONFLICT (workspace_id, chunking_profile, doc_id) DO NOTHING" if preserve_time else
                        """ON CONFLICT (workspace_id, chunking_profile, doc_id) DO UPDATE SET
                        root_path=EXCLUDED.root_path, source_path=EXCLUDED.source_path, source_type=EXCLUDED.source_type,
                        content_hash=EXCLUDED.content_hash, metadata=EXCLUDED.metadata, updated_at=now()""")
            await conn.execute(
                f"""INSERT INTO {self._schema}.source_documents
                (doc_id, workspace_id, chunking_profile, root_path, source_path, source_type, content_hash, metadata)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                {conflict}""",
                document["doc_id"], document["workspace_id"], document["chunking_profile"], document.get("root_path"), document["source_path"],
                document["source_type"], document.get("content_hash") or "", document.get("metadata", {}),
            )
            await self._upsert_on_connection(conn, chunks)
            await publish_metadata(conn, self._schema, self._table, self._profile_name,
                                   document, preserve_time=preserve_time)
            await conn.execute(
                f"""DELETE FROM {self._schema}.document_index_assets
                    WHERE workspace_id=$1 AND chunking_profile=$2 AND doc_id=$3 AND model_profile=$4""",
                document["workspace_id"], document["chunking_profile"], document["doc_id"], self._profile_name)
            for asset in assets or []:
                await conn.execute(
                    f"""INSERT INTO {self._schema}.document_assets
                    (asset_id, workspace_id, chunking_profile, doc_id, storage_key,
                     content_hash, media_type, byte_size, original_name,
                     relationship_id, ordinal, width, height, alt_text, caption,
                     anchor_block_id)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11,
                            $12, $13, $14, $15, $16) ON CONFLICT (asset_id) DO NOTHING""",
                    asset["asset_id"], document["workspace_id"],
                    document["chunking_profile"], document["doc_id"],
                    asset["storage_key"], asset["content_hash"],
                    asset["media_type"], asset["byte_size"],
                    asset.get("original_name"), asset.get("relationship_id"),
                    asset["ordinal"], asset.get("width"), asset.get("height"),
                    asset.get("alt_text"), asset.get("caption"),
                    asset.get("anchor_block_id"),
                )
                await conn.execute(
                    f"""INSERT INTO {self._schema}.document_index_assets
                        (workspace_id,model_profile,chunking_profile,doc_id,asset_id)
                        VALUES ($1,$2,$3,$4,$5) ON CONFLICT DO NOTHING""",
                    document["workspace_id"], self._profile_name, document["chunking_profile"],
                    document["doc_id"], asset["asset_id"])
                for display_order, chunk_id in enumerate(asset.get("related_chunk_ids", [])):
                    await conn.execute(
                        f"""INSERT INTO {self._schema}.chunk_assets
                        (workspace_id, chunking_profile, doc_id, chunk_id,
                         asset_id, display_order)
                        VALUES ($1, $2, $3, $4, $5, $6) ON CONFLICT DO NOTHING""",
                        document["workspace_id"], document["chunking_profile"],
                        document["doc_id"], chunk_id, asset["asset_id"],
                        display_order,
                    )
            await self._prune_shared_document(conn, document["workspace_id"], document["chunking_profile"], document["doc_id"])

    async def _prune_shared_document(self, conn, workspace, chunking, doc_id):
        # Before backfill certifies historical references, never delete shared
        # rows solely because the new projection has not seen another model.
        if not await conn.fetchval(f"SELECT ready FROM {self._schema}.document_catalog_state WHERE singleton=TRUE"):
            return
        await conn.execute(
            f"""DELETE FROM {self._schema}.document_assets assets
                WHERE workspace_id=$1 AND chunking_profile=$2 AND doc_id=$3
                AND NOT EXISTS (SELECT 1 FROM {self._schema}.document_index_assets refs
                                WHERE refs.asset_id=assets.asset_id)""", workspace, chunking, doc_id)
        await conn.execute(
            f"""DELETE FROM {self._schema}.source_documents source
                WHERE workspace_id=$1 AND chunking_profile=$2 AND doc_id=$3
                AND NOT EXISTS (SELECT 1 FROM {self._schema}.document_index_metadata publications
                    WHERE publications.workspace_id=source.workspace_id
                      AND publications.chunking_profile=source.chunking_profile
                      AND publications.doc_id=source.doc_id)""", workspace, chunking, doc_id)

    async def delete_missing_documents(self, root_path: str, workspace_id: str, present_doc_ids: list[str],
                                       chunking_profile: str = "default", *, recursive: bool = True,
                                       scan_started_at=None) -> int:
        if not self._ensured:
            await self.ensure_collection()
        async with self._pool.acquire() as conn:
            async with conn.transaction():
                await lock_publication(conn, self._schema, self._profile_name)
                rows = await conn.fetch(
                    f"""SELECT doc_id,source_path FROM {self._schema}.document_index_metadata
                        WHERE root_path=$1 AND workspace_id=$2 AND chunking_profile=$3 AND model_profile=$5
                        AND NOT (doc_id = ANY($4::text[]))
                        AND ($6::timestamptz IS NULL OR updated_at<=$6)""",
                    root_path, workspace_id, chunking_profile, present_doc_ids, self._profile_name, scan_started_at,
                )
                # Limit cleanup to the actual scan coverage. A top-level scan
                # cannot prove that descendants disappeared.
                root = Path(root_path).resolve()
                doc_ids = [row["doc_id"] for row in rows
                           if Path(row["source_path"]).resolve().is_relative_to(root)
                           and (recursive or Path(row["source_path"]).resolve().parent == root)]
                if not doc_ids:
                    return 0
                for doc_id in sorted(doc_ids):
                    await lock_document(conn, self._schema, workspace_id, chunking_profile, doc_id)
                await conn.execute(f"DELETE FROM {self._schema}.{self._table} WHERE metadata->>'doc_id' = ANY($1::text[]) AND metadata->>'workspace_id' = $2 AND COALESCE(metadata->>'chunking_profile', 'default') = $3", doc_ids, workspace_id, chunking_profile)
                await conn.execute(
                    f"""DELETE FROM {self._schema}.document_index_metadata
                        WHERE doc_id=ANY($1::text[]) AND workspace_id=$2 AND chunking_profile=$3 AND model_profile=$4""",
                    doc_ids, workspace_id, chunking_profile, self._profile_name)
                await bump_revision(conn, self._schema, workspace_id, self._profile_name, chunking_profile)
                for doc_id in doc_ids:
                    await self._prune_shared_document(conn, workspace_id, chunking_profile, doc_id)
                return len(doc_ids)

    async def health_check(self) -> bool:
        try:
            async with self._pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
            return True
        except Exception:
            return False

    async def get_asset_metadata(self, workspace_id: str, asset_id: str) -> dict | None:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                f"""SELECT asset_id, workspace_id, chunking_profile, doc_id,
                storage_key, content_hash, media_type, byte_size, original_name, width, height,
                alt_text, caption
                FROM {self._schema}.document_assets
                WHERE workspace_id=$1 AND asset_id=$2""",
                workspace_id, asset_id,
            )
        return dict(row) if row is not None else None

    async def list_asset_storage_keys(self) -> list[str]:
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                f"SELECT DISTINCT storage_key FROM {self._schema}.document_assets"
            )
        return [row["storage_key"] for row in rows]


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
        related_asset_ids=tuple(metadata.get("related_asset_ids", [])),
        related_assets=tuple(metadata.get("related_assets", [])),
    )

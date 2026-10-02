from contextlib import asynccontextmanager
from datetime import datetime, timezone
from unittest.mock import AsyncMock

import asyncpg
import pytest

from app.clients.pg_vector_store import PgVectorStore
from app.services.document_catalog import PostgresDocumentCatalog, DocumentListError, publish_metadata


class Connection:
    def __init__(self):
        self.calls = []
        self.in_transaction = False
        self.committed = False
        self.rolled_back = False
        self.fetch = AsyncMock(return_value=[])
        self.fetchrow = AsyncMock(return_value=None)
        self.fetchval = AsyncMock(side_effect=self.values)
        self.execute = AsyncMock(side_effect=self.record_write)
        self.executemany = AsyncMock()
        self.now = datetime(2026, 10, 2, tzinfo=timezone.utc)
    @asynccontextmanager
    async def transaction(self, **options):
        self.options = options
        self.in_transaction = True
        try:
            yield
        except BaseException:
            self.rolled_back = True
            raise
        else:
            self.committed = True
        finally:
            self.in_transaction = False
    async def values(self, sql, *args):
        self.calls.append((sql, args))
        if "SELECT ready" in sql:
            return True
        if "SELECT status" in sql:
            return "ready"
        if "SELECT revision" in sql:
            return 7
        if "SELECT count(*)" in sql:
            return 2
        if sql == "SELECT clock_timestamp()":
            return self.now
        if "RETURNING 1" in sql:
            assert self.in_transaction
            return 1
        return None
    async def record_write(self, sql, *args):
        self.calls.append((sql, args))
        assert self.in_transaction


class Pool:
    def __init__(self, conn):
        self.conn = conn
    @asynccontextmanager
    async def acquire(self):
        yield self.conn


@pytest.mark.asyncio
async def test_pg_listing_reads_revision_and_rows_in_one_repeatable_read_transaction():
    conn = Connection()
    revision, rows = await PostgresDocumentCatalog(Pool(conn), "rag").page("ws", "bge-m3", "default", 25, None)
    assert revision == "7" and rows == []
    assert conn.options == {"isolation": "repeatable_read", "readonly": True}
    sql, *args = conn.fetch.await_args.args
    assert args[:3] == ["ws", "bge-m3", "default"]
    assert args[-1] == 26
    assert 'NULLS LAST' in sql and 'COLLATE "C"' in sql


@pytest.mark.asyncio
async def test_changed_revision_never_fetches_page_rows():
    conn = Connection()
    with pytest.raises(DocumentListError) as error:
        await PostgresDocumentCatalog(Pool(conn), "rag").page("ws", "default", "default", 25, {"revision": "6"})
    assert error.value.status == 409
    conn.fetch.assert_not_awaited()


@pytest.mark.asyncio
async def test_database_failure_maps_to_catalog_unavailable():
    conn = Connection()
    conn.fetch.side_effect = asyncpg.PostgresError("secret SQL failure")
    with pytest.raises(DocumentListError) as error:
        await PostgresDocumentCatalog(Pool(conn), "rag").page("ws", "default", "default", 25, None)
    assert error.value.status == 503
    assert "secret" not in str(error.value)


def document():
    return dict(doc_id="doc", workspace_id="ws", chunking_profile="default", source_path="/private/guide.txt",
                source_type="text", title="Guide", content_hash="new-hash", root_path=None)


@pytest.mark.asyncio
async def test_postgres_replace_publishes_count_and_revision_inside_vector_transaction():
    conn = Connection()
    store = PgVectorStore(Pool(conn), "rag", "chunks", 3)
    store._ensured, store._profile_name = True, "bge-m3"
    await store.replace_document(document(), [])
    assert conn.committed and not conn.rolled_back
    writes = [sql for sql, _ in conn.calls]
    assert "pg_advisory_xact_lock" in writes[0]
    publication = next(args for sql, args in conn.calls if "RETURNING 1" in sql)
    assert publication[:4] == ("ws", "bge-m3", "default", "doc")
    assert publication[8] == conn.now
    assert publication[9] == 2  # Derived from persisted rows, not request len.
    assert any("document_list_revisions" in sql for sql in writes)


@pytest.mark.asyncio
async def test_failed_vector_write_rolls_back_before_catalog_publication():
    conn = Connection()
    conn.executemany.side_effect = RuntimeError("failed vector write")
    store = PgVectorStore(Pool(conn), "rag", "chunks", 3)
    store._ensured, store._profile_name = True, "default"
    chunk = {"chunk_id": "doc:0", "vector": [1, 2, 3], "payload": {"workspace_id": "ws", "text": "text"}}
    with pytest.raises(RuntimeError):
        await store.replace_document(document(), [chunk])
    assert conn.rolled_back and not conn.committed
    assert not any("RETURNING 1" in sql for sql, _ in conn.calls)


@pytest.mark.asyncio
async def test_same_version_concurrent_publication_is_unchanged_under_writer_lock():
    conn = Connection()
    original_values = conn.values
    async def values(sql, *args):
        if "SELECT content_hash" in sql:
            return "new-hash"
        return await original_values(sql, *args)
    conn.fetchval.side_effect = values
    store = PgVectorStore(Pool(conn), "rag", "chunks", 3)
    store._ensured, store._profile_name = True, "default"
    await store.replace_document(document(), [])
    assert conn.committed
    assert not any("DELETE" in sql or "RETURNING 1" in sql for sql, _ in conn.calls)


@pytest.mark.asyncio
async def test_private_hash_repair_does_not_invalidate_public_list_revision():
    conn = Connection()
    conn.fetchrow.return_value = {"title": "Guide", "file_name": "guide.txt", "document_type": "text",
                                 "last_ingested_at": conn.now, "indexed_chunk_count": 2}
    async with conn.transaction():
        await publish_metadata(conn, "rag", "chunks", "default", {**document(), "last_ingested_at": conn.now}, preserve_time=True)
    assert not any("document_list_revisions" in sql for sql, _ in conn.calls)


@pytest.mark.asyncio
async def test_pg_chunk_identity_isolated_by_workspace_without_changing_public_chunk_id():
    conn = Connection()
    store = PgVectorStore(Pool(conn), "rag", "chunks", 3)
    for workspace in ["alpha", "beta"]:
        await store._upsert_on_connection(conn, [{"chunk_id": "same:0", "vector": [1, 2, 3],
                                               "payload": {"workspace_id": workspace, "text": "text"}}])
    first = conn.executemany.await_args_list[0].args[1][0]
    second = conn.executemany.await_args_list[1].args[1][0]
    assert first[0] != second[0]
    assert first[2]["chunk_id"] == second[2]["chunk_id"] == "same:0"


@pytest.mark.asyncio
async def test_nonrecursive_pg_cleanup_preserves_descendants(tmp_path):
    conn = Connection()
    conn.fetch.return_value = [{"doc_id": "top", "source_path": str(tmp_path / "top.txt")},
                              {"doc_id": "nested", "source_path": str(tmp_path / "sub" / "nested.txt")}]
    store = PgVectorStore(Pool(conn), "rag", "chunks", 3)
    store._ensured, store._profile_name = True, "default"
    assert await store.delete_missing_documents(str(tmp_path), "ws", [], recursive=False) == 1
    deleted = [args[0] for sql, args in conn.calls if "DELETE FROM rag.chunks" in sql]
    assert deleted == [["top"]]
    assert conn.fetch.await_args.args[1:6] == (str(tmp_path), "ws", "default", [], "default")

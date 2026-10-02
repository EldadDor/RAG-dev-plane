import hashlib
import importlib.util
from pathlib import Path
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest

from app.config import Settings
from app.domain.models import Document, SourceType, DocumentAsset
from app.services.ingestion_service import IngestionService
from app.services.model_profile_warmer import ModelProfileWarmer
from app.services.model_profiles import ModelProfile, InMemoryModelProfileStore, InMemoryEmbeddingCache


def settings():
    return Settings(_env_file=None, CHAT_BASE_URL="http://unused", VECTOR_STORE="qdrant")


@pytest.mark.asyncio
async def test_empty_document_is_replaced_once_then_unchanged(monkeypatch):
    document = Document("doc", "empty.txt", SourceType.text, " ", title="Empty")
    monkeypatch.setattr("app.services.ingestion_service.load_document", lambda _: document)
    store = AsyncMock()
    store.get_document_hash.return_value = None
    provider = AsyncMock()
    service = IngestionService(settings(), provider, store)
    result = await service.ingest_path("empty.txt")
    stored, chunks, _ = store.replace_document.await_args.args
    assert stored["title"] == "Empty" and chunks == []
    store.get_document_hash.return_value = hashlib.sha256(b"").hexdigest()
    store.replace_document.reset_mock()
    result = await service.ingest_path("empty.txt")
    assert result.documents[0].skip_reason == "unchanged"
    store.replace_document.assert_not_awaited()
    provider.create_embedding.assert_not_awaited()


@pytest.mark.asyncio
async def test_nonempty_document_without_valid_chunks_removes_old_rows(monkeypatch):
    monkeypatch.setattr("app.services.ingestion_service.load_document", lambda _: Document("doc", "guide.txt", SourceType.text, "text"))
    store = AsyncMock()
    store.get_document_hash.return_value = None
    service = IngestionService(settings(), AsyncMock(), store)
    class EmptyChunker:
        def chunk(self, _):
            return []
    monkeypatch.setattr(service, "_chunker_for", lambda _: EmptyChunker())
    await service.ingest_path("guide.txt")
    assert store.replace_document.await_args.args[1] == []


@pytest.mark.asyncio
async def test_failed_directory_file_is_protected_and_scan_coverage_forwarded(monkeypatch, tmp_path):
    failed = str(tmp_path / "failed.txt")
    monkeypatch.setattr("app.services.ingestion_service.load_directory", lambda *a, **k: ([], [{"path": failed, "reason": "load failed"}]))
    store = AsyncMock()
    service = IngestionService(settings(), AsyncMock(), store)
    await service.ingest_path(str(tmp_path), recursive=False)
    args, kwargs = store.delete_missing_documents.await_args
    assert hashlib.sha256(failed.encode()).hexdigest() in args[2]
    assert kwargs["recursive"] is False


@pytest.mark.asyncio
async def test_asset_versions_do_not_overwrite_prior_publications():
    service = IngestionService(settings(), AsyncMock(), AsyncMock())
    def doc(content):
        return Document("doc", "guide.docx", SourceType.word, content,
                        assets=[DocumentAsset("anchor", "r1", content=b"new bytes")])
    first, _ = await service._prepare_assets(doc("first"), [], "workspace", "default", persist=False)
    second, _ = await service._prepare_assets(doc("second"), [], "workspace", "default", persist=False)
    assert first[0]["asset_id"] != second[0]["asset_id"]
    assert first[0]["storage_key"] == second[0]["storage_key"]


class PublicationStore:
    supports_document_catalog = True
    def __init__(self, documents=None):
        self.documents = documents or []
        self.published = []
        self.views = {}
        self.locked = False
    @asynccontextmanager
    async def publication_session(self, *profiles):
        self.locked = True
        try:
            yield "connection"
        finally:
            self.locked = False
    async def for_profile(self, target, dimensions):
        return self.views[target]
    async def list_warmable_documents(self, workspace, conn):
        assert conn == "connection"
        return self.documents
    async def replace_document(self, document, chunks, assets, **kwargs):
        assert kwargs == {"connection": "connection", "preserve_time": True}
        self.published.append((document, chunks, assets))


def warm_setup():
    stamp = datetime(2026, 9, 1, tzinfo=timezone.utc)
    source = ModelProfile("source", "ollama", "source-model", 3, "source_table")
    target = ModelProfile("target", "ollama", "target-model", 3, "target_table", status="draft")
    documents = [dict(doc_id="one", last_ingested_at=stamp, assets=[], chunks=[
        {"chunk_id": "one:0", "payload": {"text": "one"}}, {"chunk_id": "one:1", "payload": {"text": "two"}}]),
        dict(doc_id="zero", last_ingested_at=stamp, assets=[], chunks=[])]
    base, source_store, target_store = PublicationStore(), PublicationStore(documents), PublicationStore()
    base.views = {"source_table": source_store, "target_table": target_store}
    profiles = InMemoryModelProfileStore([source, target])
    provider = AsyncMock()
    provider.create_embedding.return_value = [0.1, 0.2, 0.3]
    return base, source_store, target_store, profiles, provider


@pytest.mark.asyncio
async def test_warming_publishes_complete_documents_and_zero_chunks_preserving_time():
    base, source, target, profiles, provider = warm_setup()
    result = await ModelProfileWarmer(base, provider, profiles, InMemoryEmbeddingCache()).warm("target", "source", "ws", dry_run=False)
    assert result.chunks == 2
    assert [len(record[1]) for record in target.published] == [2, 0]
    assert target.published[0][0]["last_ingested_at"] == source.documents[0]["last_ingested_at"]
    assert (await profiles.get("target")).status == "ready"
    assert base.locked is False


@pytest.mark.asyncio
async def test_warm_provider_failure_never_publishes_partial_document_and_can_retry():
    base, _, target, profiles, provider = warm_setup()
    provider.create_embedding.side_effect = [[0.1, 0.2, 0.3], RuntimeError("provider failed")]
    warmer = ModelProfileWarmer(base, provider, profiles, InMemoryEmbeddingCache())
    with pytest.raises(RuntimeError):
        await warmer.warm("target", "source", "ws", dry_run=False)
    assert target.published == []
    assert (await profiles.get("target")).status == "warming"
    assert base.locked is False
    provider.create_embedding.side_effect = None
    await warmer.warm("target", "source", "ws", dry_run=False)
    assert [len(r[1]) for r in target.published] == [2, 0]


@pytest.mark.asyncio
async def test_published_warm_dry_run_has_no_provider_or_status_writes():
    base, _, target, profiles, provider = warm_setup()
    await ModelProfileWarmer(base, provider, profiles, InMemoryEmbeddingCache()).warm("target", "source", "ws", dry_run=True)
    provider.create_embedding.assert_not_awaited()
    assert target.published == []
    assert (await profiles.get("target")).status == "draft"


@pytest.mark.asyncio
async def test_locked_warm_uses_pinned_adapters_instead_of_borrowing_pool_connections():
    base, _, target, profiles, provider = warm_setup()
    cache = InMemoryEmbeddingCache()
    class LockedProfiles:
        def with_connection(self, conn):
            assert conn == "connection"
            return profiles
        async def get(self, name):
            raise AssertionError("Would borrow from an exhausted pool")
    class LockedCache:
        def with_connection(self, conn):
            assert conn == "connection"
            return cache
        async def contains_many(self, *args):
            raise AssertionError("Would borrow from an exhausted pool")
    class BoundStore:
        async def for_profile(self, table, dimensions):
            return base.views[table]
    class LockedStore(PublicationStore):
        def bound_to(self, conn):
            assert conn == "connection"
            return BoundStore()
        async def for_profile(self, *args):
            raise AssertionError("Would borrow from an exhausted pool")
    await ModelProfileWarmer(LockedStore(), provider, LockedProfiles(), LockedCache()).warm("target", "source", "ws", dry_run=False)
    assert len(target.published) == 2


def load_reconciliation():
    spec = importlib.util.spec_from_file_location("reconciliation_test", Path(__file__).parents[1] / "scripts" / "reconcile_document_catalog.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_historical_backfill_does_not_invent_time_or_profile_hash():
    rows = [{"id": "one", "source": "/private/guide.txt", "metadata": {
        "workspace_id": "ws", "doc_id": "doc", "chunk_id": "doc:0", "source_type": "text", "title": "Guide"}}]
    documents, errors = load_reconciliation().analyze_chunks(rows)
    assert errors == []
    assert documents[0]["count"] == 1
    assert documents[0]["last_ingested_at"] is None and documents[0]["content_hash"] is None


def test_backfill_reports_duplicates_and_conflicting_document_metadata():
    one = {"id": "one", "source": "guide.txt", "metadata": {"workspace_id": "ws", "doc_id": "doc", "chunk_id": "same", "title": "Guide"}}
    two = {"id": "two", "source": "other.txt", "metadata": one["metadata"]}
    documents, errors = load_reconciliation().analyze_chunks([one, two])
    assert documents == []
    assert any("duplicate_chunk_identity" in error for error in errors)
    assert any("conflicting_document_metadata" in error for error in errors)


@pytest.mark.asyncio
async def test_reconciliation_default_runs_read_only_and_never_invents_recency(monkeypatch):
    from types import SimpleNamespace
    module = load_reconciliation()
    profile_row = dict(profile_name="default", storage_target="chunks", dimensions=3, status="ready")
    source_row = dict(workspace_id="ws", chunking_profile="default", doc_id="doc", source_path="guide.txt", root_path=None)
    class ReconcileConnection:
        execute = AsyncMock()
        @asynccontextmanager
        async def transaction(self):
            yield
        async def fetch(self, sql, *args):
            if "model_profiles" in sql:
                return [profile_row]
            if "SELECT id,content" in sql:
                return [{"id": "row", "content": "source text", "source": "guide.txt", "metadata": {
                    "doc_id": "doc", "workspace_id": "ws", "chunk_id": "doc:0", "source_type": "text"}}]
            if "SELECT workspace_id" in sql:
                return [source_row]
            return []
        async def fetchrow(self, *args):
            return source_row
        async def fetchval(self, *args):
            return True
    conn = ReconcileConnection()
    class ReconcileStore:
        close = AsyncMock()
        pool = SimpleNamespace()
        @asynccontextmanager
        async def publication_session(self, *args):
            yield conn
        def bound_to(self, connection):
            assert connection is conn
            return self
        async def for_profile(self, *args):
            return self
    store = ReconcileStore()
    @asynccontextmanager
    async def acquire():
        yield conn
    store.pool.acquire = acquire
    monkeypatch.setattr(module, "get_settings", lambda: SimpleNamespace(vector_store="postgres", pg_schema="rag"))
    monkeypatch.setattr("app.main._init_pg_vector_store", AsyncMock(return_value=store))
    report = await module.reconcile()
    conn.execute.assert_not_awaited()
    assert report["documents"] == 1 and report["chunks"] == 1 and report["dry_run"] is True
    assert report["errors"] == [] and report["ready"] is False

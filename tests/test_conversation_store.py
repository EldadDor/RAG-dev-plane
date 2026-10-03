from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.conversation_store import InMemoryConversationStore, PostgresConversationStore


@pytest.mark.asyncio
async def test_list_is_unique_uncapped_scoped_and_deterministic():
    store = InMemoryConversationStore()
    timestamp = datetime(2026, 10, 3, tzinfo=UTC)
    for index in reversed(range(105)):
        session_id = f"session-{index:03}"
        await store.ensure_session(session_id, "alice", "alpha", "Same title")
        await store.ensure_session(session_id, "alice", "alpha", "Repeated ensure")
        store._session_meta[session_id]["updated_at"] = timestamp
    store._session_meta["session-104"]["updated_at"] = timestamp + timedelta(seconds=1)
    store._session_meta["session-103"]["updated_at"] = None
    await store.ensure_session("other-owner", "bob", "alpha", "Same title")
    await store.ensure_session("other-workspace", "alice", "beta", "Same title")
    await store.ensure_session("archived", "alice", "alpha", "Same title")
    await store.archive_session("archived", "alice", "alpha")
    rows = await store.list_sessions("alice", "alpha")
    ids = [row["session_id"] for row in rows]
    assert ids == ["session-104"] + [f"session-{index:03}" for index in range(103)] + ["session-103"]
    assert len(set(ids)) == 105
    rows[0]["title"] = "External mutation"
    assert (await store.get_session("session-104", "alice"))["title"] == "Same title"


@pytest.mark.asyncio
async def test_rename_and_archive_persist_with_scope_guards():
    store = InMemoryConversationStore()
    await store.ensure_session("session", "alice", "alpha", "Original")
    store._session_meta["session"]["updated_at"] = datetime(2000, 1, 1, tzinfo=UTC)
    for owner, workspace in [("bob", "alpha"), ("alice", "beta")]:
        assert not await store.rename_session("session", owner, workspace, "Denied")
        assert not await store.archive_session("session", owner, workspace)
    assert await store.rename_session("session", "alice", "alpha", "x" * 201)
    detail = await store.get_session("session", "alice")
    assert detail["title"] == "x" * 200
    assert detail["updated_at"].year >= 2026
    assert (await store.list_sessions("alice", "alpha"))[0]["title"] == "x" * 200
    assert await store.archive_session("session", "alice", "alpha")
    assert await store.list_sessions("alice", "alpha") == []
    assert await store.get_session("session", "alice") is None
    assert not await store.archive_session("session", "alice", "alpha")
    assert not await store.rename_session("session", "alice", "alpha", "Revive")
    assert not await store.rename_session("missing", "alice", "alpha", "Missing")


@pytest.mark.asyncio
async def test_postgres_list_query_preserves_scope_and_has_total_order():
    connection = AsyncMock()
    connection.fetch.return_value = [{"session_id": "session"}]
    pool = MagicMock()
    pool.acquire.return_value.__aenter__ = AsyncMock(return_value=connection)
    pool.acquire.return_value.__aexit__ = AsyncMock(return_value=None)
    store = PostgresConversationStore(pool, "rag", 10, 90)
    assert await store.list_sessions("alice", "alpha") == [{"session_id": "session"}]
    query, owner, workspace = connection.fetch.await_args.args
    assert (owner, workspace) == ("alice", "alpha")
    assert "owner_id=$1 AND workspace_id=$2 AND NOT archived" in query
    assert 'ORDER BY updated_at DESC NULLS LAST, session_id COLLATE "C" ASC' in query
    assert "LIMIT" not in query

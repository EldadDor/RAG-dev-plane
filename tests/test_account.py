from contextlib import asynccontextmanager
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock

import asyncpg
import pytest
from httpx import ASGITransport, AsyncClient

from app.config import Settings, get_settings
from app.dependencies import get_account_preference_store, get_workspace_store
from app.identity import Principal, get_principal
from app.main import create_app
from app.services.account_preferences import (
    AccountUnavailableError, InMemoryAccountPreferenceStore,
    PostgresAccountPreferenceStore, UnavailableAccountPreferenceStore,
)
from app.services.workspace_store import AuthorizedWorkspace, InMemoryWorkspaceStore


@pytest.fixture
def context():
    app = create_app()
    store = InMemoryAccountPreferenceStore()
    members = InMemoryWorkspaceStore({
        "alice": [AuthorizedWorkspace("alpha", "Alpha", "owner")],
        "bob": [AuthorizedWorkspace("beta", "Beta", "member")],
    })
    app.dependency_overrides[get_principal] = lambda: Principal("alice", "Alice", None)
    app.dependency_overrides[get_workspace_store] = lambda: members
    app.dependency_overrides[get_account_preference_store] = lambda: store
    app.dependency_overrides[get_settings] = lambda: SimpleNamespace(auth_mode="local")
    return SimpleNamespace(app=app, store=store, members=members)


@pytest.fixture
async def client(context):
    async with AsyncClient(transport=ASGITransport(app=context.app), base_url="http://test") as instance:
        yield instance


def assert_private(response):
    assert response.headers["cache-control"] == "private, no-store"
    assert response.headers["vary"] == "Cookie, Authorization"


async def test_profile_is_read_only_trusted_and_membership_is_fresh(context, client):
    response = await client.get("/account/profile", headers={"X-Forwarded-User": "bob"})
    assert response.status_code == 200
    result = response.json()
    assert result["profile"] == {"display_name": "Alice", "email": None}
    assert result["workspaces"] == [{"workspace_id": "alpha", "display_name": "Alpha", "role": "owner"}]
    assert "subject" not in response.text
    assert result["capabilities"] == {
        "profile_editable": False,
        "preferences": {
            "read": True, "update": True, "persistence": "process",
            "editable_fields": ["recent_chat_limit"],
            "recent_chat_limit_options": [10, 20, 50, 100], "recent_chat_limit_default": 10,
        },
        "logout": {"supported": False, "reason": "fixed_local_identity"},
    }
    assert_private(response)
    context.members._memberships["alice"] = []
    assert (await client.get("/account/profile")).json()["workspaces"] == []
    assert (await client.patch("/account/preferences", json={"recent_chat_limit": 20})).status_code == 200


@pytest.mark.parametrize("limit", [10, 20, 50, 100])
async def test_update_reload_and_principal_isolation(context, client, limit):
    initial = await client.get("/account/preferences")
    assert initial.json() == {"preferences": {"recent_chat_limit": 10}, "persistence": "process"}
    assert context.store._limits == {}
    saved = await client.patch("/account/preferences", json={"recent_chat_limit": limit})
    assert saved.status_code == 200
    assert saved.json() == {"preferences": {"recent_chat_limit": limit}, "persistence": "process"}
    assert_private(saved)
    assert (await client.get("/account/preferences")).json() == saved.json()
    context.app.dependency_overrides[get_principal] = lambda: Principal("bob", "Bob", "bob@example.test")
    assert (await client.get("/account/preferences")).json()["preferences"]["recent_chat_limit"] == 10
    assert (await client.get("/account/profile")).json()["profile"]["email"] == "bob@example.test"


@pytest.mark.parametrize("body", [
    {}, None, [], 20, "20", {"recent_chat_limit": None}, {"recent_chat_limit": True},
    {"recent_chat_limit": False}, {"recent_chat_limit": "20"}, {"recent_chat_limit": 20.0},
    {"recent_chat_limit": 0}, {"recent_chat_limit": 21}, {"recent_chat_limit": 101},
    {"recent_chat_limit": 20, "subject": "bob"},
    {"recent_chat_limit": 20, "display_name": "Other"},
    {"recent_chat_limit": 20, "workspace_id": "beta"},
])
async def test_invalid_preferences_never_mutate_store(context, client, body):
    response = await client.patch(
        "/account/preferences", content=json.dumps(body), headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 422
    assert response.json() == {"code": "invalid_request", "message": "The request is invalid."}
    assert context.store._limits == {}
    assert_private(response)


@pytest.mark.parametrize("content", ["", "{broken"])
async def test_empty_or_malformed_json_is_safe(context, client, content):
    response = await client.patch(
        "/account/preferences", content=content, headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 422
    assert context.store._limits == {}
    assert_private(response)


@pytest.mark.parametrize("media", ["text/plain", "application/x-www-form-urlencoded", "application/merge-patch+json"])
async def test_unsupported_media_is_rejected(client, media):
    response = await client.patch(
        "/account/preferences", content='{"recent_chat_limit":20}', headers={"Content-Type": media},
    )
    assert response.status_code == 415
    assert response.json()["code"] == "unsupported_media_type"
    assert_private(response)


async def test_json_charset_is_accepted(client):
    response = await client.patch(
        "/account/preferences", content='{"recent_chat_limit":20}',
        headers={"Content-Type": "application/json; charset=utf-8"},
    )
    assert response.status_code == 200


@pytest.mark.parametrize("path", ["/account/profile", "/account/preferences"])
async def test_query_identity_selectors_are_rejected(client, path):
    response = await client.get(path, params={"subject": "bob"})
    assert response.status_code == 422
    assert_private(response)


@pytest.mark.parametrize("method,path", [
    ("GET", "/account/profile"), ("GET", "/account/preferences"), ("PATCH", "/account/preferences"),
])
async def test_missing_gateway_identity_is_unauthenticated(context, client, method, path):
    context.app.dependency_overrides.pop(get_principal)
    context.app.dependency_overrides[get_settings] = lambda: SimpleNamespace(
        auth_mode="gateway", chat_identity_header="X-Forwarded-User",
        chat_identity_name_header="X-Forwarded-Name", chat_identity_email_header="X-Forwarded-Email",
    )
    response = await client.request(method, path, json={"recent_chat_limit": 20})
    assert response.status_code == 401
    assert response.json()["code"] == "authentication_required"
    assert_private(response)


async def test_unavailable_preferences_are_truthful_and_have_account_errors(context, client):
    context.app.dependency_overrides[get_account_preference_store] = lambda: UnavailableAccountPreferenceStore()
    context.app.dependency_overrides[get_settings] = lambda: SimpleNamespace(auth_mode="gateway")
    profile = await client.get("/account/profile")
    caps = profile.json()["capabilities"]
    assert caps["logout"] == {"supported": False, "reason": "not_configured"}
    assert caps["preferences"]["read"] is caps["preferences"]["update"] is False
    assert caps["preferences"]["persistence"] == "unavailable"
    assert caps["preferences"]["editable_fields"] == []
    for method in ["GET", "PATCH"]:
        response = await client.request(method, "/account/preferences", json={"recent_chat_limit": 20})
        assert response.status_code == 503
        assert response.json()["code"] == "account_preferences_unavailable"
        assert_private(response)


async def test_membership_failure_does_not_fabricate_empty_profile(context, client):
    members = SimpleNamespace(list_for_subject=AsyncMock(side_effect=asyncpg.PostgresError("private database data")))
    context.app.dependency_overrides[get_workspace_store] = lambda: members
    response = await client.get("/account/profile")
    assert response.status_code == 503
    assert response.json()["code"] == "account_profile_unavailable"
    assert "private database data" not in response.text
    assert_private(response)


async def test_unexpected_error_is_private_and_safe(context):
    context.app.dependency_overrides[get_workspace_store] = lambda: SimpleNamespace(
        list_for_subject=AsyncMock(side_effect=RuntimeError("private internals")),
    )
    async with AsyncClient(
        transport=ASGITransport(app=context.app, raise_app_exceptions=False), base_url="http://test",
    ) as instance:
        response = await instance.get("/account/profile")
    assert response.status_code == 500
    assert response.json()["code"] == "internal_error"
    assert "private internals" not in response.text
    assert_private(response)


class Pool:
    def __init__(self, conn):
        self.conn = conn

    @asynccontextmanager
    async def acquire(self):
        yield self.conn


async def test_postgres_store_default_has_no_write_and_subject_is_bound():
    conn = SimpleNamespace(fetchval=AsyncMock(return_value=None))
    store = PostgresAccountPreferenceStore(Pool(conn), "rag")
    assert await store.read("alice' --") == 10
    sql, subject = conn.fetchval.await_args.args
    assert sql.startswith("SELECT") and "WHERE subject=$1" in sql
    assert subject == "alice' --" and subject not in sql


async def test_postgres_update_and_new_store_reload_share_subject_scoped_row():
    rows = {}

    async def fetch(sql, subject, *values):
        if sql.lstrip().startswith("INSERT"):
            assert "ON CONFLICT (subject) DO UPDATE" in sql
            assert "RETURNING recent_chat_limit" in sql
            rows[subject] = values[0]
        return rows.get(subject)

    conn = SimpleNamespace(fetchval=AsyncMock(side_effect=fetch))
    pool = Pool(conn)
    assert await PostgresAccountPreferenceStore(pool, "rag").update("alice", 50) == 50
    reloaded = PostgresAccountPreferenceStore(pool, "rag")
    assert await reloaded.read("alice") == 50
    assert await reloaded.read("bob") == 10


@pytest.mark.parametrize("operation", ["read", "update"])
@pytest.mark.parametrize("error", [asyncpg.PostgresError("private db error"), asyncpg.InterfaceError("closed pool"), OSError("offline"), TimeoutError()])
async def test_postgres_failure_never_falls_back_to_memory(operation, error):
    conn = SimpleNamespace(fetchval=AsyncMock(side_effect=error))
    store = PostgresAccountPreferenceStore(Pool(conn), "rag")
    with pytest.raises(AccountUnavailableError) as caught:
        await (store.read("alice") if operation == "read" else store.update("alice", 20))
    assert caught.value.code == "account_preferences_unavailable"
    assert "private" not in str(caught.value)


@pytest.mark.parametrize("auth_mode,persistence", [("local", "process"), ("gateway", "unavailable")])
async def test_qdrant_lifespan_store_is_shared_and_resets_on_restart(monkeypatch, auth_mode, persistence):
    import app.main as main
    settings = Settings(_env_file=None, VECTOR_STORE="qdrant", AUTH_MODE=auth_mode)
    monkeypatch.setattr(main, "get_settings", lambda: settings)
    monkeypatch.setattr(main, "QdrantVectorStore", lambda **kwargs: SimpleNamespace())
    app = main.create_app()
    async with main.lifespan(app):
        original = app.state.account_preference_store
        assert original.persistence == persistence
        request = SimpleNamespace(app=app)
        assert get_account_preference_store(request) is original
        if persistence == "process":
            await original.update("alice", 100)
            assert await get_account_preference_store(request).read("alice") == 100
    async with main.lifespan(app):
        assert app.state.account_preference_store is not original
        if persistence == "process":
            assert await app.state.account_preference_store.read("alice") == 10


async def test_postgres_lifespan_uses_shared_pool_without_network(monkeypatch):
    import app.main as main
    settings = Settings(_env_file=None, VECTOR_STORE="postgres", PG_HOST="localhost", PG_USER="test")
    monkeypatch.setattr(main, "get_settings", lambda: settings)
    vector_store = SimpleNamespace(pool=object(), close=AsyncMock())
    monkeypatch.setattr(main, "_init_pg_vector_store", AsyncMock(return_value=vector_store))
    app = main.create_app()
    async with main.lifespan(app):
        preference_store = app.state.account_preference_store
        assert isinstance(preference_store, PostgresAccountPreferenceStore)
        assert preference_store._pool is vector_store.pool
    vector_store.close.assert_awaited_once()


async def test_no_lifespan_means_unavailable_instead_of_per_request_memory():
    request = SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace()))
    assert get_account_preference_store(request).persistence == "unavailable"


async def test_local_identity_cannot_be_selected_by_browser_headers(context, client):
    context.app.dependency_overrides.pop(get_principal)
    context.app.dependency_overrides[get_settings] = lambda: SimpleNamespace(
        auth_mode="local", local_subject="alice", local_display_name="Configured Alice", local_email=None,
    )
    headers = {"X-Forwarded-User": "bob", "X-Forwarded-Name": "Bob", "X-Forwarded-Email": "bob@example.test"}
    profile = await client.get("/account/profile", headers=headers)
    assert profile.json()["profile"] == {"display_name": "Configured Alice", "email": None}
    assert (await client.patch("/account/preferences", json={"recent_chat_limit": 50}, headers=headers)).status_code == 200
    assert await context.store.read("alice") == 50
    assert await context.store.read("bob") == 10


@pytest.mark.parametrize("missing", ["table", "ledger", None])
async def test_postgres_startup_requires_account_table_and_migration(missing):
    from app.clients.pg_vector_store import PgVectorStore

    async def fetchval(sql, *args):
        if sql == "SELECT to_regclass($1)":
            return None if missing == "table" and args[0].endswith(".account_preferences") else args[0]
        if "format_type" in sql:
            return "vector(768)"
        if "SELECT profile_name" in sql:
            return "default"
        raise AssertionError(sql)

    async def fetch(sql, versions):
        assert "008_account_preferences" in versions
        return [{"version": version} for version in versions if missing != "ledger" or version != "008_account_preferences"]

    conn = SimpleNamespace(fetchval=AsyncMock(side_effect=fetchval), fetch=AsyncMock(side_effect=fetch))
    store = PgVectorStore(Pool(conn), "rag", "document_chunks", 768)
    if missing:
        with pytest.raises(RuntimeError, match="account_preferences"):
            await store.ensure_collection()
        assert not store._ensured
    else:
        await store.ensure_collection()
        assert store._ensured

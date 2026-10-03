"""Provider-free gateway acceptance; no services are started or called."""

import asyncio
from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock
from urllib.parse import unquote, urlsplit, parse_qs

import asyncpg
from cryptography.fernet import Fernet
from httpx import ASGITransport, AsyncClient
from joserfc import jwt
from joserfc.jwk import RSAKey
import pytest

from app.auth.config import GatewaySettings
from app.auth.main import create_gateway, digest
from app.auth.oidc import EntraProvider
from app.auth.store import MemorySessionStore, PostgresSessionStore, Record, StoreUnavailable
from app.config import Settings, get_settings
from app.dependencies import get_account_preference_store, get_workspace_store
from app.main import create_app
from app.services.account_preferences import InMemoryAccountPreferenceStore
from app.services.workspace_store import AuthorizedWorkspace, InMemoryWorkspaceStore

ORIGIN = "http://localhost:8080"
PROXY_SECRET = "p" * 40
TENANT = "11111111-1111-1111-1111-111111111111"
CLIENT = "22222222-2222-2222-2222-222222222222"
OBJECT = "33333333-3333-3333-3333-333333333333"


def config(**kwargs):
    return GatewaySettings(_env_file=None, AUTH_PROXY_SECRET=PROXY_SECRET, **kwargs)


@pytest.fixture
def context():
    settings = config(AUTH_IDLE_SECONDS=60, AUTH_ABSOLUTE_SECONDS=180)
    now = [datetime(2026, 10, 3, tzinfo=UTC)]
    store = MemorySessionStore()
    app = create_gateway(settings, store=store, clock=lambda: now[0])
    return SimpleNamespace(app=app, now=now, store=store, settings=settings)


@pytest.fixture
async def client(context):
    async with AsyncClient(transport=ASGITransport(app=context.app), base_url=ORIGIN) as c:
        yield c


async def sign_in(client, identity="local-dev"):
    status = await client.get("/auth/session")
    csrf = status.json()["csrf_token"]
    response = await client.post("/auth/dev-login", json={"identity": identity}, headers={"Origin": ORIGIN, "X-CSRF-Token": csrf})
    assert response.status_code == 303, response.text
    status = await client.get("/auth/session")
    assert status.json()["authenticated"]
    return status.json()["csrf_token"]


async def admission(client, method="GET", csrf=None, **headers):
    request_headers = {"X-Auth-Proxy-Secret": PROXY_SECRET, "X-Original-Method": method}
    if csrf:
        request_headers.update({"Origin": ORIGIN, "X-CSRF-Token": csrf})
    request_headers.update(headers)
    return await client.get("/internal/authorize", headers=request_headers)


async def test_local_login_cookie_headers_identity_and_no_token_storage(context, client):
    bootstrap = await client.get("/auth/session")
    assert bootstrap.json()["authenticated"] is False
    assert "httponly" in bootstrap.headers["set-cookie"].lower()
    assert "samesite=lax" in bootstrap.headers["set-cookie"].lower()
    assert "secure" not in bootstrap.headers["set-cookie"].lower()
    choices = await client.get("/auth/login")
    assert [x["identity"] for x in choices.json()["identities"]] == ["local-dev", "local-test-2"]
    assert (await client.get("/auth/session")).json()["authenticated"] is False
    await sign_in(client)
    cookie = client.cookies.get("rag_session_dev")
    assert len(cookie) == 43
    response = await admission(client, **{"X-Forwarded-User": "attacker"})
    assert response.status_code == 204
    assert response.headers["x-forwarded-user"] == "local-dev"
    assert unquote(response.headers["x-forwarded-name"]) == "Local Developer"
    assert response.headers["cache-control"] == "private, no-store"
    assert all(cookie not in row.payload and cookie != row.token_hash for row in context.store._records.values())
    assert all("local-dev" not in row.payload for row in context.store._records.values())


async def test_anonymous_and_wrong_proxy_secret_are_denied(client):
    assert (await admission(client)).status_code == 401
    await sign_in(client)
    assert (await client.get("/internal/authorize", headers={"X-Forwarded-User": "local-dev"})).status_code == 403
    assert (await admission(client, **{"X-Auth-Proxy-Secret": "wrong"})).status_code == 403
    assert (await admission(client, method="TRACE")).status_code == 400


@pytest.mark.parametrize("method", ["POST", "PATCH", "PUT", "DELETE"])
async def test_mutation_admission_requires_exact_origin_and_bound_csrf(client, method):
    csrf = await sign_in(client)
    assert (await admission(client, method)).status_code == 403
    assert (await admission(client, method, csrf, Origin="http://attacker.test")).status_code == 403
    assert (await admission(client, method, "wrong")).status_code == 403
    assert (await admission(client, method, csrf)).status_code == 204


async def test_idle_is_not_refreshed_by_status_and_admission_refreshes_only_idle(context, client):
    await sign_in(client)
    original_absolute = (await client.get("/auth/session")).json()["absolute_expires_at"]
    context.now[0] += timedelta(seconds=40)
    assert (await client.get("/auth/session")).json()["authenticated"]
    assert (await admission(client)).status_code == 204
    status = (await client.get("/auth/session")).json()
    assert status["absolute_expires_at"] == original_absolute
    context.now[0] += timedelta(seconds=59)
    assert (await client.get("/auth/session")).json()["authenticated"]
    context.now[0] += timedelta(seconds=1)
    assert (await admission(client)).status_code == 401
    assert not (await client.get("/auth/session")).json()["authenticated"]


async def test_absolute_expiry_cannot_be_extended(context, client):
    await sign_in(client)
    for _ in range(3):
        context.now[0] += timedelta(seconds=50)
        assert (await admission(client)).status_code == 204
    context.now[0] += timedelta(seconds=30)
    assert (await admission(client)).status_code == 401


async def test_failed_csrf_does_not_renew_idle(context, client):
    await sign_in(client)
    context.now[0] += timedelta(seconds=50)
    assert (await admission(client, "POST", "invalid")).status_code == 403
    context.now[0] += timedelta(seconds=10)
    assert (await admission(client)).status_code == 401


async def test_logout_revokes_copied_cookie_and_retries_with_bootstrap(context, client):
    csrf = await sign_in(client)
    cookie = client.cookies.get("rag_session_dev")
    assert (await client.post("/auth/logout", headers={"Origin": ORIGIN, "X-CSRF-Token": "wrong"})).status_code == 403
    response = await client.post("/auth/logout", headers={"Origin": ORIGIN, "X-CSRF-Token": csrf})
    assert response.status_code == 204
    assert "max-age=0" in response.headers["set-cookie"].lower()
    assert "path=/" in response.headers["set-cookie"].lower()
    async with AsyncClient(transport=ASGITransport(app=context.app), base_url=ORIGIN, cookies={"rag_session_dev": cookie}) as copied:
        assert (await admission(copied)).status_code == 401
    bootstrap = (await client.get("/auth/session")).json()
    assert not bootstrap["authenticated"]
    assert (await client.post("/auth/logout", headers={"Origin": ORIGIN, "X-CSRF-Token": bootstrap["csrf_token"]})).status_code == 204


async def test_switch_rotates_and_revokes_prior_identity(context, client):
    await sign_in(client)
    first = client.cookies.get("rag_session_dev")
    await sign_in(client, "local-test-2")
    assert first != client.cookies.get("rag_session_dev")
    assert (await admission(client)).headers["x-forwarded-user"] == "local-test-2"
    async with AsyncClient(transport=ASGITransport(app=context.app), base_url=ORIGIN, cookies={"rag_session_dev": first}) as old:
        assert (await admission(old)).status_code == 401


@pytest.mark.parametrize("path", ["/auth/login?return_to=https://evil.test", "/auth/login?return_to=//evil.test", "/auth/login?return_to=/&return_to=/", "/auth/session?subject=alice"])
async def test_arbitrary_return_destinations_and_selectors_are_rejected(client, path):
    assert (await client.get(path)).status_code in (400, 422)


async def test_dev_login_has_no_password_or_arbitrary_subject_support(client):
    csrf = (await client.get("/auth/session")).json()["csrf_token"]
    headers = {"Origin": ORIGIN, "X-CSRF-Token": csrf}
    for body in ({"identity": "attacker"}, {"identity": "local-dev", "password": "secret"}, {"identity": "local-dev", "subject": "attacker"}):
        assert (await client.post("/auth/dev-login", json=body, headers=headers)).status_code == 422
    assert (await client.post("/auth/dev-login", content="bad", headers={**headers, "Content-Type": "text/plain"})).status_code == 415
    assert (await client.post("/auth/dev-login", content="x" * 4097, headers={**headers, "Content-Type": "application/json"})).status_code == 413
    assert (await client.post("/auth/dev-login", json={"identity": "local-dev"}, headers={**headers, "Origin": "null"})).status_code == 403


async def test_no_lifespan_is_unavailable_not_per_request_fallback():
    app = create_gateway(config())
    async with AsyncClient(transport=ASGITransport(app=app), base_url=ORIGIN) as c:
        response = await c.get("/auth/session")
        assert response.status_code == 503
        assert response.json()["code"] == "auth_unavailable"


async def test_shared_encryption_key_and_store_allow_cross_replica_revocation():
    key = Fernet.generate_key().decode()
    store = MemorySessionStore()
    first = create_gateway(config(AUTH_STATE_ENCRYPTION_KEY=key), store=store)
    second = create_gateway(config(AUTH_STATE_ENCRYPTION_KEY=key), store=store)
    async with AsyncClient(transport=ASGITransport(app=first), base_url=ORIGIN) as c:
        csrf = await sign_in(c)
        cookie = c.cookies.get("rag_session_dev")
        async with AsyncClient(transport=ASGITransport(app=second), base_url=ORIGIN, cookies={"rag_session_dev": cookie}) as replica:
            assert (await admission(replica)).status_code == 204
            await replica.post("/auth/logout", headers={"Origin": ORIGIN, "X-CSRF-Token": csrf})
        assert (await admission(c)).status_code == 401
        unreadable = create_gateway(config(AUTH_STATE_ENCRYPTION_KEY=Fernet.generate_key().decode()), store=store)
        async with AsyncClient(transport=ASGITransport(app=unreadable), base_url=ORIGIN, cookies={"rag_session_dev": cookie}) as wrong_key:
            # Logout has revoked the record; no stale plaintext/fallback is admitted.
            assert (await admission(wrong_key)).status_code == 401


async def test_unreadable_active_session_fails_closed(context, client):
    await sign_in(client)
    cookie = client.cookies.get("rag_session_dev")
    changed_key_app = create_gateway(config(), store=context.store, clock=lambda: context.now[0])
    async with AsyncClient(transport=ASGITransport(app=changed_key_app), base_url=ORIGIN, cookies={"rag_session_dev": cookie}) as other:
        assert (await other.get("/auth/session")).status_code == 503
        assert (await admission(other)).status_code == 503


async def test_unknown_routes_and_methods_use_safe_envelope(client):
    for response in (await client.get("/auth/unknown"), await client.put("/auth/logout")):
        assert response.status_code in {404, 405}
        assert set(response.json()) == {"code", "message"}
        assert response.headers["cache-control"] == "private, no-store"


@pytest.mark.parametrize("operation", ["get", "revoke", "admit"])
async def test_storage_failures_are_safe_and_logout_never_fabricates_success(context, client, operation):
    csrf = await sign_in(client)
    setattr(context.store, operation, AsyncMock(side_effect=asyncpg.PostgresError("postgres://secret-host password")))
    if operation == "admit":
        response = await admission(client)
    elif operation == "revoke":
        response = await client.post("/auth/logout", headers={"Origin": ORIGIN, "X-CSRF-Token": csrf})
        assert "set-cookie" not in response.headers
    else:
        response = await client.get("/auth/session")
    assert response.status_code == 503
    assert "password" not in response.text and "secret-host" not in response.text
    assert response.headers["cache-control"] == "private, no-store"


@pytest.mark.parametrize("options", [
    {"APP_ENV": "office"}, {"AUTH_PUBLIC_ORIGIN": "http://example.com"},
    {"AUTH_PUBLIC_ORIGIN": "http://localhost:8080/path"}, {"AUTH_PUBLIC_ORIGIN": "http://localhost:8080?x=1"},
    {"AUTH_PUBLIC_ORIGIN": "http://user:password@localhost:8080"}, {"AUTH_PUBLIC_ORIGIN": "https://localhost:8080"},
    {"AUTH_COOKIE_NAME": "__Host-rag_session"}, {"AUTH_COOKIE_NAME": "invalid;cookie"},
    {"AUTH_SESSION_STORE": "postgres"}, {"AUTH_IDLE_SECONDS": 300, "AUTH_ABSOLUTE_SECONDS": 60},
    {"AUTH_RETURN_PATHS": ["/", "//evil.test"]}, {"AUTH_PROVIDER": "entra"},
])
def test_unsafe_configuration_fails_closed(options):
    with pytest.raises(ValueError):
        config(**options)


def test_proxy_secret_cannot_inject_configuration_and_errors_hide_input():
    unsafe = 'secret-value-that-must-not-be-logged"; injected'
    with pytest.raises(ValueError) as captured:
        GatewaySettings(_env_file=None, AUTH_PROXY_SECRET=unsafe)
    assert unsafe not in str(captured.value)


async def test_postgres_put_serializes_capacity_and_binds_ciphertext():
    now = datetime.now(UTC)
    row = Record(digest("opaque"), "session", "encrypted payload", now, now, now + timedelta(seconds=60))
    @asynccontextmanager
    async def transaction():
        yield
    conn = SimpleNamespace(transaction=transaction, execute=AsyncMock(return_value="INSERT 1"), fetchval=AsyncMock(return_value=0))
    store = PostgresSessionStore(FakePool(conn), "rag", max_records=1)
    await store.put(row, now)
    calls = conn.execute.call_args_list
    assert "pg_advisory_xact_lock" in calls[0].args[0]
    assert "DELETE" in calls[1].args[0] and calls[1].args[1] == now
    assert "VALUES ($1,$2,$3,$4,$5,$6,$7)" in calls[2].args[0]
    assert calls[2].args[1:] == (row.token_hash, row.kind, row.payload, now, now, row.expires_at, False)
    conn.fetchval.return_value = 1
    with pytest.raises(StoreUnavailable):
        await store.put(row, now)


async def test_workplace_cookie_creation_and_deletion_match():
    settings = config(APP_ENV="office", AUTH_PROVIDER="entra", AUTH_PUBLIC_ORIGIN="https://rag.example.test",
        AUTH_SESSION_STORE="postgres", AUTH_COOKIE_NAME="__Host-rag_session", AUTH_COOKIE_SECURE=True,
        AUTH_DATABASE_URL="postgresql://role@database/rag?sslmode=require", AUTH_STATE_ENCRYPTION_KEY=Fernet.generate_key().decode(),
        AUTH_ENTRA_TENANT_ID=TENANT, AUTH_ENTRA_CLIENT_ID=CLIENT, AUTH_ENTRA_CLIENT_SECRET="secret")
    app = create_gateway(settings, store=MemorySessionStore(), provider=SimpleNamespace())
    async with AsyncClient(transport=ASGITransport(app=app), base_url="https://rag.example.test") as c:
        status = await c.get("/auth/session")
        cookie = status.headers["set-cookie"].lower()
        assert "secure" in cookie and "httponly" in cookie and "domain=" not in cookie
        assert "path=/" in cookie and "samesite=lax" in cookie
        assert (await c.post("/auth/dev-login")).status_code == 404
        result = await c.post("/auth/logout", headers={"Origin": settings.public_origin, "X-CSRF-Token": status.json()["csrf_token"]})
        assert result.status_code == 204
        deletion = result.headers["set-cookie"].lower()
        assert "secure" in deletion and "httponly" in deletion and "max-age=0" in deletion


class FakeProvider:
    async def begin(self):
        return {"state": "state", "nonce": "nonce", "code_verifier": "verifier", "url": "https://login.microsoftonline.com/authorize"}

    async def finish(self, transaction, code):
        assert transaction["code_verifier"] == "verifier"
        assert code == "code"
        return {"subject": f"entra:{TENANT}:{OBJECT}", "display_name": "שלום\r\nInjected: bad", "email": None}


def entra_config(**kwargs):
    return config(AUTH_PROVIDER="entra", AUTH_ENTRA_TENANT_ID=TENANT,
                  AUTH_ENTRA_CLIENT_ID=CLIENT, AUTH_ENTRA_CLIENT_SECRET="secret", **kwargs)


async def test_oidc_callback_browser_binding_replay_unicode_and_logout_cancels_login():
    store = MemorySessionStore()
    app = create_gateway(entra_config(), store=store, provider=FakeProvider())
    async with AsyncClient(transport=ASGITransport(app=app), base_url=ORIGIN) as c:
        await c.get("/auth/login")
        login_cookie = c.cookies.get("rag_session_dev_login")
        async with AsyncClient(transport=ASGITransport(app=app), base_url=ORIGIN) as other:
            assert (await other.get("/auth/callback?state=state&code=code")).status_code == 400
        assert (await c.get("/auth/callback?state=state&code=code")).status_code == 303
        response = await admission(c)
        assert response.status_code == 204
        assert "\r" not in response.headers["x-forwarded-name"]
        assert unquote(response.headers["x-forwarded-name"]).startswith("שלום")
        c.cookies.set("rag_session_dev_login", login_cookie)
        assert (await c.get("/auth/callback?state=state&code=code")).status_code == 400
        await c.get("/auth/login")
        status = (await c.get("/auth/session")).json()
        await c.post("/auth/logout", headers={"Origin": ORIGIN, "X-CSRF-Token": status["csrf_token"]})
        assert (await c.get("/auth/callback?state=state&code=code")).status_code == 400


@pytest.mark.parametrize("query", ["state=wrong&code=code", "state=state&error=access_denied", "state=state&code=code&code=evil"])
async def test_oidc_state_denial_and_duplicate_params(query):
    app = create_gateway(entra_config(), store=MemorySessionStore(), provider=FakeProvider())
    async with AsyncClient(transport=ASGITransport(app=app), base_url=ORIGIN) as c:
        await c.get("/auth/login")
        assert (await c.get("/auth/callback?" + query)).status_code == 400


@pytest.fixture
def signing_key():
    return RSAKey.generate_key(parameters={"kid": "test-key"})


@pytest.mark.parametrize("change", [None, "iss", "aud", "exp", "nonce", "tid", "oid", "signature", "embedded_key", "none", "missing_nonce"])
async def test_real_authlib_signature_and_identity_claim_validation(monkeypatch, signing_key, change):
    provider = EntraProvider(entra_config())
    now = int(datetime.now(UTC).timestamp())
    claims = {"iss": provider.settings.issuer, "aud": CLIENT, "sub": "sub", "iat": now,
              "exp": now + 600, "nonce": "nonce", "tid": TENANT, "oid": OBJECT, "name": "Test"}
    if change == "exp":
        claims["exp"] = now - 1
    elif change in {"iss", "aud", "nonce", "tid", "oid"}:
        claims[change] = "wrong"
    if change == "missing_nonce":
        del claims["nonce"]
        claims["nonce_supported"] = False
    key = RSAKey.generate_key(parameters={"kid": "test-key"}) if change in {"signature", "embedded_key"} else signing_key
    header = {"alg": "RS256", "kid": "test-key"}
    if change == "embedded_key":
        header["jwk"] = key.as_dict(private=False)
    token = jwt.encode(header, claims, key)
    if change == "none":
        import base64
        import json
        encode = lambda value: base64.urlsafe_b64encode(json.dumps(value).encode()).rstrip(b"=").decode()
        token = encode({"alg": "none"}) + "." + encode(claims) + "."
    metadata = {"issuer": provider.settings.issuer, "authorization_endpoint": "https://login.microsoftonline.com/authorize",
                "token_endpoint": "https://login.microsoftonline.com/token", "jwks_uri": "https://login.microsoftonline.com/keys"}
    monkeypatch.setattr(provider.client, "load_server_metadata", AsyncMock(return_value=metadata))
    monkeypatch.setattr(provider.client, "fetch_access_token", AsyncMock(return_value={"id_token": token, "access_token": "discarded"}))
    monkeypatch.setattr(provider.client, "fetch_jwk_set", AsyncMock(return_value={"keys": [signing_key.as_dict(private=False)]}))
    transaction = {"nonce": "nonce", "code_verifier": "verifier"}
    if change:
        with pytest.raises(Exception):
            await provider.finish(transaction, "code")
    else:
        identity = await provider.finish(transaction, "code")
        assert identity["subject"] == f"entra:{TENANT}:{OBJECT}"
        assert "access_token" not in identity
        assert provider.client.fetch_access_token.call_args.kwargs["code_verifier"] == "verifier"


async def test_real_authlib_pkce_and_nonce_creation_without_network(monkeypatch):
    provider = EntraProvider(entra_config())
    metadata = {"issuer": provider.settings.issuer, "authorization_endpoint": "https://login.microsoftonline.com/authorize",
                "token_endpoint": "https://login.microsoftonline.com/token", "jwks_uri": "https://login.microsoftonline.com/keys"}
    monkeypatch.setattr(provider.client, "load_server_metadata", AsyncMock(return_value=metadata))
    transaction = await provider.begin()
    query = parse_qs(urlsplit(transaction["url"]).query)
    assert query["code_challenge_method"] == ["S256"]
    assert query["nonce"] == [transaction["nonce"]]
    assert query["prompt"] == ["select_account"]
    assert query["redirect_uri"] == [ORIGIN + "/auth/callback"]
    assert "code_verifier" not in query


async def test_atomic_memory_consume_revocation_capacity_and_cleanup():
    now = datetime.now(UTC)
    store = MemorySessionStore(max_records=1)
    row = Record(digest("cookie"), "login", "encrypted", now, now, now + timedelta(seconds=5))
    await store.put(row, now)
    with pytest.raises(StoreUnavailable):
        await store.put(Record(digest("other"), "login", "encrypted", now, now, row.expires_at), now)
    results = await asyncio.gather(*(store.consume(row.token_hash, "login", now) for _ in range(5)))
    assert sum(x is not None for x in results) == 1
    await store.put(row, now)
    assert await store.cleanup(row.expires_at) == 1


class FakePool:
    def __init__(self, conn):
        self.conn = conn

    @asynccontextmanager
    async def acquire(self):
        yield self.conn


async def test_postgres_parameter_binding_atomic_admission_and_shared_revocation():
    now = datetime.now(UTC)
    record = Record(digest("session"), "session", "ciphertext", now, now, now + timedelta(seconds=180))
    conn = SimpleNamespace(fetchrow=AsyncMock(return_value=record.__dict__), execute=AsyncMock(return_value="UPDATE 1"))
    store = PostgresSessionStore(FakePool(conn), "rag")
    assert await store.admit(record.token_hash, now, 60) == record
    sql, *args = conn.fetchrow.call_args.args
    assert "UPDATE" in sql and "NOT revoked" in sql and "last_seen>" in sql and "expires_at>" in sql
    assert args == [record.token_hash, now, 60]
    await store.consume(record.token_hash, "login", now)
    sql, *args = conn.fetchrow.call_args.args
    assert "DELETE" in sql and "RETURNING" in sql
    assert args == [record.token_hash, "login", now]
    other_worker = PostgresSessionStore(store.pool, "rag")
    await other_worker.revoke(record.token_hash)
    assert conn.execute.call_args.args[1] == record.token_hash
    conn.fetchrow.return_value = None
    assert await store.admit(record.token_hash, now, 60) is None
    with pytest.raises(ValueError):
        PostgresSessionStore(store.pool, 'rag;DROP TABLE')


@pytest.mark.parametrize("missing", ["table", "migration"])
async def test_postgres_gateway_startup_requires_own_migration(missing):
    conn = SimpleNamespace(fetchval=AsyncMock(side_effect=[False] if missing == "table" else [True, False]))
    with pytest.raises(StoreUnavailable):
        await PostgresSessionStore(FakePool(conn), "rag").validate()


async def test_gateway_identity_isolation_membership_and_profile_capability(monkeypatch, context, client):
    settings = Settings(_env_file=None, AUTH_MODE="gateway", AUTH_SESSION_GATEWAY_ENABLED=True,
                        VECTOR_STORE="qdrant", CHAT_BASE_URL="http://unused")
    monkeypatch.setattr("app.main.get_settings", lambda: settings)
    api = create_app()
    api.dependency_overrides[get_settings] = lambda: settings
    api.dependency_overrides[get_workspace_store] = lambda: InMemoryWorkspaceStore({
        "local-dev": [AuthorizedWorkspace("local", "Local", "owner")],
    })
    api.dependency_overrides[get_account_preference_store] = lambda: InMemoryAccountPreferenceStore()
    async with AsyncClient(transport=ASGITransport(app=api), base_url="http://internal") as backend:
        await sign_in(client)
        auth = await admission(client)
        headers = {key: value for key, value in auth.headers.items() if key.startswith("x-forwarded-")}
        profile = (await backend.get("/account/profile", headers=headers)).json()
        assert profile["capabilities"]["logout"] == {"supported": True, "owner": "gateway", "method": "POST", "url": "/auth/logout", "scope": "application"}
        assert len(profile["workspaces"]) == 1
        await sign_in(client, "local-test-2")
        auth = await admission(client)
        headers = {key: value for key, value in auth.headers.items() if key.startswith("x-forwarded-")}
        assert (await backend.get("/account/profile", headers=headers)).json()["workspaces"] == []
        assert (await backend.get("/account/profile")).status_code == 401


def test_proxy_example_has_private_auth_and_captures_original_method():
    text = Path("deploy/auth/nginx.local.conf.template").read_text()
    assert "internal;" in text and 'X-Auth-Proxy-Secret "${AUTH_PROXY_SECRET}"' in text
    assert "set $auth_original_method $request_method;" in text
    assert "X-Original-Method $auth_original_method;" in text
    for field in ("User", "Name", "Email"):
        assert f"proxy_set_header X-Forwarded-{field} $auth_" in text
    assert "proxy_buffering off;" in text and "proxy_cache off;" in text

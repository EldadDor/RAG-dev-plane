from datetime import datetime, timezone
from unittest.mock import AsyncMock
import time

import pytest
from httpx import ASGITransport, AsyncClient

from app.config import Settings
from app.dependencies import get_document_catalog_service, get_workspace_store, get_embedding_client, get_chat_client
from app.identity import Principal, get_principal
from app.main import app
from app.services.document_catalog import DocumentCatalogService, DocumentCursor, DocumentListError, safe_display_metadata
from app.services.model_profiles import ModelProfile, InMemoryModelProfileStore
from app.services.workspace_store import AuthorizedWorkspace, InMemoryWorkspaceStore


def settings(**values):
    return Settings(_env_file=None, CHAT_BASE_URL="http://unused", VECTOR_STORE="qdrant",
                    DOCUMENT_LIST_ENABLED=True, **values)


def profile(name="default", **values):
    return ModelProfile(profile_name=name, provider="ollama", model="test", dimensions=3,
                        storage_target="chunks_" + name.replace("-", "_"), **values)


class Catalog:
    """Independent fixture corpus; rejects inconsistent traversal revisions."""
    def __init__(self):
        stamp = datetime(2026, 10, 2, 8, tzinfo=timezone.utc)
        self.rows = [dict(doc_id=key, title="מסמך " + key, file_name=key + ".docx", document_type="word",
                          last_ingested_at=stamp if key < "c" else None, indexed_chunk_count=count)
                     for key, count in [("a", 0), ("b", 42), ("c", 1000), ("d", 2)]]
        self.revision = "3"
        self.requests = []

    async def page(self, workspace, model, chunking, limit, token):
        self.requests.append((workspace, model, chunking))
        if token and token["revision"] != self.revision:
            raise DocumentListError(409)
        rows = self.rows if workspace == "alpha" and model == "default" and chunking == "default" else []
        start = next((i+1 for i, row in enumerate(rows) if token and row["doc_id"] == token["last_id"]), 0)
        return self.revision, rows[start:start + limit + 1]


@pytest.fixture
def api():
    app.dependency_overrides.clear()
    catalog = Catalog()
    service = DocumentCatalogService(settings(), catalog, InMemoryModelProfileStore([profile(), profile("other")]), DocumentCursor("x" * 32))
    app.dependency_overrides[get_document_catalog_service] = lambda: service
    app.dependency_overrides[get_principal] = lambda: Principal("alice", "Alice")
    memberships = InMemoryWorkspaceStore({"alice": [AuthorizedWorkspace("alpha", "Alpha", "owner")],
                                         "bob": [AuthorizedWorkspace("alpha", "Alpha", "member")]})
    app.dependency_overrides[get_workspace_store] = lambda: memberships
    # A GET accidentally constructing either provider fails the test.
    def forbidden_provider():
        raise AssertionError("Document discovery must never construct providers")
    app.dependency_overrides[get_embedding_client] = forbidden_provider
    app.dependency_overrides[get_chat_client] = forbidden_provider
    yield catalog, service, memberships
    app.dependency_overrides.clear()


async def get(path="/workspaces/alpha/documents", **params):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        return await client.get(path, params=params)


@pytest.mark.asyncio
async def test_documents_contract_and_full_continuation(api):
    first = await get(limit=2)
    assert first.status_code == 200
    body = first.json()
    assert body["scope"] == {"model_profile": "default", "chunking_profile": "default"}
    assert [r["doc_id"] for r in body["items"]] == ["a", "b"]
    assert body["items"][0]["indexed_chunk_count"] == 0
    assert body["items"][0]["last_ingested_at"].endswith("Z")
    assert set(body["items"][0]) == {"doc_id", "title", "file_name", "document_type", "last_ingested_at", "indexed_chunk_count"}
    second = await get(limit=2, cursor=body["page"]["next_cursor"])
    assert [r["doc_id"] for r in second.json()["items"]] == ["c", "d"]
    assert second.json()["items"][0]["last_ingested_at"] is None
    assert second.json()["page"]["next_cursor"] is None
    assert second.json()["page"]["has_more"] is False
    assert first.headers["cache-control"] == "private, no-store"


@pytest.mark.asyncio
async def test_null_time_continuation_and_member_access(api):
    app.dependency_overrides[get_principal] = lambda: Principal("bob", "Bob")
    body = (await get(limit=3)).json()
    token = api[1].cursors.decode(body["page"]["next_cursor"])
    assert token["last_time"] is None
    assert [r["doc_id"] for r in (await get(limit=3, cursor=body["page"]["next_cursor"])).json()["items"]] == ["d"]


@pytest.mark.asyncio
async def test_revision_change_restarts_instead_of_appending(api):
    body = (await get(limit=1)).json()
    api[0].revision = "4"
    response = await get(limit=1, cursor=body["page"]["next_cursor"])
    assert response.status_code == 409
    assert response.json()["code"] == "document_list_changed"
    assert (await get(limit=1)).status_code == 200


@pytest.mark.asyncio
async def test_revoked_access_is_checked_before_cursor_use(api):
    body = (await get(limit=1)).json()
    api[2]._memberships["alice"] = []
    response = await get(limit=1, cursor=body["page"]["next_cursor"])
    assert response.status_code == 403
    assert response.json()["code"] == "workspace_access_denied"
    assert response.headers["cache-control"] == "private, no-store"
    assert len(api[0].requests) == 1


@pytest.mark.asyncio
@pytest.mark.parametrize("params", [{"limit": 0}, {"limit": 101}, {"limit": "no"}, {"cursor": ""},
                                     {"cursor": "bad"}, {"model_profile": "../table"}, {"chunking_profile": ""}])
async def test_invalid_query_is_safe(api, params):
    response = await get(**params)
    assert response.status_code == 422
    assert response.json() == {"code": "invalid_request", "message": "The request is invalid."}
    assert response.headers["cache-control"] == "private, no-store"


@pytest.mark.asyncio
async def test_cursor_subject_limit_scope_and_signature_binding(api):
    token = (await get(limit=1)).json()["page"]["next_cursor"]
    assert (await get(limit=2, cursor=token)).status_code == 422
    assert (await get(limit=1, cursor=token, model_profile="other")).status_code == 422
    assert (await get(limit=1, cursor=token[:-1] + ("0" if token[-1] != "0" else "1"))).status_code == 422
    app.dependency_overrides[get_principal] = lambda: Principal("bob", "Bob")
    assert (await get(limit=1, cursor=token)).status_code == 422


@pytest.mark.asyncio
async def test_default_switch_and_valid_expiry_use_restart_error(api):
    token = (await get(limit=1)).json()["page"]["next_cursor"]
    api[1].settings.model_profile = "other"
    assert (await get(limit=1, cursor=token)).status_code == 409
    api[1].settings.model_profile = "default"
    payload = api[1].cursors.decode(token)
    payload.update(issued=int(time.time()) - 1000, expires=int(time.time()) - 100)
    assert (await get(limit=1, cursor=api[1].cursors.encode(payload))).status_code == 409


@pytest.mark.asyncio
async def test_explicit_profile_and_backend_unavailable_are_distinct(api):
    assert (await get(model_profile="missing")).status_code == 422
    assert (await get(model_profile="other")).json()["items"] == []
    api[1].store = None
    response = await get()
    assert response.status_code == 503
    assert response.json()["code"] == "document_list_unavailable"


@pytest.mark.asyncio
async def test_missing_gateway_identity_uses_existing_safe_authentication_error(api):
    from app.config import get_settings
    app.dependency_overrides.pop(get_principal)
    app.dependency_overrides[get_settings] = lambda: settings(AUTH_MODE="gateway", DOCUMENT_LIST_CURSOR_SECRET="x" * 32)
    response = await get()
    assert response.status_code == 401
    assert response.json()["code"] == "authentication_required"
    assert api[0].requests == []


@pytest.mark.asyncio
async def test_document_list_uses_configured_chunking_default(api):
    api[1].settings.chunking_profiles["experiment"] = api[1].settings.chunking_profiles["default"]
    api[1].settings.default_chunking_profile = "experiment"
    response = await get()
    assert response.json()["scope"]["chunking_profile"] == "experiment"
    assert api[0].requests[-1] == ("alpha", "default", "experiment")


def test_gateway_requires_server_secret_for_enabled_route():
    with pytest.raises(ValueError, match="CURSOR_SECRET"):
        settings(AUTH_MODE="gateway", APP_ENV="office")


@pytest.mark.parametrize("source,title,expected", [
    (r"C:\internal\report.docx", r"C:\private\path", "report.docx"),
    ("/private/report.pdf", "/private/path", "report.pdf"),
    ("מסמך.docx", "\u202eטיפול\u2066\x00", "טיפול"),
])
def test_safe_titles_and_filenames(source, title, expected):
    display = safe_display_metadata({"source_path": source, "title": title, "source_type": "unknown-type"})
    assert display["title"] == expected
    assert "/" not in display["file_name"] and "\\" not in display["file_name"]
    assert display["document_type"] == "unknown"


@pytest.mark.parametrize("kind", ["word", "pdf", "markdown", "html", "text", "code"])
def test_backend_types_and_display_bounds(kind):
    value = safe_display_metadata({"source_path": "n" * 1000, "title": "t" * 1000, "source_type": kind})
    assert len(value["file_name"]) == 255 and len(value["title"]) == 300
    assert value["document_type"] == kind

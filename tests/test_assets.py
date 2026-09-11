from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
from httpx import ASGITransport, AsyncClient

from app.config import Settings
from app.dependencies import get_asset_store, get_vector_store, get_workspace_store
from app.domain.models import Document, DocumentAsset, SourceType
from app.identity import Principal, get_principal
from app.main import app
from app.services.asset_store import InMemoryAssetStore, LocalFileAssetStore
from app.services.ingestion_service import IngestionService
from app.services.workspace_store import AuthorizedWorkspace, InMemoryWorkspaceStore


def _settings(**overrides) -> Settings:
    values = {
        "CHAT_BASE_URL": "http://localhost:8080/v1",
        "VECTOR_STORE": "qdrant",
        "QDRANT_URL": "http://localhost:6333",
    }
    values.update(overrides)
    return Settings(**values)


@pytest.mark.asyncio
async def test_local_asset_store_round_trip_and_safe_pruning(tmp_path):
    store = LocalFileAssetStore(tmp_path / "assets")
    first_key = "a" * 64
    second_key = "b" * 64
    await store.put(first_key, b"first")
    await store.put(second_key, b"second")

    assert await store.read(first_key) == b"first"
    assert await store.delete_unreferenced({first_key}) == 1
    assert await store.read(first_key) == b"first"
    with pytest.raises(FileNotFoundError):
        await store.read(second_key)
    with pytest.raises(ValueError):
        await store.put("../escape", b"unsafe")


@pytest.mark.asyncio
async def test_ingestion_persists_and_links_embedded_asset(monkeypatch):
    document = Document(
        doc_id="guide",
        source_path="guide.docx",
        source_type=SourceType.word,
        content="Console screenshot and deployment instructions.",
        content_hash="c" * 64,
        assets=[
            DocumentAsset(
                anchor_id="image-0000",
                relationship_id="rId9",
                content=b"png-bytes",
                content_hash="d" * 64,
                media_type="image/png",
                original_name="screen.png",
                source_index=0,
                caption="Deployment console",
            )
        ],
    )
    monkeypatch.setattr("app.services.ingestion_service.load_document", lambda _: document)
    embedding_client = AsyncMock()
    embedding_client.create_embedding.return_value = [0.1]
    vector_store = AsyncMock()
    vector_store.get_document_hash.return_value = None
    asset_store = InMemoryAssetStore()

    await IngestionService(_settings(), embedding_client, vector_store, asset_store).ingest_path("guide.docx")

    stored_document, chunks, assets = vector_store.replace_document.await_args.args
    assert stored_document["content_hash"] == "c" * 64
    assert len(assets) == 1
    assert await asset_store.read("d" * 64) == b"png-bytes"
    assert chunks[0]["payload"]["related_asset_ids"] == [assets[0]["asset_id"]]
    assert chunks[0]["payload"]["related_assets"][0]["caption"] == "Deployment console"


@pytest.mark.asyncio
async def test_word_asset_dry_run_reports_without_writing(monkeypatch):
    document = Document(
        "guide", "guide.docx", SourceType.word, "Visible text",
        assets=[DocumentAsset("image-0000", "rId1", b"bytes", "a" * 64, "image/png")],
    )
    monkeypatch.setattr("app.services.ingestion_service.load_document", lambda _: document)
    embedding_client = AsyncMock()
    vector_store = AsyncMock()
    asset_store = InMemoryAssetStore()

    result = await IngestionService(_settings(), embedding_client, vector_store, asset_store).ingest_path(
        "guide.docx", dry_run=True
    )

    assert result.documents[0].assets_found == 1
    assert asset_store.items == {}
    embedding_client.create_embedding.assert_not_awaited()
    vector_store.replace_document.assert_not_awaited()


@pytest.fixture(autouse=True)
def clear_dependency_overrides():
    app.dependency_overrides.clear()
    yield
    app.dependency_overrides.clear()


def _authorized_workspaces() -> InMemoryWorkspaceStore:
    return InMemoryWorkspaceStore({"alice": [AuthorizedWorkspace("alpha", "Alpha", "owner")]})


@pytest.mark.asyncio
async def test_asset_endpoint_authorizes_and_returns_safe_headers():
    vector_store = AsyncMock()
    vector_store.get_asset_metadata.return_value = {
        "asset_id": "asset-1",
        "workspace_id": "alpha",
        "storage_key": "e" * 64,
        "content_hash": "e" * 64,
        "media_type": "image/png",
    }
    asset_store = InMemoryAssetStore()
    png_bytes = b"\x89PNG\r\n\x1a\nimage-bytes"
    await asset_store.put("e" * 64, png_bytes)
    app.dependency_overrides[get_principal] = lambda: Principal("alice", "Alice")
    app.dependency_overrides[get_workspace_store] = _authorized_workspaces
    app.dependency_overrides[get_vector_store] = lambda: vector_store
    app.dependency_overrides[get_asset_store] = lambda: asset_store

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/workspaces/alpha/assets/asset-1")
        cached = await client.get(
            "/workspaces/alpha/assets/asset-1", headers={"If-None-Match": '"' + "e" * 64 + '"'}
        )

    assert response.status_code == 200
    assert response.content == png_bytes
    assert response.headers["content-type"] == "image/png"
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["cache-control"].startswith("private")
    assert cached.status_code == 304


@pytest.mark.asyncio
async def test_asset_endpoint_rejects_unauthorized_workspace_before_lookup():
    vector_store = AsyncMock()
    app.dependency_overrides[get_principal] = lambda: Principal("alice", "Alice")
    app.dependency_overrides[get_workspace_store] = _authorized_workspaces
    app.dependency_overrides[get_vector_store] = lambda: vector_store
    app.dependency_overrides[get_asset_store] = InMemoryAssetStore

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/workspaces/beta/assets/guessed-id")

    assert response.status_code == 403
    vector_store.get_asset_metadata.assert_not_awaited()


@pytest.mark.asyncio
async def test_asset_endpoint_rejects_non_browser_media():
    vector_store = AsyncMock()
    vector_store.get_asset_metadata.return_value = {
        "asset_id": "asset-1",
        "workspace_id": "alpha",
        "storage_key": "f" * 64,
        "content_hash": "f" * 64,
        "media_type": "image/svg+xml",
    }
    app.dependency_overrides[get_principal] = lambda: Principal("alice", "Alice")
    app.dependency_overrides[get_workspace_store] = _authorized_workspaces
    app.dependency_overrides[get_vector_store] = lambda: vector_store
    app.dependency_overrides[get_asset_store] = InMemoryAssetStore

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/workspaces/alpha/assets/asset-1")

    assert response.status_code == 415
    assert response.json()["code"] == "unsupported_media_type"


@pytest.mark.asyncio
async def test_asset_endpoint_rejects_spoofed_image_content():
    vector_store = AsyncMock()
    vector_store.get_asset_metadata.return_value = {
        "asset_id": "asset-1",
        "workspace_id": "alpha",
        "storage_key": "a" * 64,
        "content_hash": "a" * 64,
        "media_type": "image/png",
    }
    asset_store = InMemoryAssetStore()
    await asset_store.put("a" * 64, b"<svg onload='alert(1)'></svg>")
    app.dependency_overrides[get_principal] = lambda: Principal("alice", "Alice")
    app.dependency_overrides[get_workspace_store] = _authorized_workspaces
    app.dependency_overrides[get_vector_store] = lambda: vector_store
    app.dependency_overrides[get_asset_store] = lambda: asset_store

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/workspaces/alpha/assets/asset-1")

    assert response.status_code == 415
    assert response.json()["code"] == "unsupported_media_type"

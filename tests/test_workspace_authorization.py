from unittest.mock import AsyncMock

import pytest
from httpx import ASGITransport, AsyncClient

from app.dependencies import get_chat_service, get_workspace_store
from app.identity import Principal, get_principal
from app.main import app
from app.services.conversation_store import InMemoryConversationStore, SessionScopeError
from app.services.workspace_store import AuthorizedWorkspace, InMemoryWorkspaceStore


@pytest.fixture(autouse=True)
def clear_overrides():
    app.dependency_overrides.clear()
    yield
    app.dependency_overrides.clear()


def _workspace_store() -> InMemoryWorkspaceStore:
    return InMemoryWorkspaceStore(
        {
            "alice": [AuthorizedWorkspace("alpha", "Alpha", "owner")],
            "bob": [AuthorizedWorkspace("alpha", "Alpha", "member")],
        }
    )


@pytest.mark.asyncio
async def test_workspace_discovery_returns_only_principal_memberships():
    app.dependency_overrides[get_principal] = lambda: Principal("alice", "Alice")
    app.dependency_overrides[get_workspace_store] = _workspace_store

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/workspaces")

    assert response.status_code == 200
    assert response.json() == {
        "principal": {"display_name": "Alice"},
        "workspaces": [
            {"workspace_id": "alpha", "display_name": "Alpha", "role": "owner"}
        ],
    }


@pytest.mark.asyncio
async def test_unauthorized_workspace_is_rejected_before_chat_service():
    chat_service = AsyncMock()
    app.dependency_overrides[get_principal] = lambda: Principal("alice", "Alice")
    app.dependency_overrides[get_workspace_store] = _workspace_store
    app.dependency_overrides[get_chat_service] = lambda: chat_service

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/chat", json={"question": "Secret?", "workspace_id": "beta"}
        )

    assert response.status_code == 403
    chat_service.answer.assert_not_awaited()


@pytest.mark.asyncio
async def test_authorized_workspace_and_principal_are_forwarded_to_chat_service():
    chat_service = AsyncMock()
    chat_service.answer.return_value = {
        "answer": "No context",
        "sources": [],
        "grounded": False,
        "session_id": "session-1",
    }
    app.dependency_overrides[get_principal] = lambda: Principal("alice", "Alice")
    app.dependency_overrides[get_workspace_store] = _workspace_store
    app.dependency_overrides[get_chat_service] = lambda: chat_service

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/chat", json={"question": "Hello", "workspace_id": "alpha"}
        )

    assert response.status_code == 200
    assert chat_service.answer.await_args.kwargs["owner_id"] == "alice"
    assert chat_service.answer.await_args.kwargs["workspace_id"] == "alpha"


@pytest.mark.asyncio
async def test_dependency_overridden_users_cannot_load_each_others_sessions():
    conversation_store = InMemoryConversationStore()
    await conversation_store.ensure_session("alice-session", "alice", "alpha", "Alice chat")
    previous_store = getattr(app.state, "conversation_store", None)
    app.state.conversation_store = conversation_store
    app.dependency_overrides[get_workspace_store] = _workspace_store
    app.dependency_overrides[get_principal] = lambda: Principal("bob", "Bob")
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/chat/sessions/alice-session")
    finally:
        if previous_store is None:
            del app.state.conversation_store
        else:
            app.state.conversation_store = previous_store

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_session_id_cannot_move_between_owner_or_workspace():
    store = InMemoryConversationStore()
    await store.ensure_session("shared-id", "alice", "alpha", "Alice chat")

    with pytest.raises(SessionScopeError):
        await store.ensure_session("shared-id", "bob", "alpha", "Bob chat")
    with pytest.raises(SessionScopeError):
        await store.ensure_session("shared-id", "alice", "beta", "Other workspace")

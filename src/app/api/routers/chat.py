import logging
import json

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse

from app.api.schemas import (
    ChatRequest,
    ChatResponse,
    ChatSessionDetail,
    ChatSessionSummary,
    RenameChatSessionRequest,
)
from app.config import Settings, get_settings
from app.dependencies import get_chat_service, get_workspace_store
from app.identity import Principal, get_principal
from app.services.chat_service import ChatService
from app.services.conversation_store import SessionScopeError
from app.services.observability import Observability
from app.services.workspace_store import WorkspaceStore, require_workspace_access

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chat", tags=["chat"])


async def _authorized_workspace(
    requested_workspace_id: str | None,
    principal: Principal,
    workspace_store: WorkspaceStore,
    settings: Settings,
) -> str:
    workspace_id = requested_workspace_id or settings.default_workspace_id
    return await require_workspace_access(workspace_id, principal, workspace_store)


@router.post("", response_model=ChatResponse)
async def chat(
    body: ChatRequest,
    chat_service: ChatService = Depends(get_chat_service),
    principal: Principal = Depends(get_principal),
    workspace_store: WorkspaceStore = Depends(get_workspace_store),
    settings: Settings = Depends(get_settings),
) -> ChatResponse:
    workspace_id = await _authorized_workspace(body.workspace_id, principal, workspace_store, settings)
    try:
        with Observability(settings).request(
            "chat.request", {"workspace_id": workspace_id, "session_id": body.session_id}
        ):
            return await chat_service.answer(
                question=body.question,
                top_k=body.top_k,
                include_debug=body.include_debug,
                session_id=body.session_id,
                workspace_id=workspace_id,
                owner_id=principal.subject,
            )
    except SessionScopeError as exc:
        raise HTTPException(status_code=404, detail="Chat session not found") from exc
    except Exception as exc:
        logger.exception("Chat upstream error: %s", exc)
        raise HTTPException(status_code=502, detail=f"Upstream provider error: {exc}") from exc


@router.post("/stream")
async def chat_stream(
    body: ChatRequest,
    request: Request,
    chat_service: ChatService = Depends(get_chat_service),
    principal: Principal = Depends(get_principal),
    workspace_store: WorkspaceStore = Depends(get_workspace_store),
    settings: Settings = Depends(get_settings),
):
    workspace_id = await _authorized_workspace(body.workspace_id, principal, workspace_store, settings)
    if body.session_id:
        try:
            await request.app.state.conversation_store.ensure_session(
                body.session_id, principal.subject, workspace_id, body.question[:80]
            )
        except SessionScopeError as exc:
            raise HTTPException(status_code=404, detail="Chat session not found") from exc

    async def events():
        try:
            async for event in chat_service.answer_stream(
                question=body.question,
                top_k=body.top_k,
                include_debug=body.include_debug,
                session_id=body.session_id,
                workspace_id=workspace_id,
                owner_id=principal.subject,
            ):
                yield event
        except Exception:
            logger.exception("Chat stream failed")
            payload = {"code": "stream_interrupted", "message": "The answer stream was interrupted. Please try again."}
            yield f"event: error\ndata: {json.dumps(payload)}\n\n"
            yield 'event: done\ndata: {"reason":"error"}\n\n'

    return StreamingResponse(
        events(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("/sessions", response_model=list[ChatSessionSummary])
async def list_sessions(
    request: Request,
    workspace_id: str = Query(min_length=1),
    principal: Principal = Depends(get_principal),
    workspace_store: WorkspaceStore = Depends(get_workspace_store),
):
    await require_workspace_access(workspace_id, principal, workspace_store)
    return await request.app.state.conversation_store.list_sessions(principal.subject, workspace_id)


async def _owned_authorized_session(
    session_id: str,
    request: Request,
    principal: Principal,
    workspace_store: WorkspaceStore,
) -> dict:
    item = await request.app.state.conversation_store.get_session(session_id, principal.subject)
    if not item:
        raise HTTPException(status_code=404, detail="Chat session not found")
    await require_workspace_access(item["workspace_id"], principal, workspace_store)
    return item


@router.get("/sessions/{session_id}", response_model=ChatSessionDetail)
async def get_session(
    session_id: str,
    request: Request,
    principal: Principal = Depends(get_principal),
    workspace_store: WorkspaceStore = Depends(get_workspace_store),
):
    return await _owned_authorized_session(session_id, request, principal, workspace_store)


@router.patch("/sessions/{session_id}")
async def rename_session(
    session_id: str,
    body: RenameChatSessionRequest,
    request: Request,
    principal: Principal = Depends(get_principal),
    workspace_store: WorkspaceStore = Depends(get_workspace_store),
):
    item = await _owned_authorized_session(session_id, request, principal, workspace_store)
    changed = await request.app.state.conversation_store.rename_session(
        session_id, principal.subject, item["workspace_id"], body.title
    )
    if not changed:
        raise HTTPException(status_code=404, detail="Chat session not found")
    return {"ok": True}


@router.delete("/sessions/{session_id}", status_code=204)
async def archive_session(
    session_id: str,
    request: Request,
    principal: Principal = Depends(get_principal),
    workspace_store: WorkspaceStore = Depends(get_workspace_store),
):
    item = await _owned_authorized_session(session_id, request, principal, workspace_store)
    changed = await request.app.state.conversation_store.archive_session(
        session_id, principal.subject, item["workspace_id"]
    )
    if not changed:
        raise HTTPException(status_code=404, detail="Chat session not found")

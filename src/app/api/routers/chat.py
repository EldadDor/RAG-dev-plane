import logging

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from app.api.schemas import ChatRequest, ChatResponse, ChatSessionDetail, ChatSessionSummary, RenameChatSessionRequest
from app.dependencies import get_chat_service, get_current_user
from app.services.chat_service import ChatService
from app.services.observability import Observability
from app.config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
async def chat(
        request: ChatRequest,
        chat_service: ChatService = Depends(get_chat_service),
        user_id: str = Depends(get_current_user),
) -> ChatResponse:
    try:
        with Observability(get_settings()).request("chat.request", {"workspace_id": request.workspace_id, "session_id": request.session_id}):
            return await chat_service.answer(
            question=request.question,
            top_k=request.top_k,
            include_debug=request.include_debug,
            session_id=request.session_id,
            workspace_id=request.workspace_id,
            owner_id=user_id,
            )
    except Exception as exc:
        logger.exception("Chat upstream error: %s", exc)
        raise HTTPException(status_code=502, detail=f"Upstream provider error: {exc}") from exc

@router.post("/stream")
async def chat_stream(request: ChatRequest, chat_service: ChatService = Depends(get_chat_service), user_id: str = Depends(get_current_user)):
    async def events():
        async for event in chat_service.answer_stream(question=request.question, top_k=request.top_k, include_debug=request.include_debug, session_id=request.session_id, workspace_id=request.workspace_id, owner_id=user_id): yield event
    return StreamingResponse(events(), media_type="text/event-stream")

@router.get("/sessions", response_model=list[ChatSessionSummary])
async def list_sessions(workspace_id: str, request, user_id: str = Depends(get_current_user)):
    return await request.app.state.conversation_store.list_sessions(user_id, workspace_id)

@router.get("/sessions/{session_id}", response_model=ChatSessionDetail)
async def get_session(session_id: str, request, user_id: str = Depends(get_current_user)):
    item = await request.app.state.conversation_store.get_session(session_id, user_id)
    if not item: raise HTTPException(status_code=404, detail="Chat session not found")
    return item

@router.patch("/sessions/{session_id}")
async def rename_session(session_id: str, body: RenameChatSessionRequest, request, user_id: str = Depends(get_current_user)):
    if not await request.app.state.conversation_store.rename_session(session_id, user_id, body.title): raise HTTPException(status_code=404, detail="Chat session not found")
    return {"ok": True}

@router.delete("/sessions/{session_id}", status_code=204)
async def archive_session(session_id: str, request, user_id: str = Depends(get_current_user)):
    if not await request.app.state.conversation_store.archive_session(session_id, user_id): raise HTTPException(status_code=404, detail="Chat session not found")

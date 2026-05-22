from fastapi import APIRouter, Depends, HTTPException

from app.api.schemas import ChatRequest, ChatResponse
from app.dependencies import get_chat_service
from app.services.chat_service import ChatService

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    chat_service: ChatService = Depends(get_chat_service),
) -> ChatResponse:
    try:
        return await chat_service.answer(
            question=request.question,
            top_k=request.top_k,
            include_debug=request.debug,
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Upstream provider error") from exc

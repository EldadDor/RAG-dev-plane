from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.api.schemas import ChatRequest, ChatResponse
from app.dependencies import get_chat_service
from app.services.chat_service import ChatService

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, chat_service: ChatService = Depends(get_chat_service)):
    return await chat_service.answer(
        question=request.question,
        top_k=request.top_k,
        include_debug=request.include_debug,
        session_id=request.session_id,
    )


@router.post("/chat/stream")
async def chat_stream(request: ChatRequest, chat_service: ChatService = Depends(get_chat_service)):
    async def event_stream():
        async for chunk in chat_service.answer_stream(
                question=request.question,
                top_k=request.top_k,
                include_debug=request.include_debug,
                session_id=request.session_id,
        ):
            yield chunk
    return StreamingResponse(event_stream(), media_type="text/event-stream")

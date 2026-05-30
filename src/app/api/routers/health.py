from fastapi import APIRouter, Depends

from app.api.schemas import HealthResponse, ReadinessResponse
from app.clients.vector_store import VectorStore
from app.config import Settings, get_settings
from app.dependencies import get_vector_store

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health(settings: Settings = Depends(get_settings)) -> HealthResponse:
    return HealthResponse(status="ok", environment=settings.app_env)


@router.get("/readiness", response_model=ReadinessResponse)
async def readiness(
    vector_store: VectorStore = Depends(get_vector_store),
    settings: Settings = Depends(get_settings),
) -> ReadinessResponse:
    store_ok = await vector_store.health_check()
    overall = "ok" if store_ok else "degraded"
    return ReadinessResponse(
        status=overall,
        vector_store="ok" if store_ok else "unreachable",
        details={
            "chat_model": settings.chat_model,
            "embedding_model": settings.embedding_model,
            "vector_store_type": settings.vector_store,
        },
    )

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routers import chat, health, ingest
from app.config import get_settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    logger.info(
        "Starting RAG service | env=%s chat_model=%s embedding_model=%s",
        settings.app_env,
        settings.chat_model,
        settings.embedding_model,
    )
    yield
    logger.info("Shutting down RAG service")


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Developer RAG Service",
        description="Retrieval-augmented generation over internal developer documentation.",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if settings.app_env == "local" else [],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router)
    app.include_router(chat.router)
    app.include_router(ingest.router)

    return app


app = create_app()

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routers import chat, health, ingest
from app.config import Settings, get_settings
from app.logging_config import configure_logging

# Configure logging before anything else
configure_logging()
logger = logging.getLogger(__name__)


async def _init_pg_vector_store(settings: Settings):
    """Create the asyncpg pool and return an initialised PgVectorStore."""
    from app.clients.pg_vector_store import PgVectorStore

    password: str | None
    if settings.pg_use_entra:
        from app.clients.azure_auth import get_azure_postgres_token
        password = get_azure_postgres_token()
    else:
        password = settings.pg_password

    return await PgVectorStore.create(
        host=settings.pg_host or "",
        port=settings.pg_port,
        database=settings.pg_database,
        user=settings.pg_user or "",
        password=password,
        sslmode=settings.pg_sslmode,
        table=settings.pg_table,
        vector_dim=settings.pg_vector_dim,
    )


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()

    if settings.vector_store == "postgres":
        app.state.vector_store = await _init_pg_vector_store(settings)
        logger.info(
            "📊 PostgreSQL vector store ready | table=%s dim=%d",
            settings.pg_table,
            settings.pg_vector_dim,
        )

    logger.info(
        "🚀 Starting RAG service | env=%s chat=%s/%s embed=%s/%s store=%s",
        settings.app_env,
        settings.chat_provider,
        settings.chat_model,
        settings.embedding_provider,
        settings.embedding_model,
        settings.vector_store,
    )
    if settings.vector_store == "qdrant":
        logger.info("📍 Backends: Qdrant=%s Ollama=%s", settings.qdrant_url, settings.embedding_base_url)
    elif settings.vector_store == "postgres":
        logger.info("📍 Backends: PostgreSQL=%s:%d/%s", settings.pg_host, settings.pg_port, settings.pg_database)

    yield

    if settings.vector_store == "postgres" and hasattr(app.state, "vector_store"):
        await app.state.vector_store.close()
        logger.info("📊 PostgreSQL connection pool closed")

    logger.info("🛑 Shutting down RAG service")


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
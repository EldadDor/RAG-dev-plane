# Developer RAG Service

Starter skeleton for a developer-facing RAG backend built with FastAPI, Pydantic v2, Qdrant, and OpenAI-compatible clients.

## Stack
- Python 3.12+
- uv
- FastAPI
- Pydantic v2
- Qdrant
- pytest
- Docker Compose

## Quick start
```bash
uv sync
cp .env.example .env
uv run uvicorn app.main:app --reload --app-dir src
```

## Docker Compose
```bash
docker compose up -d qdrant
uv run uvicorn app.main:app --reload --app-dir src
```

## Layout
- `src/app/config.py` typed settings
- `src/app/domain/models.py` core data models
- `src/app/api/schemas.py` API request and response models
- `src/app/services/*` ingestion, retrieval, and chat orchestration
- `src/app/clients/*` provider and vector store adapters
- `tests/` starter test coverage

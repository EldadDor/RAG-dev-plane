# Developer RAG Service

Production-oriented RAG backend built with FastAPI, Pydantic v2, Qdrant, and OpenAI-compatible clients.

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
# edit .env with your CHAT_BASE_URL and other settings
uv run uvicorn app.main:app --reload --app-dir src
```

## Docker Compose
```bash
# Start Qdrant only (Ollama runs externally)
docker compose up -d qdrant

# Start everything (requires .env)
docker compose up -d
```

## Ingest documents
```bash
curl -X POST http://localhost:8000/ingest \
  -H "Content-Type: application/json" \
  -d '{"source_path": "docs/", "recursive": true}'
```

## Ask a question
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "How does the ingestion pipeline work?"}'
```

## Run tests
```bash
uv run python -m pytest tests/ -v
```

## Layout
```
src/app/
├── main.py                   FastAPI app factory
├── config.py                 Typed settings (Pydantic v2)
├── dependencies.py           FastAPI dependency wiring
├── domain/
│   └── models.py             Document, Chunk, RetrievedChunk
├── api/
│   ├── schemas.py            ChatRequest/Response, IngestRequest/Response
│   └── routers/
│       ├── chat.py           POST /chat
│       ├── ingest.py         POST /ingest
│       └── health.py         GET /health, GET /readiness
├── clients/
│   ├── chat_client.py        OpenAI-compatible chat adapter
│   ├── embedding_client.py   Ollama embedding adapter
│   └── qdrant_client.py      Qdrant vector store adapter
├── services/
│   ├── chat_service.py       Retrieval → prompt → answer orchestration
│   ├── retrieval_service.py  Embed query → vector search
│   └── ingestion_service.py  Load → chunk → embed → upsert pipeline
├── loaders/
│   ├── registry.py           Loader dispatch by file extension
│   ├── markdown_loader.py    .md / .mdx
│   ├── html_loader.py        .html / .htm
│   ├── text_loader.py        .txt
│   └── pdf_loader.py         .pdf
├── chunkers/
│   ├── text_chunker.py       Recursive + markdown-header chunking
│   └── ids.py                Deterministic doc/chunk ID generation
└── prompts/
    └── chat_prompt.py        build_context_prompt() + abstention instruction
tests/                        Unit tests for all layers
```


# Developer RAG Service

Production-oriented RAG backend built with FastAPI, Pydantic v2, PostgreSQL + pgvector, and OpenAI-compatible clients.

## Stack
- Python 3.12+
- uv
- FastAPI
- Pydantic v2
- PostgreSQL + pgvector (default; Qdrant still supported)
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
# Start PostgreSQL + pgvector only (Ollama runs externally)
docker compose up -d postgres-pgvector

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

PostgreSQL retrieval uses hybrid search by default: pgvector semantic search
plus PostgreSQL full-text search, fused with reciprocal-rank fusion. This is
especially useful for file paths, code symbols, configuration names, and error
messages. Set `HYBRID_SEARCH_ENABLED=false` to use semantic search alone.

Python repositories can be ingested directly. Python files are chunked by
module/class/function and retain language, symbol, line-range, Git branch,
commit, repository, and repository-relative-path metadata. Other common code
and configuration extensions are indexed with language metadata.

Java files use Tree-sitter parsing and are chunked into package/import
preambles, type headers, and fields/methods/constructors. Chunks preserve the
fully qualified in-file symbol, enclosing type, and line range. Malformed Java
falls back to generic text chunking rather than failing ingestion.

## Local-model performance and logs

The chat client logs request start, completion/failure, elapsed time, prompt
length, output length, and model name without writing prompt or document
content to logs. For slower local GPUs, tune `CHAT_TIMEOUT_SECONDS` (default
`240`) and `CHAT_MAX_TOKENS` (default `400`). `CHAT_THINK=false` is the normal
RAG setting; enable it only for Ollama models that explicitly support thinking
and where the added latency is acceptable.

`/chat` returns a `session_id`. Send it with a follow-up request to retain a
short conversation memory. With PostgreSQL this memory is shared across API
workers and retained for `MEMORY_RETENTION_DAYS` (90 days by default). A
compact session summary refreshes after `MEMORY_SUMMARY_AFTER_TURNS` new turns
(8 by default). Memory is kept separate from the document index and is not
embedded for retrieval.

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
│   ├── qdrant_client.py      Qdrant vector store adapter
│   └── pg_vector_store.py    PostgreSQL + pgvector adapter
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


# AGENTS.md

This repository implements a production-oriented RAG system for internal developer documentation and chat.

## Stack baseline
- Python 3.12+
- `uv` for dependency management and execution
- FastAPI for HTTP API
- Pydantic v2 for typed settings and schemas
- Qdrant as the vector database
- OpenAI-compatible chat provider for answer generation
- Ollama embedding provider for local embeddings
- Pytest for tests
- Docker and Docker Compose for local infrastructure

## Current provider defaults
- Chat model: `qwen2.5:7b-instruct-q4_K_M`
- Chat endpoint: configured through `CHAT_BASE_URL`
- Embedding model: `mxbai-embed-large`
- Embedding endpoint: configured through `EMBEDDING_BASE_URL`

## Architecture rules
- Keep chat generation and embedding generation in separate client adapters.
- Retrieval must depend on the embedding client, not the chat client.
- Chat answer synthesis must depend on the chat client, not the embedding client.
- Qdrant payloads must preserve provenance-rich metadata.
- Prompt templates must be centrally managed and reused.

## Delivery rules for coding agents
- Preserve the dual-provider model unless explicitly asked to unify it.
- If adding a new provider, do so behind the existing adapter pattern.
- Update `.env.example`, docs, and tests whenever provider configuration changes.
- Keep the default local embedding path working without cloud calls.

# Copilot instructions

This repository is a Python 3.12+ RAG service for internal developer knowledge retrieval.

## Current baseline stack
- Use `uv` for Python package management and command execution.
- Use FastAPI for the API layer.
- Use Pydantic v2 for typed settings and API schemas.
- Use Qdrant as the vector database.
- Use an OpenAI-compatible chat provider for generation.
- Use Ollama for local embeddings by default.
- Use pytest for tests.
- Use Docker and Docker Compose for local infrastructure.

## Current provider defaults
- Chat provider: OpenAI-compatible endpoint at `CHAT_BASE_URL`.
- Default chat model: `Qwen3-Coder-30B-A3B-Instruct-Q4_K_M`.
- Embedding provider: Ollama at `EMBEDDING_BASE_URL`.
- Default embedding model: `mxbai-embed-large`.

## Implementation rules
- Keep chat and embedding providers separate in code, config, and dependencies.
- Do not assume the chat provider can also generate embeddings.
- Preserve provenance metadata through ingestion, indexing, retrieval, and answer generation.
- Route handlers stay thin; orchestration belongs in service modules.
- Provider-specific calls must stay inside dedicated client adapters.

## Configuration rules
- Read configuration from environment variables via typed settings.
- Do not hardcode model names, base URLs, or API keys outside config defaults.
- Update `.env.example` and docs whenever provider configuration changes.

## RAG behavior rules
- Answer only from retrieved context.
- If evidence is insufficient, return an explicit abstention.
- Include structured source references in response payloads.
- Do not fabricate provenance or confidence.

## Avoid these mistakes
- Do not collapse chat and embedding settings into one shared provider unless explicitly requested.
- Do not scatter Ollama or OpenAI-compatible HTTP calls across unrelated modules.
- Do not return plain answer text without sources.

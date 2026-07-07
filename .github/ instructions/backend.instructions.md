---
applyTo: "src/**/*.py,tests/**/*.py,pyproject.toml,.env.example,Dockerfile,docker-compose*.yml"
---

# Backend stack instructions

## Current stack
- Python 3.12+
- `uv`
- FastAPI
- Pydantic v2
- PostgreSQL + pgvector as the default vector database (matches RAG_Embabel-AI local profile)
- Qdrant remains supported as an alternative vector store
- OpenAI-compatible chat provider
- Ollama embedding provider
- pytest

## Implementation rules
- Keep typed settings in a centralized module.
- Keep separate environment variables for chat and embedding providers.
- Preserve the local embedding path as a first-class use case.
- Update `.env.example` and README whenever defaults change.
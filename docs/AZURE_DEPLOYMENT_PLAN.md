Now let me create the full plan file.

<llm-snippet-file>docs/AZURE_DEPLOYMENT_PLAN.md</llm-snippet-file>
```markdown
# Azure Deployment & Migration Plan

Migrating the Developer RAG Service from a local stack
(Qdrant + Ollama + OpenAI-compatible llama.cpp) to **Azure**:

- **Chat model:** Azure OpenAI (`gpt-4o-mini` / `gpt-4o`)
- **Embeddings:** Azure OpenAI (`text-embedding-3-small` / `-large`)
- **Vector DB:** PostgreSQL + `pgvector` (Azure Database for PostgreSQL Flexible Server)
- **Hosting:** Single Dockerfile (no docker-compose) → Azure Container Apps / App Service
- **Auth:** Microsoft Entra ID (Managed Identity) preferred, API keys as fallback

---

## 0. Target architecture

```
            ┌────────────────────────────────────────────────────┐
            │                 Azure Container App                 │
            │             (FastAPI RAG service, Docker)           │
            │                                                     │
  client ─► │  /chat   ─► RetrievalService ─► EmbeddingClient ──┐ │
            │            └► ChatService ─► ChatClient ────────┐  │ │
            │  /ingest ─► IngestionService ─► VectorStore ─┐  │  │ │
            └──────────────────────────────────────────────┼──┼──┼─┘
                                                            │  │  │
                       ┌────────────────────────────────────┘  │  │
                       ▼                                        ▼  ▼
        ┌───────────────────────────┐        ┌──────────────────────────────┐
        │ Azure Database for         │        │      Azure OpenAI            │
        │ PostgreSQL Flexible Server │        │  - chat deployment (gpt-4o*) │
        │   + pgvector extension     │        │  - embed deployment (3-small)│
        └───────────────────────────┘        └──────────────────────────────┘
```

Auth path: Container App **Managed Identity** → Entra ID token → Azure OpenAI + Postgres.

---

## 1. Provider / model decisions

### 1.1 Chat model (Azure OpenAI)
| Option | When to use |
|--------|-------------|
| `gpt-4o-mini` | Default. Cheap, fast, strong enough for doc Q&A. **Start here.** |
| `gpt-4o`      | When answer quality / reasoning matters more than cost. |

Notes:
- Create a **deployment** in Azure OpenAI; the *deployment name* (not the base model name)
  is what we pass as `CHAT_MODEL`.
- Endpoint shape: `https://<resource>.openai.azure.com/`
- Calls require an `api-version` (e.g. `2024-10-21`) and use header `api-key:` **or** a Bearer Entra token.

### 1.2 Embeddings (Azure OpenAI)
| Model | Dimensions | Notes |
|-------|-----------|-------|
| `text-embedding-3-small` | 1536 | **Default.** Cheap, good quality. |
| `text-embedding-3-large` | 3072 | Higher quality, higher cost/storage. |

> ⚠️ **Dimension change:** local `mxbai-embed-large` = 1024 dims.
> Azure `3-small` = 1536, `3-large` = 3072. The vector column dimension **must match**,
> and **all documents must be re-ingested** after switching embedding models.

### 1.3 Vector DB (Postgres + pgvector)
- Use **Azure Database for PostgreSQL – Flexible Server**.
- Enable the `vector` (pgvector) extension (allow-list it in server parameters).
- One table for chunks; an `HNSW` or `IVFFlat` index on the embedding column.

---

## 2. Configuration changes (`.env` / settings)

### 2.1 New environment variables

```dotenv
APP_ENV=production
LOG_LEVEL=INFO
API_HOST=0.0.0.0
API_PORT=8000

# ---- Vector store selection ----
VECTOR_STORE=postgres            # qdrant | postgres

# ---- Postgres (pgvector) ----
PG_HOST=<server>.postgres.database.azure.com
PG_PORT=5432
PG_DATABASE=ragdb
PG_USER=<entra-or-pg-user>
PG_PASSWORD=                     # empty when using Entra/Managed Identity
PG_SSLMODE=require
PG_USE_ENTRA=true                # use Managed Identity token as password
PG_TABLE=document_chunks
PG_VECTOR_DIM=1536               # MUST match embedding model dims

# ---- Chat: Azure OpenAI ----
CHAT_PROVIDER=azure_openai       # openai_compatible | azure_openai
AZURE_OPENAI_ENDPOINT=https://<resource>.openai.azure.com
AZURE_OPENAI_API_VERSION=2024-10-21
AZURE_OPENAI_USE_ENTRA=true      # true = Managed Identity, false = api-key
CHAT_API_KEY=                    # only if USE_ENTRA=false
CHAT_MODEL=gpt-4o-mini           # = Azure deployment name

# ---- Embeddings: Azure OpenAI ----
EMBEDDING_PROVIDER=azure_openai  # ollama | azure_openai
EMBEDDING_MODEL=text-embedding-3-small   # = Azure deployment name
# (reuses AZURE_OPENAI_ENDPOINT / API_VERSION / USE_ENTRA / key)

# ---- RAG tuning ----
TOP_K=5
CHUNK_SIZE=800
CHUNK_OVERLAP=120
RERANK_ENABLED=false
```

### 2.2 `config.py` additions
Add typed fields for everything above:
- `vector_store: str`
- Postgres block: `pg_host`, `pg_port`, `pg_database`, `pg_user`, `pg_password`,
  `pg_sslmode`, `pg_use_entra`, `pg_table`, `pg_vector_dim`
- Azure block: `azure_openai_endpoint`, `azure_openai_api_version`,
  `azure_openai_use_entra`
- Keep existing Qdrant + Ollama fields so **local dev still works**.

---

## 3. Code changes (abstraction work)

The current code is hardwired to Ollama embeddings and Qdrant. Introduce
provider switches so the same codebase runs locally and on Azure.

### 3.1 Embeddings — add Azure provider
- Keep the existing `EmbeddingClient` Protocol.
- New `AzureOpenAIEmbeddingClient` calling:
  `POST {endpoint}/openai/deployments/{model}/embeddings?api-version=...`
- Update `get_embedding_client()` to branch on `EMBEDDING_PROVIDER`:
  - `ollama` → existing `OllamaEmbeddingClient`
  - `azure_openai` → new client

### 3.2 Chat — make client Azure-aware
- Current client sends `Authorization: Bearer` to `{base_url}/chat/completions`.
- Azure OpenAI needs:
  - URL: `{endpoint}/openai/deployments/{deployment}/chat/completions?api-version=...`
  - Header `api-key: <key>` **or** `Authorization: Bearer <entra-token>`
- Add `AzureOpenAIChatClient` (or extend existing client) and branch in
  `get_chat_client()` on `CHAT_PROVIDER`.

### 3.3 Vector store — add Postgres/pgvector
- Define a `VectorStore` Protocol matching the existing methods:
  `ensure_collection`, `upsert`, `search`, `health_check`.
- New `PgVectorStore` (use `asyncpg` or SQLAlchemy async + `pgvector`):
  - `ensure_collection(dim)` → `CREATE EXTENSION IF NOT EXISTS vector;`
    + `CREATE TABLE IF NOT EXISTS document_chunks(...)` + HNSW index.
  - `upsert(chunks)` → `INSERT ... ON CONFLICT (chunk_id) DO UPDATE`.
  - `search(vector, limit)` → `ORDER BY embedding <=> $1 LIMIT k`
    (cosine distance), returning `RetrievedChunk`.
- Update `get_vector_store()` to branch on `VECTOR_STORE`
  (`qdrant` → `QdrantVectorStore`, `postgres` → `PgVectorStore`).

### 3.4 Entra ID auth helper
- Add `azure-identity` dependency.
- Helper that returns a token via `DefaultAzureCredential`
  (works with Managed Identity in Azure, `az login` locally):
  - Azure OpenAI scope: `https://cognitiveservices.azure.com/.default`
  - Postgres scope: `https://ossrdbms-aad.database.windows.net/.default`
- Cache/refresh tokens (they expire ~60 min).

### 3.5 Proposed table DDL (pgvector)
```sql
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS document_chunks (
    chunk_id    TEXT PRIMARY KEY,
    doc_id      TEXT NOT NULL,
    source_path TEXT NOT NULL,
    title       TEXT,
    section     TEXT,
    page        INT,
    text        TEXT NOT NULL,
    embedding   VECTOR(1536) NOT NULL          -- match PG_VECTOR_DIM
);

CREATE INDEX IF NOT EXISTS idx_chunks_embedding
    ON document_chunks
    USING hnsw (embedding vector_cosine_ops);
```

---

## 4. Dependencies (`pyproject.toml`)

Add:
```toml
"asyncpg>=0.29.0",          # async Postgres driver
"pgvector>=0.3.0",          # vector type adapters
"azure-identity>=1.17.0",   # Entra ID / Managed Identity
```
`qdrant-client` can stay (local dev) or move to an optional extra.

---

## 5. New Dockerfile (no docker-compose)

A production single-image build. Multi-stage keeps the runtime small and
runs as a non-root user.

```dockerfile
# ---- Stage 1: build deps ----
FROM python:3.12-slim AS builder
WORKDIR /app
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock README.md ./
RUN uv sync --no-dev --frozen

# ---- Stage 2: runtime ----
FROM python:3.12-slim AS runtime
WORKDIR /app
# libpq for asyncpg/ssl is statically bundled, but keep ca-certs fresh
RUN apt-get update && apt-get install -y --no-install-recommends \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# non-root
RUN useradd --create-home --uid 10001 appuser

COPY --from=builder /app/.venv /app/.venv
COPY src/ src/

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONPATH=/app/src \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    API_PORT=8000

USER appuser
EXPOSE 8000

# Container App / App Service health probe should hit /health
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--app-dir", "src"]
```

> Tip: keep `uv.lock` committed so `uv sync --frozen` builds are reproducible.

---

## 6. Azure resource provisioning (one-time)

1. **Resource group**, e.g. `rg-rag-prod`.
2. **Azure OpenAI** resource:
   - Deploy `gpt-4o-mini` (chat) and `text-embedding-3-small` (embeddings).
   - Note the **deployment names** → `CHAT_MODEL`, `EMBEDDING_MODEL`.
   - Endpoint → `AZURE_OPENAI_ENDPOINT`.
3. **Azure Database for PostgreSQL – Flexible Server**:
   - Enable Entra authentication.
   - Server parameters: add `vector` to `azure.extensions`.
   - Create DB `ragdb`; firewall/VNet to allow the Container App.
4. **Azure Container Registry (ACR)** to push the image.
5. **Azure Container App** (or App Service for Containers):
   - Enable **system-assigned Managed Identity**.
   - Grant identity:
     - Azure OpenAI → role **Cognitive Services OpenAI User**.
     - Postgres → add identity as an Entra DB user with table privileges.
   - Set env vars (section 2) — secrets via Key Vault references if key-based.
6. **(Optional) Key Vault** for any non-Entra secrets.

---

## 7. Migration / re-ingestion

Because embedding dimensions change (1024 → 1536/3072):
1. Provision Postgres + create table with the **new** `PG_VECTOR_DIM`.
2. Deploy the app with Azure providers configured.
3. Re-run ingestion against the source docs:
   ```bash
   curl -X POST https://<app-url>/ingest \
     -H "Content-Type: application/json" \
     -d '{"source_path": "docs/", "recursive": true}'
   ```
4. Validate with `/chat` and check `/readiness`.

> Old Qdrant vectors are **not** reusable across embedding models — full re-ingest is required.

---

## 8. Testing & validation

- **Unit tests:** add tests for `AzureOpenAIChatClient`, `AzureOpenAIEmbeddingClient`,
  and `PgVectorStore` (mock httpx / use a test Postgres or `pytest` fixtures).
- **Provider parity:** keep local (Qdrant+Ollama) tests green so dev still works.
- **Integration smoke test:** ingest a tiny doc set → `/chat` → assert grounded answer.
- **Health:** `/health` (liveness) and `/readiness` (checks Azure OpenAI + Postgres reachable).
- **Security:** confirm no API keys in logs; confirm Managed Identity path works
  (run with `az login` locally, Managed Identity in Azure).

---

## 9. Rollout checklist

- [ ] `config.py` extended with Azure + Postgres fields
- [ ] `AzureOpenAIEmbeddingClient` + provider switch
- [ ] `AzureOpenAIChatClient` + provider switch
- [ ] `PgVectorStore` + `VECTOR_STORE` switch + DDL/index
- [ ] `azure-identity`, `asyncpg`, `pgvector` added to deps + `uv.lock` updated
- [ ] New multi-stage Dockerfile, non-root, builds & runs locally
- [ ] `.env.example` updated with Azure/Postgres keys (no real secrets)
- [ ] Azure resources provisioned (OpenAI, Postgres+pgvector, ACR, Container App, identity/roles)
- [ ] Image pushed to ACR & Container App deployed
- [ ] Re-ingestion run; `/chat` validated
- [ ] Old Qdrant/docker-compose references removed or marked dev-only in README

---

## 10. Cost & operational notes

- `gpt-4o-mini` + `text-embedding-3-small` is the low-cost combo; embeddings cost is
  dominated by the **one-time ingest** + per-query embedding of the question.
- Postgres Flexible Server: pick a burstable tier for dev, general-purpose for prod;
  HNSW index trades build time for fast queries.
- Set sensible `httpx` timeouts and add retry/backoff for Azure OpenAI 429s
  (rate limits) — recommended before prod traffic.
```

---

I've created **`docs/AZURE_DEPLOYMENT_PLAN.md`** with the complete plan. Here's the summary of what it covers and the most important things to be aware of:

### The big "gotchas" baked into the plan
1. **Embedding dimensions change** → `mxbai-embed-large` is **1024**, Azure `text-embedding-3-small` is **1536** (`-large` is 3072). The pgvector column dimension must match, and **you must re-ingest all docs** — old vectors can't be reused.
2. **It's not just `.env`.** Your code currently hardwires Ollama embeddings and Qdrant. The plan adds provider switches (`EMBEDDING_PROVIDER`, `VECTOR_STORE`, `CHAT_PROVIDER`) so the same code runs locally *and* on Azure.
3. **Azure OpenAI URL/auth differs** from your current OpenAI-compatible client: it uses `/openai/deployments/{name}/...?api-version=...` and an `api-key` header or an Entra Bearer token — hence the small chat-client change.
4. **`CHAT_MODEL`/`EMBEDDING_MODEL` become Azure *deployment names***, not model names.

### Recommended Azure choices (the plan's defaults)
- **Chat:** `gpt-4o-mini` (start here) → `gpt-4o` for quality.
- **Embeddings:** `text-embedding-3-small`.
- **Vector DB:** Azure Database for PostgreSQL Flexible Server + `pgvector` (HNSW index, cosine).
- **Auth:** Managed Identity (Entra ID) preferred over keys.

The plan file includes a **new multi-stage, non-root Dockerfile** (no compose), the **pgvector table DDL**, the **new `.env` variables**, the **dependency additions** (`asyncpg`, `pgvector`, `azure-identity`), Azure provisioning steps, the re-ingestion procedure, and a rollout checklist.

Want me to start implementing any part of this — e.g. the `config.py` fields, the `PgVectorStore`, or the Azure chat/embedding clients?
Before answering it did these function calls:
              functionName: MCP tool /get_file_text_by_path
              parameters: {"pathInProject": "src/app/dependencies.py"}
              content: from fastapi import Depends

from app.clients.chat_client import OpenAICompatibleChatClient
from app.clients.embedding_client import EmbeddingClient, OllamaEmbeddingClient
from app.clients.qdrant_client import QdrantVectorStore
from app.config import Settings, get_settings
from app.services.chat_service import ChatService
from app.services.ingestion_service import IngestionService
from app.services.retrieval_service import RetrievalService


def get_chat_client(settings: Settings = Depends(get_settings)) -> OpenAICompatibleChatClient:
    return OpenAICompatibleChatClient(base_url=settings.chat_base_url, api_key=settings.chat_api_key)


def get_embedding_client(settings: Settings = Depends(get_settings)) -> EmbeddingClient:
    if settings.embedding_provider == "ollama":
        return OllamaEmbeddingClient(base_url=settings.embedding_base_url)
    raise ValueError(f"Unsupported embedding provider: {settings.embedding_provider}")


def get_vector_store(settings: Settings = Depends(get_settings)) -> QdrantVectorStore:
    return QdrantVectorStore(
        url=settings.qdrant_url,
        api_key=settings.qdrant_api_key,
        collection_name=settings.qdrant_collection,
    )


def get_retrieval_service(
    settings: Settings = Depends(get_settings),
    embedding_client: EmbeddingClient = Depends(get_embedding_client),
    vector_store: QdrantVectorStore = Depends(get_vector_store),
) -> RetrievalService:
    return RetrievalService(settings=settings, embedding_client=embedding_client, vector_store=vector_store)


def get_chat_service(
    settings: Settings = Depends(get_settings),
    retrieval_service: RetrievalService = Depends(get_retrieval_service),
    chat_client: OpenAICompatibleChatClient = Depends(get_chat_client),
) -> ChatService:
    return ChatService(settings=settings, retrieval_service=retrieval_service, chat_client=chat_client)


def get_ingestion_service(
    settings: Settings = Depends(get_settings),
    embedding_client: EmbeddingClient = Depends(get_embedding_client),
    vector_store: QdrantVectorStore = Depends(get_vector_store),
) -> IngestionService:
    return IngestionService(
        settings=settings,
        embedding_client=embedding_client,
        vector_store=vector_store,
    )

---------------------------------------------------------------------------------------------------------------------
              functionName: MCP tool /get_file_text_by_path
              parameters: {"pathInProject": "src/app/clients/embedding_client.py"}
              content: from typing import Protocol

import httpx


class EmbeddingClient(Protocol):
    async def create_embedding(self, model: str, text: str) -> list[float]: ...


class OllamaEmbeddingClient:
    def __init__(self, base_url: str, timeout: float = 30.0) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout

    async def create_embedding(self, model: str, text: str) -> list[float]:
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.post(
                f"{self._base_url}/api/embed",
                json={"model": model, "input": text},
            )
            response.raise_for_status()
            payload = response.json()
            if "embeddings" in payload and payload["embeddings"]:
                return payload["embeddings"][0]
            if "embedding" in payload:
                return payload["embedding"]
            raise ValueError("Unexpected Ollama embedding response format")

---------------------------------------------------------------------------------------------------------------------
              functionName: MCP tool /get_file_text_by_path
              parameters: {"pathInProject": "src/app/clients/qdrant_client.py"}
              content: from __future__ import annotations

from qdrant_client import AsyncQdrantClient
from qdrant_client.http import models as qdrant_models

from app.domain.models import RetrievedChunk


_VECTOR_SIZE_CACHE: dict[str, int] = {}


class QdrantVectorStore:
    def __init__(self, url: str, collection_name: str, api_key: str | None = None) -> None:
        self._client = AsyncQdrantClient(url=url, api_key=api_key)
        self._collection_name = collection_name

    async def ensure_collection(self, vector_size: int) -> None:
        """Create the collection if it does not already exist."""
        existing = await self._client.get_collections()
        names = {c.name for c in existing.collections}
        if self._collection_name not in names:
            await self._client.create_collection(
                collection_name=self._collection_name,
                vectors_config=qdrant_models.VectorParams(
                    size=vector_size,
                    distance=qdrant_models.Distance.COSINE,
                ),
            )

    async def upsert(self, chunks: list[dict]) -> None:
        """
        Insert or update chunks in the collection.

        Each dict must contain:
          - chunk_id (str)
          - vector (list[float])
          - payload (dict) with provenance metadata
        """
        points = [
            qdrant_models.PointStruct(
                id=_chunk_id_to_int(item["chunk_id"]),
                vector=item["vector"],
                payload={**item["payload"], "chunk_id": item["chunk_id"]},
            )
            for item in chunks
        ]
        await self._client.upsert(collection_name=self._collection_name, points=points)

    async def search(self, query_vector: list[float], limit: int = 5) -> list[RetrievedChunk]:
        """Return the top-k most similar chunks for a query embedding."""
        results = await self._client.search(
            collection_name=self._collection_name,
            query_vector=query_vector,
            limit=limit,
            with_payload=True,
        )
        chunks = []
        for hit in results:
            p = hit.payload or {}
            chunks.append(
                RetrievedChunk(
                    chunk_id=p.get("chunk_id", str(hit.id)),
                    doc_id=p.get("doc_id", ""),
                    source_path=p.get("source_path", ""),
                    text=p.get("text", ""),
                    score=hit.score,
                    title=p.get("title"),
                    page=p.get("page"),
                    section=p.get("section"),
                )
            )
        return chunks

    async def health_check(self) -> bool:
        """Return True if Qdrant is reachable."""
        try:
            await self._client.get_collections()
            return True
        except Exception:
            return False


def _chunk_id_to_int(chunk_id: str) -> int:
    """Convert a hex chunk ID (sha256 prefix) to an integer Qdrant point ID."""
    # Use the first 16 hex chars of the chunk_id as an unsigned 64-bit integer
    hex_part = chunk_id.replace("-", "")[:16]
    return int(hex_part, 16)

---------------------------------------------------------------------------------------------------------------------
              functionName: MCP tool /get_file_text_by_path
              parameters: {"pathInProject": "Dockerfile"}
              content: FROM python:3.12-slim

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy dependency files
COPY pyproject.toml .
COPY README.md .

# Install dependencies (no dev extras)
RUN uv sync --no-dev

# Copy application source
COPY src/ src/

ENV PYTHONPATH=/app/src
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--app-dir", "src"]

---------------------------------------------------------------------------------------------------------------------
              functionName: MCP tool /get_file_text_by_path
              parameters: {"pathInProject": "pyproject.toml"}
              content: [project]
name = "rag-dev-plane"
version = "0.1.0"
description = "Developer-facing RAG backend with FastAPI, Qdrant, and OpenAI-compatible providers"
readme = "README.md"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.30.0",
    "pydantic>=2.7.0",
    "pydantic-settings>=2.3.0",
    "httpx>=0.27.0",
    "qdrant-client>=1.9.0",
    "langchain-text-splitters>=0.2.0",
    "python-multipart>=0.0.9",
    "pypdf>=4.2.0",
    "beautifulsoup4>=4.12.0",
    "lxml>=5.2.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.2.0",
    "pytest-asyncio>=0.23.0",
    "pytest-httpx>=0.30.0",
    "httpx>=0.27.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/app"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
pythonpath = ["src"]

[tool.uv]
package = false

[dependency-groups]
dev = [
    "httpx>=0.28.1",
    "pytest>=9.0.3",
    "pytest-asyncio>=1.3.0",
    "pytest-httpx>=0.36.2",
]

---------------------------------------------------------------------------------------------------------------------


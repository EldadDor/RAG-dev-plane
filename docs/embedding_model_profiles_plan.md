# Embedding Model Profiles and Embedding Cache — Review Proposal

**Status:** Proposed for review; not approved for implementation
**Prepared:** 2026-09-11
**Proposed phase:** NP-17
**Supports:** NP-16 (Hebrew and multilingual RAG evaluation)

## Motivation

NP-16 requires comparing embedding models that produce different vector
dimensions (`nomic-embed-text` at 768, `bge-m3` at 1024, Azure
`text-embedding-3-large` at 3072 or a Matryoshka-truncated dimension). Today
one dimension is fixed per database through `PG_VECTOR_DIM` and validated
against the single embeddings column in `rag.document_chunks`. Comparing
models therefore means recreating storage and re-embedding every chunk every
time, which is slow, destructive, and blocks the NP-16 benchmark cycle.

This proposal adds two capabilities:

1. **Model profiles** — named, registry-backed embedding configurations with
   their own validated storage, so models coexist.
2. **Embedding cache** — a persistent, model-aware embedding cache so that
   re-ingestion and model switch-back do not call the provider again.

Together they make switching embedding models a configuration change, not a
data operation.

## Current Constraints

- `PG_VECTOR_DIM` is validated once at startup against the single
  `embedding vector(N)` column; all profiles share the same dimension.
- NP-08 `chunking_profile` scopes chunking only; every profile still embeds
  with the globally configured model into one table.
- Chunked text and embeddings are recomputed per profile ingestion; there is
  no reuse across models.
- PostgreSQL objects are owned by versioned SQL under `database/migrations`;
  the application validates schema at startup and must never create or alter
  database objects.
- Qdrant remains a supported alternative for the local/no-database path.

## Design Principles

- Chunking and embedding are separable configuration axes. A model profile
  selects an embedding model, dimension, and any required prompt prefixes;
  the NP-08 chunking profile still selects chunking strategy.
- Existing indexed data must not be touched. The current table and the
  configured default embedding model keep working with zero migration impact.
- Switching back to a previously used model must be instant.
- All new behavior is reach-through adapters and configuration; the offline
  test suite must not require models, downloads, or a database.

## Proposed Data Model

### Model profile registry: `rag.model_profiles`

Created by a versioned migration (`005_model_profiles.sql`).

| Column | Purpose |
| --- | --- |
| `profile_name` (PK) | Stable identifier, e.g. `default`, `bge-m3` |
| `provider` | `ollama`, `azure_openai`, future providers |
| `model` | Provider model name |
| `dimensions` | Expected vector size for this model |
| `query_prefix` / `document_prefix` | Text prefixes required by the model (for example E5 `query:`/`passage:`, Nomic v2 `search_query:`/`search_document:`, empty for current defaults) |
| `storage_target` | Provisioned PostgreSQL table name or Qdrant collection name |
| `status` | `draft`, `warming`, `ready`, `archived` |
| `created_at` / `updated_at` | Audit lifecycle |

The migration seeds one row mapping the current configuration
(`default`, current `EMBEDDING_MODEL`, current `PG_VECTOR_DIM`) to the
existing `rag.document_chunks` table. This preserves day-one behavior.

### Embedding cache: `rag.embedding_cache`

Created by the same migration.

| Column | Purpose |
| --- | --- |
| `cache_key` (PK) | SHA-256 of provider, model, normalized text, and target dimension |
| `provider`, `model` | Model identity for inspection and future eviction |
| `dimensions` | Vector size recorded for validation |
| `embedding` (`bytea`) | Little-endian float32 payload; not a typed vector column, so any dimension fits |
| `hit_count`, `created_at`, `last_hit_at` | Usage signal for a future, separately approved eviction policy |

The cache stores bytes, not `vector(N)`, because it must serve any dimension.
Only profile tables hold typed vectors for ANN indexing.

### Per-model chunk storage

Each model profile gets its own storage that mirrors the current
`document_chunks` shape:

- PostgreSQL: a provisioned table per profile, e.g.
  `rag.document_chunks_bge_m3`, holding `embedding vector(1024)` with its own
  HNSW and lexical indexes.
- Qdrant: a collection per profile, e.g. `developer_docs_bge_m3`.

PostgreSQL tables are **provisioned**, not created by the application:

- New reusable provisioning script
  `database/migrations/model_profile_table.sql` accepts
  `-v profile_name=... -v dim=...` and creates the table and indexes for one
  profile.
- The application's store validates that the selected profile's target exists
  and its embedding column matches the profile's registered dimension, and
  fails with provisioning guidance otherwise — exactly the pattern used by
  `ensure_collection` today.

This keeps the invariant that migrations and provisioning scripts own all DDL.

## Request Flow Changes

### Ingestion

1. Resolve `model_profile` (new optional field) and `chunking_profile`
   (existing); both default to current behavior when omitted.
2. Chunk with the existing NP-08 chunking-profile adapters — unchanged.
3. Embed one layer down through a caching decorator:
   - Batch chunks; apply the profile's `document_prefix`.
   - Read-through cache lookup per chunk; provider is called only for misses.
   - Write-through cache insert for every provider result.
4. Write chunk rows into the model profile's storage target, keyed by the
   existing workspace/chunking-profile/document identity.

Chunking and text are identical for a given chunking profile regardless of
model, so chunk IDs stay deterministic across model profiles.

### Retrieval and chat

1. Resolve the requested `model_profile` (new optional field on
   `/chat` and `/chat/stream`, plus retrieval callers).
2. Embed the query with the profile model and its `query_prefix`.
3. Search the profile's storage target (semantic plus lexical for PostgreSQL,
   RRF fusion unchanged), then apply the NP-10 opt-in rerank stage.

Requests without a model profile resolve to the seeded `default` profile and
behave exactly as today.

### Model warming (the fast-switch job)

`POST /admin/model-profiles/{profile_name}/warm`:

- Reads chunk rows from a source profile (default: the current default).
- Embeds them into the target profile using the cache (hits are free).
- Writes rows to the target storage; marks the profile `warming` → `ready`.
- Supports `dry_run=true` reporting chunk counts, cache hit rate, and
  estimated provider calls without writes.
- Idempotent and workspace-scoped; re-running embeds only new or changed
  chunks (existing content-hash lifecycle still governs source changes).

After warming once, `MODEL_PROFILE=<name>` switches models with zero provider
calls. A/B runs follow the NP-10 pattern: same parsed data, two profiles,
compared through the NP-09 runner on the Hebrew golden set.

## Configuration

Extend typed settings; defaults preserve today's behavior:

```dotenv
# Active model profile; omitted = resolved registry default (current model)
MODEL_PROFILE=
# Registry/cache behavior
EMBEDDING_CACHE_ENABLED=true
EMBEDDING_CACHE_MAX_AGE_DAYS=0    # 0 = no eviction; eviction needs approval
```

`.env.example` documents registered profiles with their dimensional and
prefix requirements. Qdrant deployments get an in-memory or Qdrant-payload
cache implementation behind the same `EmbeddingCache` protocol so the
no-database path keeps working.

## Task Breakdown

| ID | Task |
| --- | --- |
| NP17-01 | Add migration `005_model_profiles.sql` (registry + cache) with rollback instructions, and the profile-table provisioning script. |
| NP17-02 | Add `ModelProfileStore` and `EmbeddingCache` protocols with PostgreSQL and fallback implementations; seed default profile to current table. |
| NP17-03 | Add `CachedEmbeddingClient` decorator with prefix handling per provider/model. |
| NP17-04 | Route ingestion and retrieval through model-profile resolution; keep unspecified-request behavior byte-compatible. |
| NP17-05 | Implement the `warm` operation with dry-run; add focused unit/API tests including dimension-mismatch failures. |
| NP17-06 | Live validation: provision a second profile for a Hebrew-capable model, warm it, and run the NP-09 harness against both profiles; record artifacts. |

## Acceptance Checks

- Omitted-`model_profile` ingestion, retrieval, and chat are behaviorally
  identical to pre-change behavior against the existing table.
- Two model profiles with different dimensions coexist; each validates its
  own storage at startup.
- Cache lookups make a second identical ingestion make zero provider calls.
- Switching back to a warmed profile requires no embedding calls.
- Dimension mismatches between registry, storage column, and provider output
  fail fast with actionable guidance.
- Providers requiring prefixes produce distinct cache entries from the same
  text under different models.

## Approval Gates

- Approve the new `rag.*` tables and the provisioning script before
  implementation (schema change gate).
- Approve the `MODEL_PROFILE` API fields before the frontend contract is
  updated; no frontend change is required for the first iteration.
- Approve any cache eviction/backfill policy separately; the first release
  never deletes cached embeddings.
- Approve each concrete non-default model (and any model downloads) before
  live warming runs, consistent with NP-16 activation rules.

## Out of Scope

- ColPali-style multi-vector or late-interaction retrieval.
- Unified multimodal embeddings for images (future NP-18 candidate after
  NP-13–15 live validation).
- Cache eviction, quota, and retention policies beyond counting.
- Cross-model federated search in a single request.

## Rollback

Nothing in this proposal modifies an existing table, row, index, or request
path. Rolling back means not selecting a non-default model profile; the
registry and cache tables are additive and inert when unused.

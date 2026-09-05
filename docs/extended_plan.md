# Extended Application Plan — Frontend and Backend

**Status:** Approved roadmap. NP-08 is the active phase.
**Prepared:** 2026-09-04
**Basis:** All documentation under `docs/` (excluding `phase_qa/`), the phase
history through NP-05, the FP-01 frontend phase records, and the current
repository state.

This document extends the project plan for the entire application. It registers
the quality and delivery phases that follow the completed NP-01 through NP-05
backend phases. Each phase still requires its own activation review through
`next_phase.md` before implementation, except NP-08, which is approved active.

## Current State

### Backend — NP-01 through NP-05 complete

| Area | State |
| --- | --- |
| Core RAG foundation | FastAPI service with separate chat and embedding adapters, grounded answers with structured sources, explicit abstention. |
| Retrieval | PostgreSQL hybrid semantic + lexical search with reciprocal-rank fusion, minimum-score filtering, Qdrant alternative. |
| Ingestion | Structure-aware loaders (Markdown, HTML, text, PDF), Python AST and Java/Kotlin Tree-sitter chunking, workspace-scoped content-hash source lifecycle. |
| Persistence | PostgreSQL + pgvector default (`rag` schema, versioned migrations), durable conversation memory, workspace membership authorization. |
| Workspace authorization | `GET /workspaces`, PostgreSQL membership, gateway/local principals, centralized enforcement, safe `{ code, message }` error envelope. |
| Observability | Optional Langfuse root tracing, disabled by default. |

### Frontend — FP-01 in flight

FP-01 through FP-06 are implemented: app shell, workspace discovery, sessions,
bounded history, rename/archive, and named-event SSE streaming with Stop and
recovery states. FP-07 (type check, tests, production build) completed
2026-09-04 in `1ba58c08`. The remaining work is the operator-run live
integration checklist in `frontend/integration_test_plan.md` and phase closure.

### Known gaps

- Reranking is configuration-visible (`RERANK_ENABLED`) but is not an active
  retrieval stage.
- The application has only been run and validated on local machines.
- Ingestion and chat have been exercised mainly through AI-agent flows on
  simple documents.
- Chunking is a single global `CHUNK_SIZE`/`CHUNK_OVERLAP` setting, and
  re-ingestion replaces existing chunks per `(workspace_id, doc_id)`.

## Approved Goals Driving the New Phases

1. Chat answers must become shorter and more concise. Chunking changes may be
   required and must be investigated before prompt-only fixes.
2. Chunking must be easy to change and test while preserving the existing
   indexed data in pgvector.

Both goals are retrieval-quality problems. Answer verbosity is driven first by
the volume and precision of retrieved context, and only then by prompt wording.

## New Phases

### NP-07 — Answer Conciseness and Groundedness Tuning (Queued after NP-08 and NP-09)

**Objective:** Shorter, tighter answers without losing grounding or the
abstention behavior.

**Scope:**

- Assemble context against a configurable token budget instead of a bare
  `TOP_K`: pack the most relevant chunks up to roughly 60% of the budget, cap
  the chunk count, and drop near-duplicate chunks before packing.
- Add a dedupe/boilerplate filter in retrieval (navigation, footers, repeated
  text).
- Tighten the system prompt with an explicit brevity and target-length
  instruction while preserving the abstention rule.
- Keep provider and memory boundaries unchanged.

**Acceptance:** On the NP-09 golden set, mean answer length decreases with
equal-or-better faithfulness and no regression in grounded-answer rate.

### NP-08 — Non-Destructive Chunking Experimentation Lab (Active)

**Objective:** Change, ingest, and test chunking strategies side by side
without overwriting the existing indexed chunks in pgvector.

**Scope:**

- Add a `chunking_profile` dimension to chunk and source-document records
  through a versioned migration (`003_chunking_profiles.sql`). The default
  profile preserves current behavior, so existing rows remain valid.
- Extend `POST /ingest` with `chunking_profile` and a `dry_run` mode that
  reports chunk statistics without replacing indexed data.
- Register alternative chunking strategies behind the existing chunker
  boundary: recursive-character with profile-defined size/overlap, and an
  optional semantic splitter for comparison.
- Allow retrieval and chat to filter by `chunking_profile` so an experiment
  can be queried in isolation.

**Data preservation:** experiments live under a distinct profile; the default
profile's rows are never replaced by an experiment. Promotion means re-pointing
the workspace to the winning profile.

**Acceptance:**

- Re-ingesting the same sources under an experiment profile leaves the default
  profile's rows unchanged.
- A workspace-scoped query filtered to an experiment profile returns only that
  profile's chunks.
- Ingestion, retrieval, and chat are unchanged when no profile is specified.

### NP-09 — Golden Evaluation Set and Regression Harness (Queued)

**Objective:** Make "is it better?" measurable and repeatable.

**Scope:**

- A structured golden dataset (JSONL) of real developer questions with expected
  facts and optional expected source hints, following
  `.github/instructions/evaluation.instructions.md`.
- A pytest-compatible smoke lane plus a richer local benchmark runner reporting
  context precision/recall, faithfulness, answer relevance, latency, and
  failure source (ingestion, retrieval, rerank, prompt, generation).
- RAGAS or DeepEval behind the existing adapter boundary.
- Record each run's configuration (profile, chunk size/overlap, top_k, models)
  alongside results so runs are comparable.
- A retrieval determinism check before any metric comparison.

**Acceptance:** The eval suite runs offline with mocks; a live mode runs
against the local stack and writes a comparable result artifact.

### NP-10 — Activate Retrieval Reranking (Queued after NP-09)

**Objective:** Lift context precision so answers can get tighter.

**Scope:**

- Turn `RERANK_ENABLED` into a real stage: cross-encoder reranking over the
  fused semantic/lexical candidate set, behind the existing adapter pattern.
- Retrieve wider (for example top 12-20), rerank, keep the top 3-5 for the
  prompt.
- Offer a local reranker option to keep the on-premises path working.

**Acceptance:** Context precision improves over baseline on the NP-09 golden
set at equal or better recall; answer length drops as a side effect.

### NP-11 — Frontend Live Validation and Phase Closure (Queued)

**Objective:** Finish the FP-01 frontend phase.

**Scope:** Run the operator checklist in `frontend/integration_test_plan.md`
against the live stack (LLM, pgvector, embedding service), record evidence and
any contract discrepancies in the agent handoff, then close FP-01.

### NP-12 — Azure / Office Deployment (Queued after NP-08 and NP-09)

**Objective:** Move from local-only validation to a deployable service.

**Scope:** Execute `AZURE_DEPLOYMENT_PLAN.md` — Azure OpenAI or gateway-fronted
local models, Azure Database for PostgreSQL with pgvector, Container Apps or
App Service, Managed Identity, Nginx identity-header injection, TLS and CORS.
Re-ingestion is required if the embedding model or dimension changes; validate
quality before and after migration with the NP-09 golden set.

## Existing NP-06

NP-06 (CI test lanes) remains queued as previously registered. Once NP-09
exists, the required CI lane should include the evaluation smoke check.

## Dependency Order

```
NP-09 (golden set) --> NP-07 (conciseness)
NP-08 (chunk lab)  --> NP-07
NP-09              --> NP-10 (reranker)
NP-11 (frontend closure)   [parallel]
NP-06 (CI lanes)           [parallel]
NP-12 (deployment)         [after NP-08 and NP-09]
```

NP-08 starts first because it makes every later chunking or retrieval change
safe and reversible, and it directly satisfies the data-preservation
requirement.

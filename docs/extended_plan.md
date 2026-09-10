# Extended Application Plan — Frontend and Backend

**Status:** Approved roadmap. NP-08 through NP-10 are complete; NP-10 reranking remains opt-in.
**Prepared:** 2026-09-04
**Basis:** All documentation under `docs/` (excluding `phase_qa/`), the phase
history through NP-05, the FP-01 frontend phase records, and the current
repository state.

This document extends the project plan for the entire application. It registers
the quality and delivery phases that follow the completed NP-01 through NP-05
backend phases. Each phase still requires its own activation review through
`next_phase.md` before implementation, except NP-08, which is approved active.

## Current State

**Update 2026-09-10:** NP-08 through NP-10 are complete. NP-09 provides the
19-case default-profile baseline and NP-10 retains reranking as opt-in.
Frontend FP-01 and FP-02 are complete. NP-13 through NP-15 are proposed for
Word ingestion and cited-image display; they are not approved.

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

- Cross-encoder reranking is implemented behind `RERANK_ENABLED` and remains
  off by default: the 2026-09-10 live A/B run improved answer metrics slightly
  but had saturated context precision/recall and added 50.0% mean latency.
- The application has only been run and validated on local machines.
- Ingestion and chat have been exercised mainly through AI-agent flows on
  simple documents.
- Chunking is a single global `CHUNK_SIZE`/`CHUNK_OVERLAP` setting, and
  re-ingestion replaces existing chunks per `(workspace_id, doc_id)`.
- `.docx` is not supported, embedded document images have no managed lifecycle,
  and citations cannot currently deliver or display source images.

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

### NP-08 — Non-Destructive Chunking Experimentation Lab (Complete)

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

### NP-09 — Golden Evaluation Set and Regression Harness (Complete)

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

### NP-10 — Activate Retrieval Reranking (Complete)

**Objective:** Lift context precision so answers can get tighter.

**Scope:**

- Turn `RERANK_ENABLED` into a real stage: cross-encoder reranking over the
  fused semantic/lexical candidate set, behind the existing adapter pattern.
- Retrieve wider (for example top 12-20), rerank, keep the top 3-5 for the
  prompt.
- Offer a local reranker option to keep the on-premises path working.

**Completion decision:** The 2026-09-10 live A/B run was deterministic and
reranked every case, but context precision/recall were already saturated at
1.0. The small answer-quality gains did not offset 50.0% mean latency, so the
feature remains opt-in rather than enabled by default. Evidence is recorded in
`docs/work_current_phase.md` and `evaluation/results/np10-*.json`.

### NP-11 — Frontend Live Validation and Phase Closure (Queued)

**Status:** Complete 2026-09-05. FP-01 closure and live streaming validation
are recorded by the frontend phase records; FP-02 subsequently completed its
approved hardening scope.

**Completion evidence:** The frontend records successful operator-run live
streaming validation, no API-contract discrepancy, and formal FP-01 closure.

### NP-12 — Azure / Office Deployment (Queued after NP-08 and NP-09)

**Objective:** Move from local-only validation to a deployable service.

**Scope:** Execute `AZURE_DEPLOYMENT_PLAN.md` — Azure OpenAI or gateway-fronted
local models, Azure Database for PostgreSQL with pgvector, Container Apps or
App Service, Managed Identity, Nginx identity-header injection, TLS and CORS.
Re-ingestion is required if the embedding model or dimension changes; validate
quality before and after migration with the NP-09 golden set.

### NP-13 — Structured Microsoft Word Ingestion (Proposed)

**Objective:** Add safe, deterministic `.docx` ingestion for ordered text,
headings, lists and tables while retaining stable anchors for embedded media.

**Boundary:** Support modern OOXML `.docx`; do not automate desktop Word or
parse legacy binary `.doc`. Existing loaders and embeddings remain unchanged.

### NP-14 — Embedded Image Asset Lifecycle (Proposed after NP-13)

**Objective:** Extract original embedded image bytes, store them behind a local
and future object-storage adapter, and associate them with the relevant text
chunks under workspace/profile/document ownership.

**Boundary:** Store image metadata and associations in PostgreSQL, binary bytes
outside the vector table, and perform no OCR or visual embedding.

### NP-15 — Authorized Image Citations and Chat Display (Proposed after NP-14)

**Objective:** Extend structured citations with related asset metadata, serve
images through a workspace-authorized endpoint, and render lazy image previews
in the frontend Sources experience.

**Boundary:** The application—not the answer model—creates image URLs and
controls rendering. Existing text-only citation payloads remain compatible.

**Detailed review:** [`document_image_support_plan.md`](document_image_support_plan.md)

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
NP-13 (Word text)          --> NP-14 (image lifecycle)
NP-14 (image lifecycle)    --> NP-15 (authorized chat display)
NP-15                      --> optional OCR/multimodal phase [separate approval]
```

NP-08 starts first because it makes every later chunking or retrieval change
safe and reversible, and it directly satisfies the data-preservation
requirement.

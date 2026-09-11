# Next Phase — Approval Backlog

**Status:** NP-13 through NP-15 are active; implementation is complete and live environment validation is pending.
**Last reviewed:** 2026-09-11

This is the ordered backlog for the next approved phase. Each item must have a
defined scope, acceptance checks, and an approval decision before implementation.

## Candidate Work

| Priority | ID | Candidate task | Why it matters | Approval required |
| --- | --- | --- | --- | --- |
| 1 | NP-01 | Refresh architecture documentation | Complete in `df37f9b`. | Completed 2026-08-20 |
| 2 | NP-02 | Decide the Qdrant warning policy | Complete: production check retained; mocked tests disable the probe. | Completed 2026-08-20 |
| 3 | NP-03 | Parser-aware Kotlin chunking | Complete: Tree-sitter symbols, line ranges, fallback behavior, and unit validation. | Completed 2026-08-21 |
| 4 | NP-04 | Add operational observability | Foundation complete: optional safe root tracing. Nested RAG spans are deferred. | Completed 2026-08-21 |
| 5 | NP-05 | Workspace discovery and authorization | PostgreSQL-backed authorization, canonical frontend contract, migrations/local seed, live API validation, and documentation indexing complete. | Completed 2026-08-29 |
| 6 | NP-06 | Define CI test lanes | Moved from NP-05. Separate required unit/API CI from a manual environment-specific live lane. | Queued after NP-05 |
| 7 | NP-07 | Answer conciseness and groundedness tuning | Answer verbosity is driven by context volume and precision before prompt wording; tune retrieval-side context assembly first. | Queued after NP-08 and NP-09 |
| 8 | NP-08 | Non-destructive chunking experimentation lab | Profile-scoped indexing, dry runs, and isolated retrieval are implemented and live-validated. | Completed 2026-09-07 |
| 9 | NP-09 | Golden evaluation set and regression harness | 19-case default-profile baseline, offline smoke lane, and local artifact runner are complete. | Completed 2026-09-09 |
| 10 | NP-10 | Activate retrieval reranking | Optional local cross-encoder reranking is active behind configuration; default enablement was evaluated but declined because the benchmark's precision/recall was saturated and reranking added 50.0% mean latency. | **Complete — default remains off.** 2026-09-10 |
| 11 | NP-11 | Frontend live validation and phase closure | FP-01 closure and live streaming validation are recorded by the frontend phase records. | Completed 2026-09-05 |
| 12 | NP-12 | Azure and office deployment | Execute `AZURE_DEPLOYMENT_PLAN.md` once quality tooling exists. | Queued after NP-08 and NP-09 |
| 13 | NP-13 | Structured Microsoft Word ingestion | Safe `.docx` structure extraction, image anchors and image-aware hashing implemented. | **Implementation complete; live validation pending** |
| 14 | NP-14 | Embedded image asset lifecycle | Content-addressed asset storage, migration 004 and profile-scoped chunk associations implemented. | **Implementation and migration complete** |
| 15 | NP-15 | Authorized image citations and chat display | Authorized asset route, compatible citation metadata and accessible previews implemented. | **Implementation complete; live browser validation pending** |
| 16 | NP-16 | Hebrew and multilingual RAG evaluation | Work documents are largely Hebrew; local models (`nomic-embed-text`, `llama3.2:3b`) are English-centric, and Hebrew failures are retrieval-side before generation-side. | **Proposed after NP-13–15 live validation — activation required** |
| 17 | NP-17 | Embedding model profiles and embedding cache | Comparing embedding models needs per-model dimensions, isolated storage, and cached embeddings so a model switch is configuration-only; NP-16 benchmarks depend on this plumbing. | **Proposed — enables NP-16; activation required** |

## Current Phase State

### NP-13 through NP-15 — Word and Embedded Images (Active)

**Objective:** Ingest modern Word documents as structured text and show their
embedded screenshots with grounded citations, without requiring OCR or visual
embeddings in the first release.

**Scope:**

- Structured `.docx` parsing with headings, lists, tables, page-break hints and
  stable image anchors.
- Private content-addressed asset persistence and profile/workspace-scoped
  chunk associations.
- Authorized image delivery and accessible frontend previews under citations.

**Review document:** [`document_image_support_plan.md`](document_image_support_plan.md)

The user approved these phases on 2026-09-11. Offline implementation validation
passes; migration and live end-to-end validation wait for the configured
PostgreSQL host to become reachable.

### NP-16 — Hebrew and Multilingual RAG Evaluation (Proposed)

**Objective:** Measure and close the Hebrew quality gap with comparable
evaluation evidence before any model swap, while preserving the local-first
operating path.

**Proposed scope:**

- Extend the NP-09 golden set with human-verified Hebrew cases from real
  documents; expected facts and source hints remain human-authored.
- Benchmark the embedding side first on the Hebrew set: `nomic-embed-text`
  (current) versus at least one local multilingual candidate (for example
  `bge-m3`, noting its 1024-dimension change requires `PG_VECTOR_DIM` and
  re-ingestion; chunking profiles do not isolate embedding dimensions).
- A/B chat models that fit the desktop's 8 GB GPU (DictaLM 3.0 12B,
  Gemma 3 12B/4B, Qwen3 8B) using the NP-09 runner; keep configuration-only
  model changes and record latency alongside quality.
- Extend PostgreSQL lexical retrieval for Hebrew morphology (attached prefixes)
  if the golden set shows lexical misses.
- Produce a repeatable local-versus-Azure comparison artifact so the eventual
  Azure OpenAI deployment (`text-embedding-3-large`, GPT-5) can be evaluated
  against the same Hebrew cases.

**Constraints:**

- No model swap or embedding-dimension migration without a benchmark report
  showing a retrieval-quality improvement on the Hebrew golden cases.
- Keep the default local configuration working without cloud calls.

**Activation note:** Queued after NP-13–15 live validation and NP-06 CI lanes.
Requires explicit activation approval and, for dimension changes, a separate
migration approval. NP-17 provides the model-profile plumbing that makes these
benchmarks repeatable.

### NP-17 — Embedding Model Profiles and Embedding Cache (Proposed)

**Objective:** Make embedding models with different dimensions and prompt
prefixes switchable without re-chunking, re-parsing, or discarding existing
embeddings.

**Proposed scope:**

- Registry-backed model profiles (provider, model, dimensions, prefixes,
  storage target) with the current configuration seeded as `default`.
- Per-model chunk storage provisioned through SQL and validated at startup;
  the existing default index is untouched.
- A persistent embedding cache keyed by text and model identity so repeat
  ingestion or model switch-back avoids provider calls.
- A warming operation that embeds an existing profile's chunks into a new
  model profile without re-chunking, with a dry-run mode.
- Configuration-only activation of a warmed profile; retrieval stays scoped
  through the existing chunking-profile and model-profile boundaries.

**Review document:**
[`embedding_model_profiles_plan.md`](embedding_model_profiles_plan.md)

**Activation note:** Enables NP-16's embedding-model benchmarks and the
Azure embedding migration. Requires approval of the new `rag.*` registry and
cache tables plus per-profile storage provisioning before implementation.

## Phase Intake Checklist

Before a candidate becomes active, record:

- [ ] A clear objective and bounded scope.
- [ ] Explicit exclusions.
- [ ] Affected code, configuration, docs, and tests.
- [ ] Local and live validation requirements.
- [ ] Data/model/database impact and rollback plan, if applicable.
- [ ] Required user approvals or credentials.
- [ ] Completion criteria and a planned commit boundary.

## Deferred / Out of Scope Until Approved

- Provider changes or model swaps.
- Unapproved pgvector schema changes beyond the versioned baseline and the NP-05/NP-08 migrations.
- Making live model/database tests mandatory in CI.
- Production deployment changes.
- Replacing the dual chat/embedding provider architecture.

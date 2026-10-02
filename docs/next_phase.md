# Next Phase — Approval Backlog

**Status:** NP-20 implementation is complete and offline-validated; local migration/backfill/live rollout remains pending.
**Last reviewed:** 2026-10-02

This is the ordered backlog for the next approved phase. Each item must have a
defined scope, acceptance checks, and an approval decision before implementation.

## Candidate Work

| Priority | ID | Candidate task | Why it matters | Approval required |
| --- | --- | --- | --- | --- |
| 1 | NP-01 | Refresh architecture documentation | Complete in `df37f9b`. | Completed 2026-08-20 |
| 2 | NP-02 | Decide the Qdrant warning policy | Complete: production check retained; mocked tests disable the probe. | Completed 2026-08-20 |
| 3 | NP-03 | Parser-aware Kotlin chunking | Complete: Tree-sitter symbols, line ranges, fallback behavior, and unit validation. | Completed 2026-08-21 |
| 4 | NP-04 | Add operational observability | Foundation complete: optional safe root tracing. Nested RAG spans are deferred. | Completed 2026-08-21 |
| 5 | NP-05 | Workspace discovery and authorization | PostgreSQL-backed authorization, frontend contract, migrations/local seed, live API validation, and documentation indexing complete. | Completed 2026-08-29 |
| 6 | NP-06 | Define CI test lanes | Separate required unit/API CI from a manual environment-specific live lane. | Queued |
| 7 | NP-07 | Answer conciseness and groundedness tuning | Tune retrieval-side context assembly before prompt wording. | Queued after NP-08 and NP-09 |
| 8 | NP-08 | Non-destructive chunking experimentation lab | Profile-scoped indexing, dry runs, and isolated retrieval are implemented and live-validated. | Completed 2026-09-07 |
| 9 | NP-09 | Golden evaluation set and regression harness | Default-profile baseline, offline smoke lane, and local artifact runner are complete. | Completed 2026-09-09 |
| 10 | NP-10 | Activate retrieval reranking | Optional cross-encoder reranking was evaluated; default remains off because precision/recall was saturated and mean latency rose 50%. | Complete 2026-09-10 |
| 11 | NP-11 | Frontend live validation and phase closure | FP-01 closure and live streaming validation are recorded by the frontend phase records. | Completed 2026-09-05 |
| 12 | NP-12 | Azure and office deployment | Execute `AZURE_DEPLOYMENT_PLAN.md` after quality tooling and deployment scope are approved. | Queued |
| 13 | NP-13 | Structured Microsoft Word ingestion | Safe `.docx` structure extraction, image anchors, and image-aware hashing implemented. | Complete — live validated 2026-09-12 |
| 14 | NP-14 | Embedded image asset lifecycle | Content-addressed asset storage, migration 004, and profile-scoped chunk associations implemented. | Complete |
| 15 | NP-15 | Authorized image citations and chat display | Authorized asset route, compatible citation metadata, and accessible previews implemented. | Complete — live browser validated 2026-09-12 |
| 16 | NP-16 | Hebrew and multilingual RAG evaluation | Hebrew golden-set evaluation established bge-m3 retrieval and DictaLM chat as the recommended local pairing. | Complete — closed 2026-09-13 |
| 17 | NP-17 | Embedding model profiles and embedding cache | Registry-backed isolated profile storage, cache, selection plumbing, and local-only dry-run warming are implemented. | Complete — closed 2026-09-13 |
| 18 | NP-18 | Spring Boot backend handoff | Current backend API/behavior and Kotlin Spring AI 2.0 migration design, retaining the frontend contract. | Complete — closed 2026-09-17 |
| 19 | NP-19 | Recent document metadata API design | Full proposed contract and publication/lifecycle implementation plan in recent_document_metadata_api_design.md. | Design complete 2026-10-02. |
| 20 | NP-20 | Implement recent document metadata API | Catalog storage, lifecycle integration, authorized listing, reconciliation tooling and frontend contract implemented. | 132 offline tests passed 2026-10-02; migration/backfill/enablement and live acceptance pending in NP20-LIVE. |

## Latest Completed-Phase Record

### NP-20 — Implementation checkpoint (live phase closure pending)

Implemented 2026-10-02 with 132 passing offline tests. The source contract is
documented in `frontend_architecture.md`; migration 006 and reviewed catalog
reconciliation must precede enablement. See `../database/README.md` for rollout
commands. NP20-LIVE remains in the current task board until separate live
authorization and evidence are recorded; frontend integration stays pending.

### NP-19 — Recent Document Metadata API Design

Completed 2026-10-02. See
[`recent_document_metadata_api_design.md`](recent_document_metadata_api_design.md)
for the proposed GET route, profile-specific counts/times, revision-checked
pagination, lifecycle corrections, safe errors, migration/backfill/rollback,
frontend acceptance, and NP20-01 through NP20-05 implementation tasks.
The proposal is not an implemented browser contract. NP-20 implementation and
migration execution remain subject to their recorded approval scope.

### NP-13 through NP-15 — Word and Embedded Images

Completed and live-validated 2026-09-12: structured Word ingestion, private
content-addressed image persistence, authorized image delivery, and frontend
citation previews. See [`document_image_support_plan.md`](document_image_support_plan.md).

### NP-16 — Hebrew and Multilingual RAG Evaluation

The committed 13-case Hebrew and 19-case English artifacts support bge-m3
retrieval with DictaLM chat for local operation. The default nomic profile is
preserved for rollback and comparison. See
[`work_current_phase.md`](work_current_phase.md).

### NP-17 — Embedding Model Profiles and Embedding Cache

Migration 005, profile/cache adapters, API selection, and the workspace-scoped
local warmer are complete. The warmer remains unavailable in gateway deployments
until a dedicated operator-authorization design is approved. See
[`embedding_model_profiles_plan.md`](embedding_model_profiles_plan.md).

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
- Unapproved pgvector schema changes beyond the versioned baseline and approved migrations.
- Making live model/database tests mandatory in CI.
- Production deployment changes.
- Replacing the dual chat/embedding provider architecture.

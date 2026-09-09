# Next Phase — Approval Backlog

**Status:** NP-10 is complete with reranking retained as opt-in; NP-06 is the next queued backend phase.
**Last reviewed:** 2026-09-10

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

## Current Phase State

### NP-10 — Activate Retrieval Reranking (Complete)

The implementation record, task board, approval gates, and validation plan are
authoritative in [`work_current_phase.md`](work_current_phase.md). The live A/B
comparison was completed on 2026-09-10; reranking remains opt-in because the
baseline's context metrics were saturated and the experiment added 50.0% mean
latency.

## Completed-Phase Reference

### NP-01 — Refresh Architecture Documentation (Complete)

**Proposed objective:** Make `docs/architecture.md` accurately describe the
current RAG request, ingestion, workspace, memory, hybrid retrieval, and
provider flows.

**In scope:** Documentation only; no provider, schema, API, or runtime behavior
changes.

**Acceptance checks:**

- The diagram/text distinguishes chat and embedding adapters.
- Ingestion documents provenance metadata, source lifecycle behavior, and
  workspace boundaries.
- Retrieval documents PostgreSQL hybrid semantic/lexical search and Qdrant as
  an alternative.
- Conversation memory and its separation from document retrieval are stated.
- The document is indexed after approval and completion.

**Completion record:** Approved and completed 2026-08-20 in `df37f9b`.

### NP-03 — Parser-Aware Kotlin Chunking (Complete)

**Completion record:** Tree-sitter parsing, fallback behavior, and focused unit
validation completed 2026-08-21.

### NP-05 — Workspace Discovery and Authorization (Complete)

**Objective:** Resolve the frontend blocker by defining how an authenticated user discovers only their authorized workspaces and how `workspace_id` is enforced for chat and session operations.

**Delivered contract:** PostgreSQL-backed membership, fixed local/gateway office principals, `GET /workspaces`, canonical workspace/session and safe-error payloads, and centralized authorization for chat/session operations.

**Completion record:** Migrations `001_baseline` and
`002_workspace_authorization`, the local seed, live PostgreSQL API validation,
and documentation indexing completed 2026-08-29.

**Tracking:** [`work_current_phase.md`](work_current_phase.md).

### NP-06 — CI Test Lanes (Queued)

**Objective:** Keep unit/API verification required and isolated, while making
live stack verification explicitly manual and environment-scoped.

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

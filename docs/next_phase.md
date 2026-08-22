# Next Phase — Approval Backlog

**Status:** NP-05 is active; NP-06 is queued; all other future work requires explicit approval.
**Last reviewed:** 2026-08-23

This is the ordered backlog for the next approved phase. Each item must have a
defined scope, acceptance checks, and an approval decision before implementation.

## Candidate Work

| Priority | ID | Candidate task | Why it matters | Approval required |
| --- | --- | --- | --- | --- |
| 1 | NP-01 | Refresh architecture documentation | Complete in `df37f9b`. | Completed 2026-08-20 |
| 2 | NP-02 | Decide the Qdrant warning policy | Complete: production check retained; mocked tests disable the probe. | Completed 2026-08-20 |
| 3 | NP-03 | Parser-aware Kotlin chunking | Complete: Tree-sitter symbols, line ranges, fallback behavior, and unit validation. | Completed 2026-08-21 |
| 4 | NP-04 | Add operational observability | Foundation complete: optional safe root tracing. Nested RAG spans are deferred. | Completed 2026-08-21 |
| 5 | NP-05 | Workspace discovery and authorization | **Active.** Define the authorized `workspace_id` source and API required by the frontend selector and history filtering. | Approved 2026-08-23 |
| 6 | NP-06 | Define CI test lanes | Moved from NP-05. Separate required unit/API CI from a manual environment-specific live lane. | Queued after NP-05 |

## Recommended Next Phase

### NP-01 — Refresh Architecture Documentation (Complete)

**Proposed objective:** Make `docs/architecture.md` accurately describe the
current RAG request, ingestion, workspace, hybrid retrieval, memory, and
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

### NP-05 — Workspace Discovery and Authorization (Active)

**Objective:** Resolve the frontend blocker by defining how an authenticated user discovers only their authorized workspaces and how `workspace_id` is enforced for chat and session operations.

**Current blocker:** No workspace discovery/authorization API or approved source of workspace options exists. The frontend must not invent one.

**Tracking:** [`work_current_phase.md`](work_current_phase.md).

### NP-06 — CI Test Lanes (Queued)

**Objective:** Keep unit/API verification required and isolated, while making
live stack verification explicitly manual and environment-scoped.

**Tracking:** See `docs/work_current_phase.md` for required steps and approval
gates.

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
- pgvector schema migrations.
- Making live model/database tests mandatory in CI.
- Production deployment changes.
- Replacing the dual chat/embedding provider architecture.

# Next Phase — Approval Backlog

**Status:** No work starts from this document until explicitly approved.  
**Last reviewed:** 2026-08-20

This is the ordered backlog for the next approved phase. Each item must have a
defined scope, acceptance checks, and an approval decision before implementation.

## Candidate Work

| Priority | ID | Candidate task | Why it matters | Approval required |
| --- | --- | --- | --- | --- |
| 1 | NP-01 | Refresh architecture documentation | `docs/architecture.md` still describes several capabilities that are now implemented, such as real loaders, indexing, and richer chunking. | Yes |
| 2 | NP-02 | Decide the Qdrant warning policy | Keep the production compatibility check, make it configurable, or isolate it from mocked tests. | Yes |
| 3 | NP-03 | Parser-aware Kotlin chunking | Kotlin ingestion currently preserves language/repository metadata but uses generic chunking. | Yes |
| 4 | NP-04 | Add operational observability | Define request correlation, retrieval metrics, provider latency, and safe error diagnostics. | Yes |
| 5 | NP-05 | Define CI test lanes | Add a CI-safe unit lane and retain the live integration test as a manually triggered environment-specific lane. | Yes |

## Recommended Next Phase

### NP-01 — Refresh Architecture Documentation

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

**Decision required:** Approve `NP-01` as the next active phase, defer it, or
select another backlog item.

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

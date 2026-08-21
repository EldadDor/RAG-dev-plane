# Next Phase — Approval Backlog

**Status:** NP-04 foundation complete; all remaining items require explicit approval.
**Last reviewed:** 2026-08-20

This is the ordered backlog for the next approved phase. Each item must have a
defined scope, acceptance checks, and an approval decision before implementation.

## Candidate Work

| Priority | ID | Candidate task | Why it matters | Approval required |
| --- | --- | --- | --- | --- |
| 1 | NP-01 | Refresh architecture documentation | Complete in `df37f9b`. | Completed 2026-08-20 |
| 2 | NP-02 | Decide the Qdrant warning policy | Complete: production check retained; mocked tests disable the probe. | Completed 2026-08-20 |
| 3 | NP-03 | Parser-aware Kotlin chunking | Complete: Tree-sitter symbols, line ranges, fallback behavior, and unit validation. | Completed 2026-08-21 |
| 4 | NP-04 | Add operational observability | Foundation complete: optional safe root tracing. Nested RAG spans are deferred. | Completed 2026-08-21 |
| 5 | NP-05 | Define CI test lanes | Add a CI-safe unit lane and retain the live integration test as a manually triggered environment-specific lane. | Yes |

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

### NP-03 — Parser-Aware Kotlin Chunking (Active)

**Current progress:** Tree-sitter Kotlin dependency and initial ingestion
routing are implemented. The remaining work is grammar-shape verification,
focused unit tests, fallback validation, documentation, and indexing.

**Execution note:** The planned tests are unit-only. Uvicorn is not required;
any live API validation will be proposed before execution.

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

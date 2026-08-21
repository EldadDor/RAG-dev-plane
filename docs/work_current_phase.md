# Current Work Phase — Parser-Aware Kotlin Chunking

**Status:** Complete
**Last reviewed:** 2026-08-20
**Owner:** Project team
**Phase goal:** Replace generic Kotlin chunking with parser-aware symbols and
line-range metadata while preserving the existing loader/provider boundaries.

## Scope

This phase covers only:

- the request, ingestion, retrieval, memory, provider, and persistence flows;
- workspace/source-lifecycle behavior;
- current testing and validation boundaries;
- explicitly identifying deferred work.

It does not change runtime behavior, providers, database schema, API contracts,
or test implementation.

## Task Board

| ID | Task | Status | Evidence / outcome |
| --- | --- | --- | --- |
| CW-01 | Assess Kotlin parser options | Complete | `tree-sitter-kotlin` selected and added as a project dependency. |
| CW-02 | Implement Kotlin symbol chunking | Complete | Tree-sitter adapter emits type/function symbols, enclosing types, and line ranges. |
| CW-03 | Route Kotlin ingestion to the new chunker | Complete | Kotlin now uses the parser-aware adapter, with generic chunking on parse failure. |
| CW-04 | Add focused unit coverage | Complete | Kotlin and Java chunker tests passed (4 passed). |
| CW-05 | Update documentation and index it | In progress | README and architecture updated; index after full unit validation. |

## Execution Constraint

Focused Kotlin parser tests are unit-only and do **not** require Uvicorn, model
endpoints, or pgvector. Any proposed live integration/API test will be announced
before it is run.

## Validation Record

| Check | Result | Notes |
| --- | --- | --- |
| Documentation inventory | Pass | Current code and committed behavior were reviewed before the architecture refresh. |
| Runtime changes | Not applicable | This phase is documentation-only. |
| Architecture indexing | Pass | Architecture and phase records were indexed after approval. |

## Known Non-Blocking Item

The architecture document describes implemented behavior, not an aspirational
roadmap. Proposed future changes belong in `docs/next_phase.md` and need their
own approval.

## Current Working Tree Expected at Phase Close

- Modified `docs/architecture.md` — current system architecture.
- Modified `docs/work_current_phase.md` — active NP-01 task ledger.
- Modified `docs/next_phase.md` — NP-01 marked active.
- Modified `docs/complete_phases.md` — prior phase closed with its commit.

## Approval Gate

Approve all of the following before closing this phase:

- [x] The architecture description matches the running service and current code.
- [x] Provider separation and PostgreSQL-first behavior are accurately stated.
- [x] Current deferrals are acceptable and no unapproved roadmap work was added.
- [x] The updated architecture was indexed in the default workspace.
- [x] The documentation-only changes were committed as `df37f9b`.

## Close-Out Procedure

1. Review the architecture and phase records.
2. Index the approved architecture document.
3. Commit only the current phase documentation changes.
4. Update `docs/complete_phases.md` with the commit hash.
5. Activate the next approved item from `docs/next_phase.md`.

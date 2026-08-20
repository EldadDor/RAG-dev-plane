# Current Work Phase — Architecture Documentation Refresh

**Status:** Active
**Last reviewed:** 2026-08-20
**Owner:** Project team
**Phase goal:** Make the architecture documentation accurately describe the
implemented RAG service without changing runtime behavior.

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
| CW-01 | Inventory implemented behavior | Complete | Reviewed API, ingestion, retrieval, chat, memory, configuration, README, and phase records. |
| CW-02 | Replace outdated architecture overview | Complete | `docs/architecture.md` now describes current rather than starter-state behavior. |
| CW-03 | Document provider boundaries | Complete | Chat, embedding, vector-store, lexical-search, and memory adapters are distinguished. |
| CW-04 | Document workspace and lifecycle behavior | Complete | Metadata, content hashes, replacement, and stale-document removal are documented. |
| CW-05 | Document testing boundary | Complete | Unit tests and opt-in live integration validation are linked to `docs/testing.md`. |
| CW-06 | Index updated architecture | Pending | Index only after documentation review is complete. |

## Validation Record

| Check | Result | Notes |
| --- | --- | --- |
| Documentation inventory | Pass | Current code and committed behavior were reviewed before the architecture refresh. |
| Runtime changes | Not applicable | This phase is documentation-only. |
| Architecture indexing | Pending | Performed after the approval review. |

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

- [ ] The architecture description matches the running service and current code.
- [ ] Provider separation and PostgreSQL-first behavior are accurately stated.
- [ ] Current deferrals are acceptable and no unapproved roadmap work was added.
- [ ] The updated architecture may be indexed in the default workspace.
- [ ] The documentation-only changes may be committed.

## Close-Out Procedure

1. Review the architecture and phase records.
2. Index the approved architecture document.
3. Commit only the current phase documentation changes.
4. Update `docs/complete_phases.md` with the commit hash.
5. Activate the next approved item from `docs/next_phase.md`.

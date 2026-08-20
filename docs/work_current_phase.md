# Current Work Phase — Validation and Developer Workflow

**Status:** Awaiting review and approval to commit  
**Last reviewed:** 2026-08-20  
**Owner:** Project team  
**Phase goal:** Make the local developer workflow repeatable and prove the
running RAG stack works end to end without making live integration checks part
of the normal unit-test path.

## Scope

This phase covers only:

- Python 3.14 as the declared project and container runtime;
- a live, opt-in API integration test for the running local stack;
- test documentation and PyCharm execution guidance;
- removal of an accidental nested `tests` uv project.

It does not change retrieval behavior, providers, database schema, or model
configuration.

## Task Board

| ID | Task | Status | Evidence / outcome |
| --- | --- | --- | --- |
| CW-01 | Declare and lock Python 3.14 | Complete | Root `pyproject.toml`, `uv.lock`, Dockerfiles, README, and guidance use Python 3.14. |
| CW-02 | Establish a usable shared repository venv | Complete | Project `.venv` uses Python 3.14.2 and is executable from PyCharm and Codex. |
| CW-03 | Keep unit tests independent of live services | Complete | Normal suite uses mocked adapters and passed with 36 tests before the integration test was enabled. |
| CW-04 | Add a live-stack integration test | Complete | `tests/integration/test_live_stack.py` validates readiness, ingestion, grounding, source attribution, workspace isolation, and cleanup. |
| CW-05 | Validate the live stack in PyCharm | Complete | 37 tests passed against the running Uvicorn API, pgvector, embedding endpoint, and chat model. |
| CW-06 | Document testing and PyCharm configuration | Complete | `docs/testing.md` documents both test layers and the stable `--basetemp` configuration. |
| CW-07 | Index the testing guide | Complete | `docs/testing.md` was indexed into the default workspace as 7 chunks. |
| CW-08 | Remove accidental nested tests project | Complete, pending commit | `tests/pyproject.toml` is deleted; its untracked `tests/uv.lock` was removed. |

## Validation Record

| Check | Result | Notes |
| --- | --- | --- |
| Unit and API-contract suite | Pass | 36 tests passed when integration was skipped. |
| Full suite with live integration enabled | Pass | 37 passed in 19.83 seconds. |
| API readiness | Pass | Running API reported `status: ok`, PostgreSQL vector store available. |
| Testing guide indexing | Pass | One document / seven chunks indexed. |

## Known Non-Blocking Item

The unit suite emits one Qdrant client compatibility-probe warning. It is caused
by Qdrant's background version check in the mocked test environment. The
warning does not contact the configured live pgvector stack and did not affect
test results. Do not suppress or change production Qdrant behavior without a
separate approved task.

## Current Working Tree Expected at Phase Close

- Modified `.gitignore` — ignores the local integration-test temp directory.
- Modified `docs/testing.md` — records the proven PyCharm test settings.
- Deleted `tests/pyproject.toml` — removes the unintended nested uv project.
- Added this phase-management documentation set.

## Approval Gate

Approve all of the following before closing this phase:

- [ ] The documented test commands and PyCharm settings match the team workflow.
- [ ] The live test is intentionally opt-in and is not suitable for CI by default.
- [ ] The generated nested `tests` project should remain removed.
- [ ] The known Qdrant warning can remain until separately prioritized.
- [ ] The current changes may be committed as a documentation/workflow cleanup.

## Close-Out Procedure

1. Review the working tree against the list above.
2. Commit only the current phase changes.
3. Update `docs/complete_phases.md` with the commit hash and final validation.
4. Move the first approved item from `docs/next_phase.md` into a new current
   phase document.

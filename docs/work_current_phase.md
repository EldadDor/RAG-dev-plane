# Current Work Phase — NP-09 Golden Evaluation Set and Regression Harness

**Status:** Active
**Activated:** 2026-09-07
**Last reviewed:** 2026-09-07
**Owner:** Project team
**Roadmap:** [`extended_plan.md`](extended_plan.md)

## Objective

Make retrieval and answer-quality changes measurable, repeatable, and
comparable across chunking profiles, retrieval settings, and models.

## Scope and Guardrails

- Store human-verified golden cases as JSONL with a question, expected facts,
  and optional source hints.
- Provide pytest-compatible offline smoke tests and a richer local benchmark
  runner with result artifacts.
- Record run configuration, latency, metrics, and failure stage.
- Verify retrieval determinism before comparing metrics.
- Keep the benchmark read-only with respect to the document index and do not
  make live model/database checks mandatory in CI.
- Do not change retrieval, prompt, provider, or chunking behavior in this
  phase; NP-07 and NP-10 own those changes.

## Task Board

| ID | Task | Status |
| --- | --- | --- |
| CW-01 | Define the versioned golden-case JSONL schema, loader, and validation tests. | Complete 2026-09-07: strict JSONL loader and documented case template added. |
| CW-02 | Implement offline retrieval and answer metric helpers with explicit failure-stage reporting. | Complete 2026-09-07: deterministic source-hint, fact-coverage, and faithfulness-proxy metrics added. |
| CW-03 | Implement retrieval determinism checks and configuration/result artifacts. | Complete 2026-09-07: runner compares repeated retrieval IDs and writes portable JSON artifacts. |
| CW-04 | Add a local benchmark runner behind the existing adapter boundaries. | Complete 2026-09-07: provider-agnostic runner supports mocked offline evaluation. |
| CW-05 | Add human-verified cases from representative developer documents. | Blocked on verified expected facts and source hints. |
| CW-06 | Run offline smoke validation, then an approved local live benchmark and record the baseline. | In progress: offline suite passed 2026-09-07 (`56 passed, 1 skipped`); live baseline awaits golden cases. |

## Acceptance Checks

- The suite runs offline with mocks and validates dataset loading, metrics,
  determinism, configuration capture, and failure reporting.
- A local benchmark run writes a comparable result artifact.
- Each golden case has human-verified expected facts; source hints are optional.
- Results identify whether a failure arose during ingestion, retrieval,
  reranking, prompting, or generation.

## Handoff Constraint

No frontend work is required. Golden cases must use verified facts rather than
answers inferred from the system under evaluation.

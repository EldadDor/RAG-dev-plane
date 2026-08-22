# Current Work Phase — NP-05 CI Test Lanes

**Status:** Active
**Last reviewed:** 2026-08-22
**Owner:** Project team

## Objective

Establish reproducible CI lanes that always run the isolated Python 3.14 unit
suite and only run live integration checks through an explicitly approved,
environment-provisioned workflow.

## Scope and Guardrails

- CI-safe lane: `uv` + Python 3.14 + unit/API tests; no Uvicorn, models,
  pgvector, Langfuse, or office credentials.
- Live lane: manually dispatched only; never a default PR/push requirement.
- Preserve the existing opt-in integration guard: `RUN_LIVE_INTEGRATION=1`.
- Do not add deployment, frontend, gateway, or database migration work.

## Task Board

| ID | Task | Status | Evidence / outcome |
| --- | --- | --- | --- |
| CW-01 | Inspect existing CI assets and test commands | Pending | Identify current workflows, Python setup, and repository constraints. |
| CW-02 | Define required unit lane | Pending | Python 3.14, `uv sync`, and deterministic unit/API command. |
| CW-03 | Define manual live-integration lane | Pending | Explicit dispatch inputs, required secrets, services, and no automatic trigger. |
| CW-04 | Add CI workflow configuration | Pending | Separate safe and manual lanes with clear names/logs. |
| CW-05 | Validate CI-safe lane locally | Pending | No Uvicorn or live dependency use. |
| CW-06 | Document workflow and update phase records | Pending | Update testing/workflow docs; index after approval. |

## Approval Gates

- [ ] Review the proposed workflow triggers, permissions, and secret names before CI files are created.
- [ ] Approve any live runner/service topology before the manual lane is implemented or run.
- [ ] Approve phase close after the safe lane is validated.

## Execution Constraint

I will announce before any command that starts Uvicorn or contacts pgvector,
model endpoints, Langfuse, or other live office services.

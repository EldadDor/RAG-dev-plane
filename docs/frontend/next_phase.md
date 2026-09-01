# Next Frontend Phase — Approval Backlog

**Status:** FP-01 Chat Workspace Foundation is active. This file tracks work
after FP-01; authoritative current-task status remains in
`work_current_phase.md`.
**Last reviewed:** 2026-09-01
**Owner:** Frontend team

## Current Phase Checkpoint

- FP-04 workspace selection and session list/load/new-chat flow completed on
  2026-08-29 against the approved API and error contracts.
- FP-05 bounded history, rename, and approved archive behavior completed on
  2026-08-29.
- FP-06 streaming, citations, cancellation, and recovery work completed on
  2026-09-01 against the published named-event SSE contract. Operator-run
  browser/API validation remains pending because it requires the live LLM and
  pgvector stack.
- Backend live-stack workspace/session validation and documentation indexing
  are complete; NP-05 is closed.

This file is the frontend-only intake and ordering record. Before a candidate
becomes active, move it into `work_current_phase.md`, define its task board,
and record the applicable approval decision.

## Candidate Work

| Priority | ID | Candidate task | Why it matters | Approval required |
| --- | --- | --- | --- | --- |
| 1 | FP-02 | Frontend hardening and UX refinement | Strengthen accessibility, responsive behavior, error recovery, and focused test coverage after the foundation is accepted. | FP-01 acceptance, acceptance criteria, and test scope. |
| 2 | FP-03 | Office delivery integration | Configure the approved static deployment, proxy, identity handling, and SSE behavior with the infrastructure owner. | Gateway identity, Nginx/CI-CD/TLS/CORS, and deployment plan. |

## Recommended Next Phase

### FP-02 — Frontend Hardening and UX Refinement

**Proposed objective:** Harden the accepted React chat experience with focused
accessibility, responsive-layout, recovery-state, and regression-test work.

**Acceptance checks:**

- Keyboard and screen-reader behavior is verified for workspace, session,
  composer, citation, rename, and archive interactions.
- Narrow and wide layouts preserve readable chat, recent-session, and source
  navigation.
- Recoverable API/SSE failures have consistent retry and focus behavior.
- Focused regression tests, type checks, and the production build pass without
  live backend/model/database services.
- The operator-run browser/API checklist in `integration_test_plan.md` passes
  with the approved live stack, including streaming completion and cancellation.

**Activation:** Begin only after FP-01 acceptance and phase closure are
recorded in `work_current_phase.md`.

## Phase Intake Checklist

- [x] Clear objective, bounded scope, and explicit exclusions.
- [ ] Affected frontend files, dependencies, proxy behavior, and tests identified.
- [x] Backend-contract dependencies checked against `../frontend_architecture.md`.
- [ ] Local validation and any approved live validation defined.
- [ ] Privacy, identity, and browser-secret exposure reviewed.
- [ ] Required approvals and user/product decisions recorded.
- [ ] Completion criteria and planned commit boundary recorded.

## Deferred Until Approved

- Gateway identity-header names and authentication implementation.
- Nginx CI/CD, static asset path, backend upstream, TLS, and CORS changes.
- Archive-versus-permanent-deletion wording.
- Ingestion, administration, provider, database, or backend contract changes.

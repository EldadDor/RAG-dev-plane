# Next Frontend Phase — Approval Backlog

**Status:** FP-02 Frontend Hardening and UX Refinement is complete. This file
tracks work after FP-02; authoritative current-task status remains in
`work_current_phase.md`.
**Last reviewed:** 2026-09-10
**Owner:** Frontend team

## Current Phase Checkpoint

- FP-01 received formal closure approval on 2026-09-05 after unit tests, type
  checks, and the production build passed.
- FP-02 was activated on 2026-09-05 with user approval for its accessibility,
  responsive behavior, recovery-state, and focused unit-test scope.
- FP-02 received formal closure approval on 2026-09-05 after the approved
  local validation set passed.
- FP-04 workspace selection and session list/load/new-chat flow completed on
  2026-08-29 against the approved API and error contracts.
- FP-05 bounded history, rename, and approved archive behavior completed on
  2026-08-29.
- FP-06 streaming, citations, cancellation, and recovery work completed and
  passed operator-run browser/API validation on 2026-09-03 through the IPv4
  Vite proxy with the live LLM and pgvector stack.
- Backend live-stack workspace/session validation and documentation indexing
  are complete; NP-05 is closed.

This file is the frontend-only intake and ordering record. Before a candidate
becomes active, move it into `work_current_phase.md`, define its task board,
and record the applicable approval decision.

## Candidate Work

| Priority | ID | Candidate task | Why it matters | Approval required |
| --- | --- | --- | --- | --- |
| 1 | FP-03 | Office delivery integration | Configure the approved static deployment, proxy, identity handling, and SSE behavior with the infrastructure owner. | Gateway identity, Nginx/CI-CD/TLS/CORS, and deployment plan. |
| 2 | NP-15-FE | Image-bearing source citations | Render authorized images associated with retrieved Word citations in the Sources experience. | **Proposed after backend NP-14 — review required** |

## Recommended Next Phase

FP-03 remains the existing delivery candidate. The NP-15 frontend slice is a
separate review proposal and must not begin until Word asset persistence and
the authorized API contract are approved and implemented by the backend.

## Phase Intake Checklist

- [x] Clear objective, bounded scope, and explicit exclusions.
- [x] Affected frontend files, dependencies, proxy behavior, and tests identified.
- [x] Backend-contract dependencies checked against `../frontend_architecture.md`.
- [x] Local validation defined; live validation requires separate approval.
- [x] Privacy, identity, and browser-secret exposure reviewed.
- [x] Required approvals and user/product decisions recorded.
- [x] Completion criteria and planned commit boundary recorded.

## Deferred Until Approved

- Gateway identity-header names and authentication implementation.
- Nginx CI/CD, static asset path, backend upstream, TLS, and CORS changes.
- Archive-versus-permanent-deletion wording.
- Ingestion, administration, provider, database, or backend contract changes.
- Image-bearing citation UI until NP-13 through NP-15 and the contract in
  `../document_image_support_plan.md` are approved.

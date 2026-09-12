# Current Frontend Work Phase — FP-02 Frontend Hardening and UX Refinement

**Status:** Completed
**Last reviewed:** 2026-09-12
**Owner:** Frontend team

## Objective

Harden the accepted React chat experience with focused accessibility,
responsive-layout, recovery-state, and regression-test work. The phase is
limited to the existing frontend and proxy-only API contract.

## Scope and Guardrails

- Work only in `frontend/**`; the API contract is read-only unless separately
  approved by the backend owner.
- Keep the existing relative Vite/Nginx proxy integration. Do not add browser
  secrets, identity headers, direct backend URLs, or live-service traffic.
- Keep automated coverage unit-focused. Browser automation, end-to-end tests,
  visual regression tooling, and new dependencies require separate approval.
- Do not change archive wording, office deployment, ingestion, or
  administrative features.

## Task Board

| ID | Task | Status | Evidence / outcome |
| --- | --- | --- | --- |
| FP2-01 | Audit and harden keyboard, screen-reader, and recoverable-error behavior | Completed | 2026-09-05: Added in-place workspace/session retry controls, `aria-busy` chat state, alert/status semantics for recoverable stream states, a labelled rename form, source updates, and `aria-current` on the active session. Added an SSE-incomplete unit regression. Passed Vitest (4 tests), `tsc -b`, and Vite production build; no live services or browser automation ran. |
| FP2-02 | Refine narrow and wide responsive layout behavior | Completed | 2026-09-05: Preserved the existing desktop grid and added narrow-layout safeguards for the workspace picker, chat heading/actions, rename controls, pane padding/tabs, and conversation bubble width. Passed Vitest (4 tests), `tsc -b`, and Vite production build; no browser automation or live services ran. |
| FP2-03 | Extend focused unit regression coverage | Completed | 2026-09-05: Added Node-environment coverage for session-detail mapping, encoded rename/archive requests, incomplete SSE streams, and safe terminal SSE errors. Vitest now passes 6 tests; `tsc -b` and the production build pass. No new dependencies, browser automation, or live services were used. |
| FP2-04 | Run local validation and prepare phase handoff | Completed | 2026-09-05: Passed Vitest (6 tests), `tsc -b`, Vite production build, and `git diff --check`. The audit found no API-contract discrepancy, so no backend handoff was required. Browser automation and live-stack validation did not run because they are outside the approved scope. Changes are ready for review and commit. |

## Acceptance Checks

- Keyboard and screen-reader behavior is verified for workspace, session,
  composer, citation, rename, and archive interactions.
- Narrow and wide layouts preserve readable chat, recent-session, and source
  navigation.
- Recoverable API/SSE failures have consistent retry and focus behavior.
- Focused regression tests, type checks, and the production build pass without
  live backend/model/database services.
- Approved live-stack validation, if requested, passes the existing operator
  checklist for streaming completion and cancellation.

## Approval Gates

- [x] Approve FP-01 acceptance and FP-02 activation, acceptance criteria, and
  unit-test scope. Approved 2026-09-05.
- [ ] Approve any additional dependency, proxy/authentication change, browser
  automation, visual-regression tooling, or live-service validation before use.
- [x] Approve FP-02 phase closure after its accepted local-scope checks pass.
  Approved 2026-09-05.

## Execution Constraints

- Update the task board and **Last reviewed** before and after every task.
- Do not start a planned task until its prior task is recorded as completed,
  blocked, or deferred.
- Do not start Uvicorn or contact model/database services without explicit
  approval. Record backend gaps in the frontend-to-backend handoff instead of
  changing backend code.

## Phase Handoff

Keep existing proxy-only API behavior: no browser user ID or identity headers;
refresh workspace discovery for `403`; and remove unavailable sessions for
`404`. Raise any contract gap through the frontend-to-backend handoff. FP-02
was formally closed with the approved unit-focused validation scope on
2026-09-05.

Status review, 2026-09-11: FP-02 remains complete. The backend's latest
image-bearing-citation handoff is contract-aligned with the implemented
frontend; its only requested follow-up is separately approved live browser
validation after the updated API is restarted. No frontend code or contract
change was required by this review. Evidence: reviewed
`docs/agent_handoff/backend_to_frontend.md`, `docs/frontend_architecture.md`,
`frontend/src/App.tsx`, `frontend/src/api.ts`, and `frontend/src/api.test.ts`;
ran `rg` for image-citation implementation and `git diff --check` (passed).
No type check, test suite, production build, browser automation, or live
backend/model/database validation ran because this was a read-only status
review.

Hebrew-ingestion review, 2026-09-12: this is backend-owned work, so no
frontend task was started. Recorded the benchmark-first and profile-isolation
requirements in `docs/agent_handoff/frontend_to_backend.md`. Evidence: reviewed
the supplied Perplexity thread, official DICTA and Ollama model documentation,
and official OpenAI embedding documentation. No application code, service,
model, database, or frontend validation command ran.

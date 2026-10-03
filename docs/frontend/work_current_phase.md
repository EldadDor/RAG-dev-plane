# Current Frontend Work Phase — FP-02 Frontend Hardening and UX Refinement

**Status:** FP-02 completed; FP-10–FP-12 implemented and locally validated
**Last reviewed:** 2026-10-03
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
| FP-07 | Restructure the Vite frontend for independently buildable applications | Completed | 2026-09-13: Moved the existing SPA to `frontend/apps/rag-dev-plane`, added app-scoped Vite configuration and root `build:all`/`build:rag-dev-plane` scripts, and configured output at `frontend/build/dist/rag-dev-plane`. Passed Vitest (7 tests), `tsc -b`, direct Vite production build, and `git diff --check`; the sandbox runtime provides Node but not npm, so `npm run build:all` itself was not invoked. No live services or browser automation ran. Branch: `codex/multi-app-vite-structure`. |
| FP-08 | Make source citations individually expandable | Completed | 2026-09-14: Source citations now start collapsed, expose an accessible per-source toggle, and animate their metadata, excerpt, and linked image content independently. The transition disables under reduced-motion preferences; collapsed image links are not keyboard-focusable. Passed Vitest (7 tests), `tsc -b`, direct Vite production build, and `git diff --check`. No live services or browser automation ran. |
| FP-09 | Record UI enhancement tasks and document metadata dependency | Completed | FP-09: 2026-10-02: Added FP-10 recent documents, FP-11 configurable chunk-size indicators, and FP-12 document-type colors with acceptance criteria, dependencies, validation, and commit boundaries in next_phase.md. Recorded missing metadata contract in docs/agent_handoff/frontend_to_backend.md. Verified written records with targeted reads; no application code changed. Type checks, tests, builds, browser automation, and live services were not run (documentation-only intake). |
| FP-10 | Recent ingested documents in the left panel | Completed | FP-10: 2026-10-02: Implemented api.ts, documentCatalog.ts, DocumentsPanel.tsx, App.tsx and styles.css: relative scoped API, newest-first server ordering, refresh/load-more, no polling, abort/stale guards, one 409 restart, scope/revision checking, 401/403 clearing and 403 discovery, 503 retry, null ingestion history, valid zero counts, Hebrew/long-name and narrow-layout handling. Passed 34 Vitest tests including pagination/restart/abort regressions, tsc -b, Vite build and git diff --check. No browser automation or live services ran; manual browser integration remains unverified. Commit: c58e667. |
| FP-11 | Configurable chunk-count size indicators | Completed | FP-11: 2026-10-02: documentBadges.ts centralizes inclusive upper bounds 25/100/500 and size colors; Small/Medium/Big/Extra-Large text badges, exact chunk totals and expandable guide render in DocumentsPanel.tsx. Zero is Small; invalid/missing counts are Unknown. Boundary/invalid-value unit coverage passed in 34-test suite; tsc -b and production build passed. Commit: c58e667. |
| FP-12 | Configurable document-type colors | Completed | FP-12: 2026-10-02: documentBadges.ts maps word/pdf/markdown/html/text/code/unknown to configurable color pairs and explicit text labels; separate type/size badges in DocumentsPanel.tsx with future-type fallback. Unit tests cover canonical, future and inherited object keys. Passed 34 Vitest tests, tsc -b, Vite production build and git diff --check; no dependencies, browser automation or live services added. Commit: c58e667. |
| FP-13 | Record UI behavior requirements and backend API handoff | Completed | FP-13: 2026-10-03: Added FP-14 through FP-17 requirements, acceptance criteria, ordering, dependencies and validation in next_phase.md; recorded account/preferences/logout, document overview/preview and session-list clarification in docs/agent_handoff/frontend_to_backend.md. Evidence: read frontend_architecture.md first; rtk read next_phase.md and targeted handoff/phase rereads verified records. Documentation only; no application code, API contract edits or commit. Type checks, tests, builds, browser automation and live services not run. |

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

Status review, 2026-09-12: FP-02 remains complete. The backend's
image-bearing-citation handoff is contract-aligned with the implemented
frontend, and the live browser checklist passed: a grounded Hebrew Word result
rendered its associated PNG in Related source images. No frontend code or
contract change was required.

Hebrew-ingestion review, 2026-09-12: this is backend-owned work, so no
frontend task was started. Recorded the benchmark-first and profile-isolation
requirements in `docs/agent_handoff/frontend_to_backend.md`. Evidence: reviewed
the supplied Perplexity thread, official DICTA and Ollama model documentation,
and official OpenAI embedding documentation. No application code, service,
model, database, or frontend validation command ran.

UI enhancement validation, 2026-10-02: user authorized proceeding after the
NP-20 rollout handoff. Local commands passed:
`node node_modules/typescript/bin/tsc -b`,
`node node_modules/vitest/vitest.mjs run` (34 tests),
`node node_modules/vite/bin/vite.js build --config apps/rag-dev-plane/vite.config.ts`,
and scoped `git diff --check` with a per-command safe.directory override.
Direct Node entry points were used because npm is not available in the sandbox.
No Uvicorn, model/database calls, live API traffic, browser automation, or
manual browser integration ran. No commit created. Backend contract unchanged.

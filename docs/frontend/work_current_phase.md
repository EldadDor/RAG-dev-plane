# Current Frontend Work Phase — FP-01 Chat Workspace Foundation

**Status:** Completed
**Last reviewed:** 2026-09-05
**Owner:** Frontend team

## Objective

Create the React, TypeScript, and Vite foundation for the internal developer
documentation chat experience, then deliver the workspace-filtered streaming
chat UI defined in `../frontend_architecture.md`.

## Scope and Guardrails

- Work only in `frontend/**`; backend contracts and shared backend documents are
  read-only unless separately approved.
- Use only the configured Vite/Nginx proxy for HTTP and SSE. Do not embed API
  keys, provider endpoints, database credentials, or Langfuse settings in the
  browser bundle or frontend environment files.
- Do not send a user ID in any request. The trusted gateway derives identity.
- Include chat, workspace filtering, sources, and per-user session controls;
  exclude ingestion and administrative screens.
- Treat archive wording as provisional until the product decision is supplied.

## Task Board

| ID | Task | Status | Evidence / outcome |
| --- | --- | --- | --- |
| FP-01 | Inspect frontend baseline, scripts, and existing UX assets | Completed | 2026-08-22: `frontend/` contains only `AGENTS.md` plus empty `public/` and `src/` directories. No Vite project, package manifest, source, scripts, dependencies, or UX assets exist. |
| FP-02 | Confirm API client types and proxy-only integration boundary | Completed | 2026-08-22: Client will use relative proxy routes only: `POST /chat`, `POST /chat/stream`, and session GET/PATCH/DELETE routes. SSE order is answer → `meta` → `done`; requests contain no user ID. Workspace discovery/authorization is not specified and blocks live workspace data integration. |
| FP-03 | Establish app shell and responsive three-pane layout | Completed | 2026-08-22: Added Vite/React/TypeScript project files, proxy-only `/chat` development route, and responsive accessible shell with workspace selector, central composer, sources area, and recent-chat pane. Node/npm are unavailable locally, so install/type-check/build verification remains pending FP-07. |
| FP-04 | Implement workspace selection and session list/load/new-chat flow | Completed | 2026-08-29: Implemented proxy-only workspace discovery, workspace-filtered newest-first session listing, session detail loading without a workspace query, new-chat reset, canonical `last_preview`/timestamp mapping, and safe `403`/`404` recovery. `git diff --check` passes; type-check/build remain pending FP-07 because Node/npm are unavailable. Live-stack validation remains with the backend. |
| FP-05 | Implement bounded history rendering and session actions | Completed | 2026-08-29: Implemented labeled compact summary and chronological recent turns with timestamps, inline rename, and approved “Archive chat” confirmation/action through the documented PATCH/DELETE endpoints. Session actions apply safe `403` workspace recovery and `404` removal. `git diff --check` passes; type-check/build remain pending FP-07 because Node/npm are unavailable. |
| FP-06 | Implement streaming answer, metadata, citations, and recovery states | Completed | 2026-09-04: Implemented fetch-based POST SSE parsing for named JSON answer, meta, error, and done events. Answer deltas render incrementally; session ID, grounded state, and sources commit only from meta; Stop uses AbortController; interruption preserves visibly incomplete text; no automatic retry/reconnect occurs. Live browser validation through the IPv4 Vite proxy passed workspace loading, streaming, history/session commit, sources, and archive cleanup; browser console was clean. |
| FP-07 | Add frontend tests, accessibility checks, and production-build verification | Completed | 2026-09-05: User approved Vitest for a minimal unit-only baseline. Added `vitest` and `npm test` (`vitest run`) plus `src/api.test.ts`, covering proxy-contract mapping, safe error-envelope handling, and split SSE answer/meta/done parsing. Passed: `node node_modules/vitest/vitest.mjs run` (3 tests), `node node_modules/typescript/bin/tsc -b`, `node node_modules/vite/bin/vite.js build`, and `git diff --check`. No live services or browser/UI end-to-end suite ran. Changes are uncommitted; no commit was requested. |
| FP-08 | Update this phase record and frontend backlog; prepare handoff | Completed | 2026-09-05: Reconciled the phase records after local test-baseline completion. The backend fixed the empty `workspace_id` contract discrepancy (`422 invalid_request`); no frontend change is required. User formally reviewed and approved FP-01 closure on 2026-09-05. |

## Required Update Protocol

Before starting any task, update its row to **In progress** with the intended
scope and any approval dependency. Immediately after the task, update its row
to **Completed**, **Blocked**, or **Deferred** with concrete evidence. Update
**Last reviewed** on every such change. Do not begin the next task while the
prior task's result and approval state are unrecorded.

## Approval Gates

- [x] Approve FP-01 scope and implementation order before editing application code. Approved 2026-08-22.
- [x] Approve the workspace discovery/authorization approach before FP-04.
  Approved and implemented by backend NP-05 on 2026-08-24.
- [x] Approve user-facing archive wording before implementing the archive
  portion of FP-05. Approved 2026-08-29: “Archive chat” with confirmation
  “Archive this chat? It will be removed from your recent chats.”
- [x] Review the planned streaming/reconnect interaction and error states before
  FP-06. Approved 2026-08-31; use incremental answer rendering, explicit
  cancellation, safe code-specific failures, and user-initiated retry rather
  than automatic replay of a POST request.
- [x] Approve any new frontend dependency, proxy configuration change, or
  authentication/header behavior before it is added. Approved for the FP-03
  baseline dependencies on 2026-08-22; no proxy/authentication behavior will
  be invented beyond the documented contract.
- [x] Approve phase closure after local type checks, tests, and production build
  have passed. Approved 2026-09-05.

## Execution Constraints

- Announce before requesting any approval-dependent action.
- Do not start Uvicorn, contact live model/database services, or send browser
  traffic directly to a backend endpoint without explicit approval.
- Surface backend-contract gaps in this file and hand them to the backend task;
  do not silently invent an API contract.

## Backend Handoff

Call `GET /workspaces` on application load and render its `workspaces` entries.
Send the selected `workspace_id` with chat and session-list requests; session
detail uses only its session ID, whose stored workspace the backend revalidates.
Do not send a user ID or development identity header. Treat `403` as
lost/invalid workspace access and refresh discovery; treat `404` session detail
as unavailable and remove it from the current UI state.

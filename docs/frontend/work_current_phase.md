# Current Frontend Work Phase — FP-01 Chat Workspace Foundation

**Status:** Active
**Last reviewed:** 2026-08-31
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
| FP-06 | Implement streaming answer, metadata, citations, and recovery states | Blocked | 2026-08-31: Backend approved the interaction/recovery requirements but explicitly deferred the concrete wire contract. Await the implemented POST body, named answer/meta/error/done payloads, source schema, and cancellation semantics in `docs/frontend_architecture.md`; frontend acknowledged the response and added no streaming assumptions. |
| FP-07 | Add frontend tests, accessibility checks, and production-build verification | Pending | Type check, relevant tests, and static production build pass without live backend/model/database services. |
| FP-08 | Update this phase record and frontend backlog; prepare handoff | Pending | Record evidence, unresolved contract inputs, approval decisions, and completion boundary. |

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
- [ ] Approve phase closure after local type checks, tests, and production build
  have passed.

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

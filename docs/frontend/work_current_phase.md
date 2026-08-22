# Current Frontend Work Phase — FP-01 Chat Workspace Foundation

**Status:** Proposed — awaiting approval
**Last reviewed:** 2026-08-22
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
| FP-01 | Inspect frontend baseline, scripts, and existing UX assets | Pending | Record constraints and preserve unrelated work. |
| FP-02 | Confirm API client types and proxy-only integration boundary | Pending | Map chat, stream, sessions, rename, and archive calls to the documented contract; record gaps without changing backend behavior. |
| FP-03 | Establish app shell and responsive three-pane layout | Pending | Workspace selector, central chat, recent-session pane, and source drawer are accessible and usable at supported widths. |
| FP-04 | Implement workspace selection and session list/load/new-chat flow | Pending | Sessions are filtered by `workspace_id`; no browser-supplied user identity. |
| FP-05 | Implement bounded history rendering and session actions | Pending | Clearly label compact summary versus latest raw turns; rename and archive use documented endpoints. |
| FP-06 | Implement streaming answer, metadata, citations, and recovery states | Pending | SSE answer/meta/done sequencing, sources drawer, cancellation/error/reconnect handling, and grounded-state display work through the proxy. |
| FP-07 | Add frontend tests, accessibility checks, and production-build verification | Pending | Type check, relevant tests, and static production build pass without live backend/model/database services. |
| FP-08 | Update this phase record and frontend backlog; prepare handoff | Pending | Record evidence, unresolved contract inputs, approval decisions, and completion boundary. |

## Required Update Protocol

Before starting any task, update its row to **In progress** with the intended
scope and any approval dependency. Immediately after the task, update its row
to **Completed**, **Blocked**, or **Deferred** with concrete evidence. Update
**Last reviewed** on every such change. Do not begin the next task while the
prior task's result and approval state are unrecorded.

## Approval Gates

- [ ] Approve FP-01 scope and implementation order before editing application code.
- [ ] Approve the workspace discovery/authorization approach before FP-04; the
  architecture currently leaves this API unresolved.
- [ ] Approve user-facing archive wording before FP-05.
- [ ] Review the planned streaming/reconnect interaction and error states before FP-06.
- [ ] Approve any new frontend dependency, proxy configuration change, or
  authentication/header behavior before it is added.
- [ ] Approve phase closure after local type checks, tests, and production build
  have passed.

## Execution Constraints

- Announce before requesting any approval-dependent action.
- Do not start Uvicorn, contact live model/database services, or send browser
  traffic directly to a backend endpoint without explicit approval.
- Surface backend-contract gaps in this file and hand them to the backend task;
  do not silently invent an API contract.

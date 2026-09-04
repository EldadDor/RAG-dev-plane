# Frontend → Backend

Add newest entries directly below this heading. Frontend owns writing this file;
the backend reads it and records responses in `backend_to_frontend.md`.

## 2026-09-03 — Frontend archive action live validation passed

- **From:** Frontend
- **To:** Backend
- **Type:** Validation
- **Status:** Resolved
- **Affected contract/files:** `DELETE /chat/sessions/{id}`; `frontend/src/App.tsx`
- **Message:** The temporary browser-created test chat was archived through the
  frontend confirmation flow. The UI returned to the new-chat state and the
  recent-chat list was empty, confirming the expected `204` archive behavior.
- **Action requested:** None.
- **Supersedes / follow-up:** Completes cleanup for the 2026-09-03 frontend
  proxy and streaming validation.

## 2026-09-03 — Frontend proxy and streaming UI live validation passed

- **From:** Frontend
- **To:** Backend
- **Type:** Validation
- **Status:** Resolved
- **Affected contract/files:** Vite proxy; `GET /workspaces`; `GET /chat/sessions`; `POST /chat/stream`; `frontend/src/App.tsx`
- **Message:** With the frontend listening on IPv4, browser validation through
  `http://127.0.0.1:5173` passed. The UI loaded authorized workspaces and an
  empty session list, entered streaming state after submission, rendered the
  completed answer, committed the returned session/history, and rendered the
  meta-provided source drawer. Browser console inspection found no warnings or
  errors. This validation used the Vite proxy path, not a direct browser call
  to the backend.
- **Action requested:** None. The separate empty-workspace-ID contract finding
  remains open in the entry below.
- **Supersedes / follow-up:** Confirms FP-06 browser integration validation.

## 2026-09-03 — Live API validation: empty session-list workspace ID returns 403, not documented 422

- **From:** Frontend
- **To:** Backend
- **Type:** Bug
- **Status:** Needs review
- **Affected contract/files:** `GET /chat/sessions?workspace_id=<non-empty text>`; `docs/frontend_architecture.md`
- **Message:** Live validation against the active local API found that
  `GET /chat/sessions?workspace_id=` returns `403` with the safe
  `workspace_access_denied` envelope. The authoritative contract says an empty
  workspace ID is invalid input and should return `422 invalid_request`.
  Valid `local` returns `200 []`, and `not-authorized` correctly returns `403`.
- **Action requested:** Align the endpoint with the documented non-empty query
  constraint, or update the authoritative contract if `403` is intentional.
- **Supersedes / follow-up:** New live-validation finding.

## 2026-09-01 — FP-06 implemented against published SSE contract; validation checklist prepared

- **From:** Frontend
- **To:** Backend
- **Type:** Validation
- **Status:** Needs review
- **Affected contract/files:** `POST /chat/stream`; `frontend/src/api.ts`; `frontend/src/App.tsx`; `docs/frontend/integration_test_plan.md`
- **Message:** Frontend implemented the published POST/fetch SSE contract:
  named JSON `answer` deltas append verbatim; `meta` exclusively commits the
  session ID, grounded state, and source drawer; terminal `error` followed by
  `done` preserves a visibly incomplete answer; and Stop/workspace/chat/view
  cancellation uses `AbortController` with no automatic replay. The browser
  integration checklist is ready, but has not been run because the operator is
  responsible for starting the LLM and pgvector services.
- **Action requested:** No contract change requested. When the live stack is
  available, review any browser-observable mismatch reported from the checklist.
- **Supersedes / follow-up:** Resolves the 2026-08-31 wire-contract clarification.

## 2026-08-31 — FP-06 approval acknowledged; wire contract still required

- **From:** Frontend
- **To:** Backend
- **Type:** Clarification
- **Status:** Needs review
- **Affected contract/files:** `POST /chat/stream`; `docs/frontend_architecture.md`
- **Message:** Frontend acknowledges approval of the FP-06 interaction and
  recovery requirements and will not infer an answer shape from the current
  unnamed SSE `data:` chunks. FP-06 remains blocked exactly as requested until
  the canonical request body, named event payloads, source/citation schema,
  completion behavior, and cancellation persistence semantics are implemented
  and published with concrete examples in the authoritative architecture file.
- **Action requested:** Publish the implemented wire contract and reply in
  `backend_to_frontend.md` when frontend implementation may resume.
- **Supersedes / follow-up:** Follows the 2026-08-31 streaming wire-contract
  request and acknowledges the backend's requirements approval.

## 2026-08-31 — Specify FP-06 streaming wire contract

- **From:** Frontend
- **To:** Backend
- **Type:** Clarification
- **Status:** Needs review
- **Affected contract/files:** `POST /chat/stream`; `docs/frontend_architecture.md`
- **Message:** FP-06 interaction and recovery behavior is approved, but the
  authoritative frontend contract currently defines only the event order. The
  client needs the exact request body and SSE wire payloads before it can
  implement without assumptions. Please specify: required `question`,
  `workspace_id`, and optional/new-versus-existing `session_id` behavior; the
  exact `answer` event data shape and whether chunks are deltas; the `meta`
  object including `session_id`, `grounded`, and every source/citation field;
  the `done` payload; and whether a pre-answer or post-answer cancellation
  persists a turn/session. Confirm that post-start `error` data is the existing
  safe `{ code, message }` envelope and that interrupted POST streams have no
  resumable event ID, so the frontend must offer explicit user retry rather
  than automatic replay.
- **Action requested:** Approve and implement the canonical streaming request,
  event, source, completion, and cancellation semantics; document concrete JSON
  examples in `docs/frontend_architecture.md`; respond in
  `backend_to_frontend.md` when FP-06 may implement against them.
- **Supersedes / follow-up:** None.

## 2026-08-29 — Frontend aligned; confirm live-stack workspace validation

- **From:** Frontend
- **To:** Backend
- **Type:** Validation
- **Status:** Needs review
- **Affected contract/files:** `GET /workspaces`; workspace-scoped session routes; `frontend/src/api.ts`; `frontend/src/App.tsx`
- **Message:** FP-04 now parses the approved workspace envelope, bare
  newest-first session array, canonical session fields, timestamped detail,
  and safe error envelope. Session detail no longer sends `workspace_id`;
  `403` refreshes workspace discovery and `404` removes an unavailable session.
  The earlier backend handoff still lists SQL migration/local-seed live-stack
  validation as pending. Frontend has not started Uvicorn or contacted live
  backend/model/database services.
- **Action requested:** Confirm in `backend_to_frontend.md` when migrations,
  local seed, and normal-stack workspace/session validation are complete, or
  report any frontend-observable defect through the handoff.
- **Supersedes / follow-up:** Follows the 2026-08-27 backend validation entry
  and acknowledges the 2026-08-29 implemented contract entry.

## 2026-08-28 — Specify workspace and session JSON contracts for FP-04

- **From:** Frontend
- **To:** Backend
- **Type:** Clarification
- **Status:** Needs review
- **Affected contract/files:** `GET /workspaces`; `GET /chat/sessions?workspace_id=`; `GET /chat/sessions/{id}`; `docs/frontend_architecture.md`
- **Message:** The architecture document defines the endpoints and workspace
  authorization behavior but not their JSON envelopes or session resource
  shapes. The FP-04 client currently needs the exact success payload for
  workspace discovery, the session list, and a selected session. Please
  document the canonical names and types for: workspace ID, display name, and
  role; session ID, title, preview, workspace ID, and ordering/timestamp; and
  the session-detail fields needed next for bounded history (compact summary
  plus the latest raw turns and each turn's role/content/timestamp). Confirm
  whether `workspace_id` is required on the detail endpoint as a query
  parameter, as required for other workspace-scoped session operations.
- **Action requested:** Add the approved response schemas, list ordering, and
  required query parameters to `docs/frontend_architecture.md`; reply with the
  implemented schema and migration/live-validation status in
  `backend_to_frontend.md`.
- **Supersedes / follow-up:** Frontend should not treat the provisional
  `{ workspaces: [...] }` / `{ sessions: [...] }` parsing implementation as
  live-contract verified until this entry is resolved.

## 2026-08-28 — Define browser-visible API error semantics

- **From:** Frontend
- **To:** Backend
- **Type:** API change
- **Status:** Proposed
- **Affected contract/files:** Workspace and chat/session endpoints; `docs/frontend_architecture.md`
- **Message:** The frontend needs stable error status semantics to render
  recovery states without exposing backend detail. The existing handoff says a
  `403` means lost or invalid workspace access and should trigger workspace
  refresh. Please confirm documented behavior for `401`, `403`, `404`, and
  `422`, plus a minimal safe JSON error envelope (for example a stable machine
  code and user-safe message). This applies to workspace discovery, session
  list/detail, rename/archive, and later chat/stream requests.
- **Action requested:** Approve or revise the proposed status/error contract
  in `docs/frontend_architecture.md`, then report the result in
  `backend_to_frontend.md`.
- **Supersedes / follow-up:** None.

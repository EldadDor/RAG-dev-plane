# Frontend → Backend

Add newest entries directly below this heading. Frontend owns writing this file;
the backend reads it and records responses in `backend_to_frontend.md`.

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

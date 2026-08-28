# Backend → Frontend

Add newest entries directly below this heading. Backend owns writing this file;
the frontend reads it and records responses in `frontend_to_backend.md`.

## 2026-08-29 — FP-04 contract approved and implemented

- **From:** Backend
- **To:** Frontend
- **Type:** API change
- **Status:** Implemented
- **Affected contract/files:** `docs/frontend_architecture.md`; workspace and session endpoints
- **Message:** The backend-approved contract now specifies canonical workspace
  and session payloads, newest-first session lists, UTC `updated_at` and turn
  `created_at` timestamps, and the safe `{ code, message }` error envelope.
  `GET /chat/sessions` remains a bare array and session detail needs no
  `workspace_id`. The in-memory fallback now matches the timestamped,
  chronological detail response and deterministic list ordering.
- **Action requested:** Update FP-04 parsing to the documented bare session
  array and use the safe error codes. Do not render an error `message` as a
  substitute for application copy; use it only as the approved fallback.
- **Supersedes / follow-up:** Resolves both 2026-08-28 frontend requests.

## 2026-08-28 — Review of FP-04 schema and error-semantics requests

- **From:** Backend
- **To:** Frontend
- **Type:** Clarification
- **Status:** Needs review
- **Affected contract/files:** `GET /workspaces`; `GET /chat/sessions`; `GET /chat/sessions/{id}`; `docs/frontend_architecture.md`
- **Message:** The implemented success shapes are:
  - `GET /workspaces` returns
    `{ "principal": { "display_name": string }, "workspaces": [{ "workspace_id": string, "display_name": string, "role": "owner" | "member" }] }`.
    PostgreSQL discovery is ordered by `display_name`, then `workspace_id`.
  - `GET /chat/sessions?workspace_id=<non-empty string>` returns a bare array,
    not `{ "sessions": [...] }`. Each item is
    `{ "session_id": string, "workspace_id": string, "title": string,
    "last_preview": string | null, "updated_at": string | null }`.
    PostgreSQL returns newest `updated_at` first. The in-memory development
    fallback currently has no deterministic ordering and may omit `updated_at`;
    that parity gap must be resolved before this is called a stable contract.
  - `GET /chat/sessions/{session_id}` takes no `workspace_id` query parameter.
    It returns the summary fields above plus `summary: string | null` and
    `turns: [{ "role": "user" | "assistant", "content": string }]`.
    The endpoint finds the owned session, then revalidates access to the
    session's stored workspace. A session that is absent or belongs to another
    user is deliberately returned as `404`.
  - Turn timestamps are **not** present in the current response, despite being
    stored in PostgreSQL. Adding them requires a backend schema/query/test
    change. The store also enforces bounded raw history (currently 10 turns).
- **Action requested:** Parse the bare session array for the current
  implementation. Do not depend on turn timestamps or in-memory ordering until
  an approved API change provides them. Backend will add the response schemas
  to the architecture document after the contract gaps below are approved.
- **Supersedes / follow-up:** Responds to the 2026-08-28 FP-04 schema request.

## 2026-08-28 — Current error behavior is not yet a stable browser contract

- **From:** Backend
- **To:** Frontend
- **Type:** API change
- **Status:** Needs review
- **Affected contract/files:** Workspace and chat/session endpoints; `docs/frontend_architecture.md`
- **Message:** Current FastAPI responses use `{ "detail": string }`, with no
  stable machine-readable code. `401` is emitted only in office auth mode when
  the trusted gateway identity header is absent; `403` means the principal is
  not authorized for the requested workspace; `404` hides absent or
  other-user session IDs; and `422` is FastAPI request/query validation.
  Unexpected synchronous chat-provider failures currently return `502`, but
  its `detail` can expose upstream exception text and must not be treated as a
  browser-safe message.
- **Action requested:** Product/backend approval is required before introducing
  a stable error code/message envelope or changing the `502` response. Until
  then, treat `403` as refresh-workspaces-and-recover, `404` as
  unavailable-session, and all other non-success responses as a generic
  recoverable failure without rendering `detail`.
- **Supersedes / follow-up:** Responds to the 2026-08-28 error-semantics proposal.

## 2026-08-27 — Workspace authorization validation remains pending

- **From:** Backend
- **To:** Frontend
- **Type:** Validation
- **Status:** Needs review
- **Affected contract/files:** `GET /workspaces`; workspace-scoped chat and session routes
- **Message:** NP-05 implementation and isolated tests are complete. Apply the
  SQL migrations/local seed and validate the normal local stack before using
  workspace discovery against a live development database.
- **Action requested:** Keep FP-04 implementation proxy-only until the backend
  reports validation complete; then exercise the discovery and selected
  workspace flow.
- **Supersedes / follow-up:** See `../work_current_phase.md` CW-06.

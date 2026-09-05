# Backend → Frontend

Add newest entries directly below this heading. Backend owns writing this file;
the frontend reads it and records responses in `frontend_to_backend.md`.

## 2026-09-05 — Optional chunking-profile query contract published

- **From:** Backend
- **To:** Frontend
- **Type:** API change
- **Status:** Implemented
- **Affected contract/files:** `POST /chat`, `POST /chat/stream`,
  `docs/frontend_architecture.md`
- **Message:** Chat requests may include optional `chunking_profile` (a
  configured name using letters, numbers, `_`, or `-`) to retrieve only from a
  non-default chunking experiment. Omission is fully backward compatible and
  selects `default`, preserving the current UI behavior. Unknown profiles are
  rejected as invalid requests. Ingestion also supports `chunking_profile` and
  `dry_run`; those are backend/operator controls and require no UI work.
- **Action requested:** None. Keep omitting `chunking_profile` until an
  experiment-selection UI is separately approved.
- **Supersedes / follow-up:** Introduced by NP-08; local PostgreSQL migration
  validation remains before phase closure.

## 2026-09-03 — Empty session-list workspace ID validation fixed

- **From:** Backend
- **To:** Frontend
- **Type:** Bug fix
- **Status:** Resolved
- **Affected contract/files:** `GET /chat/sessions?workspace_id=<non-empty text>`; `src/app/api/routers/chat.py`
- **Message:** Confirmed and fixed. `workspace_id` now has an explicit
  `min_length=1` request constraint, so `GET /chat/sessions?workspace_id=`
  returns the documented `422` safe envelope:
  `{ "code": "invalid_request", "message": "The request is invalid." }`.
  Unauthorized non-empty IDs continue to return `403
  workspace_access_denied`.
- **Action requested:** No frontend change is required; retain the documented
  invalid-request handling if a malformed URL is ever reached.
- **Supersedes / follow-up:** Resolves the 2026-09-03 live API validation bug.

## 2026-09-01 — FP-06 SSE wire contract published

- **From:** Backend
- **To:** Frontend
- **Type:** API change
- **Status:** Implemented
- **Affected contract/files:** `POST /chat/stream`; `docs/frontend_architecture.md`
- **Message:** FP-06 is unblocked. The canonical contract now defines the POST
  request, response headers, named JSON `answer`, `meta`, `error`, and `done`
  events, terminal ordering, exact `SourceReference` payload, safe error
  example, and AbortController/user-retry semantics. The backend now emits
  named `answer` events as `{ "delta": string }` and JSON `done` payloads;
  never parse the former unnamed plain-text chunks.
- **Action requested:** Implement streaming with `fetch` plus an SSE parser,
  append `answer.delta` verbatim, and commit session/citations only from
  `meta`. Use explicit AbortController cancellation and no automatic retry.
- **Supersedes / follow-up:** Resolves the 2026-08-31 FP-06 blocker.

## 2026-08-31 — FP-06 streaming-contract requirements approved

- **From:** Backend
- **To:** Frontend
- **Type:** Approval
- **Status:** Approved
- **Affected contract/files:** `POST /chat/stream`; `docs/frontend_architecture.md`
- **Message:** The FP-06 requirements are approved: incremental rendering,
  explicit cancellation, grounded state and citations, safe code-specific
  post-start failures, and user-initiated retry only. The backend will provide
  the canonical request, SSE event/source, completion, and cancellation
  semantics requested in the frontend handoff before FP-06 is unblocked. Do
  not infer an `answer` payload shape from the current unnamed SSE `data:`
  chunks.
- **Action requested:** Keep FP-06 blocked until the concrete wire contract
  and JSON examples are published in `docs/frontend_architecture.md`; then
  implement against that documented contract.
- **Supersedes / follow-up:** Responds to the 2026-08-31 FP-06 clarification
  request. This approval does not itself change the existing wire contract.

## 2026-08-29 — NP-05 closed

- **From:** Backend
- **To:** Frontend
- **Type:** Validation
- **Status:** Resolved
- **Affected contract/files:** Workspace discovery and session authorization
- **Message:** NP-05 is complete. The migration/seed and live API validation
  remain confirmed, and the restored embedding service allowed the updated
  documentation and shared handoff records to be indexed successfully.
- **Action requested:** None. Continue frontend work through the approved
  backend contract; submit any new requirement through this handoff.
- **Supersedes / follow-up:** Resolves the documentation-indexing blocker.

## 2026-08-29 — Documentation indexing blocked; FP-04 validation unaffected

- **From:** Backend
- **To:** Frontend
- **Type:** Blocker
- **Status:** Blocked
- **Affected contract/files:** NP-05 document indexing only
- **Message:** The configured Ollama embedding endpoint could not be reached,
  so the approved documentation reindex returned `500` and wrote no new
  documents. PostgreSQL migration/authorization validation and the FP-04 API
  contract remain complete and unaffected.
- **Action requested:** None for FP-04. Backend will rerun the idempotent
  documentation index after the configured embedding service is available.
- **Supersedes / follow-up:** NP-05 cannot close until this final indexing step
  succeeds.

## 2026-08-29 — Live-stack validation complete

- **From:** Backend
- **To:** Frontend
- **Type:** Validation
- **Status:** Resolved
- **Affected contract/files:** PostgreSQL schema; `GET /workspaces`; workspace-scoped session routes
- **Message:** The configured PostgreSQL service is healthy on PostgreSQL
  16.14 with pgvector 0.8.3. Migrations `001_baseline` and
  `002_workspace_authorization` plus the local seed are applied. The local
  `local-dev` principal owns the `local` workspace. The configured FastAPI app
  was validated against that database: health and workspace discovery return
  `200`, session list/detail return the documented timestamped payloads,
  unauthorized workspace access returns the safe `403` envelope, and an
  unknown session returns the safe `404` envelope. Temporary validation rows
  were removed.
- **Action requested:** FP-04 may now perform approved local proxy integration
  against this backend. Report any browser-observable discrepancy through the
  frontend-to-backend handoff.
- **Supersedes / follow-up:** Resolves the 2026-08-29 live-stack blocker.

## 2026-08-29 — Live-stack validation blocked by local environment

- **From:** Backend
- **To:** Frontend
- **Type:** Blocker
- **Status:** Blocked
- **Affected contract/files:** PostgreSQL migrations/local seed; `GET /workspaces`; workspace-scoped session routes
- **Message:** FP-04 contract alignment is confirmed. The remaining NP-05
  validation requires a local PostgreSQL/pgvector stack, but this environment
  has neither Docker nor `psql`, and `localhost:5432` is not accepting
  connections. No migration, seed, Uvicorn process, model service, or database
  request was started.
- **Action requested:** Keep FP-04 proxy-only until the backend can access an
  approved local PostgreSQL stack. Once available, backend will apply the
  idempotent migrations/seed and validate workspace discovery and session
  ownership through the normal API.
- **Supersedes / follow-up:** Responds to the 2026-08-29 frontend validation request; the implementation contract remains complete.

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

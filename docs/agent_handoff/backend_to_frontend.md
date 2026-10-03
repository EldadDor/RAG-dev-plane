# Backend → Frontend
## 2026-10-03 — NP-23 profile/preferences implemented; offline validated

- **From:** Backend
- **To:** Frontend
- **Type:** API change / Validation
- **Status:** Implemented — G3 approved; push to default branch awaits destination review; live rollout not performed
- **Affected contract/files:** GET /account/profile; GET/PATCH /account/preferences; docs/frontend_architecture.md; docs/account_preferences_api_design.md; migration 008.
- **Message:** G2-approved read-only profile and strict recent_chat_limit preferences are implemented. Public contract includes trusted display name/nullable email, fresh memberships, supported read/update fields, 10/20/50/100 limits (default 10), per-principal storage and explicit persistence lifetime. PostgreSQL is durable; local Qdrant process storage resets on restart; gateway/Qdrant preferences return account-specific unavailable errors. Logout is explicitly unsupported pending NP-24. All account successes/errors have private/no-store headers. Session list and retention semantics remain unchanged.
- **Validation:** Full provider-free offline suite: 206 passed. Coverage includes invalid/coerced values, defaults without writes, update/reload, principal isolation, local identity spoof attempts, missing gateway auth, stale membership removal, unavailable/closed storage, safe errors/privacy headers, shared lifespan stores, parameterized SQL and startup table/ledger requirements. Scoped whitespace checks passed. Mocked SQL is not real durability validation. No real SQL/API/browser/model calls, migration execution, service operations or commit.
- **Action requested:** FP-16 profile/settings and FP-15 preferences may integrate against the published schema once the updated backend is deployed. Operator must apply migration 008 before restarting upgraded PostgreSQL writers; live rollout requires its own authorization. Kotlin parity remains with its owner.
- **Supersedes / follow-up:** Supersedes the preceding NP-23 design-only availability status. NP-24 still owns logout integration. G3 delivery and G4 closure remain pending.

## 2026-10-03 — NP-23 profile/preferences design awaiting G2

- **From:** Backend
- **To:** Frontend
- **Type:** API change / Clarification
- **Status:** Proposed — needs review
- **Affected contract/files:** Proposed GET /account/profile and GET/PATCH /account/preferences; docs/account_preferences_api_design.md; NP23-01.
- **Message:** NP-23 G1 intake is approved. Proposed read-only trusted display name/email and current workspace memberships; strict recent_chat_limit 10/20/50/100, default 10, per principal across workspaces. PostgreSQL persistence is durable; local Qdrant process storage is explicitly temporary; gateway/Qdrant preferences are unavailable. Capability fields disclose read/update support and persistence. Logout stays unsupported until NP-24 establishes ownership/integration. Existing session-list API remains uncapped. Detailed shapes, safe errors, migration 008 and rollback are in the design proposal.
- **Action requested:** Review the proposed capability/schema shape for FP-16. Structural backend implementation awaits this task's G2 approval; these routes are not available yet.
- **Supersedes / follow-up:** Updates NP-23's candidate status in the earlier FP-15–FP-17 intake response. Existing published frontend contract is unchanged; no live services, migration execution or frontend implementation occurred.

## 2026-10-03 — NP-22 approved and closed

- **From:** Backend
- **To:** Frontend
- **Type:** Validation
- **Status:** Completed
- **Affected contract/files:** GET /chat/sessions; docs/frontend_architecture.md; backend phase records.
- **Message:** User approved the reviewed implementation. NP-22 is committed as `983e8d6` and closed; the preceding readiness entry remains the capability/validation reference. FP-15 can use the uncapped list and published deterministic ordering. NP-23–NP-26 remain backlog candidates.
- **Action requested:** None for backend implementation; frontend integration and Kotlin parity remain with their owners.
- **Supersedes / follow-up:** Supersedes the uncommitted status in the preceding NP-22 readiness entry. No additional tests or live operations were required for this documentation-only closure; prior 18-test evidence remains applicable.

## 2026-10-03 — NP-22 recent-chat contract and fallback fixes ready

- **From:** Backend
- **To:** Frontend
- **Type:** Clarification / Validation
- **Status:** Implemented and offline validated; live integration not run
- **Affected contract/files:** GET /chat/sessions; docs/frontend_architecture.md; conversation_store.py.
- **Message:** Session listing remains an uncapped bare array of owned, authorized-workspace active sessions, one row per session ID. Both stores now order updated_at descending, nulls last, then session_id ascending with ordinal/case-sensitive comparison. No limit/cursor request parameters were introduced. FP-15 may apply default 10 and choices 10/20/50/100 locally after ID deduplication; different IDs with similar titles remain valid distinct chats. In-memory rename/archive now persist guarded updates under lock; archived sessions disappear from subsequent list/detail requests. List results no longer expose mutable stored metadata.
- **Validation:** 18 provider-free focused tests passed, including 105 sessions, ID uniqueness, timestamp ties/nulls, ownership/workspace boundaries, rename/archive through the API and mocked PostgreSQL query order. Scoped whitespace checks passed. No live SQL/API/browser/model calls, full suite or service operations ran. Apparent frontend duplicates were not reproduced and no cause is claimed. PostgreSQL query execution remains live-unverified.
- **Action requested:** Integrate FP-15 against the published existing response shape. Kotlin owner should apply equivalent ordering/fallback semantics when coordinating runtime parity; this repository change does not update Kotlin.
- **Supersedes / follow-up:** Updates NP-22 readiness in the earlier 2026-10-03 intake response. NP-23–NP-26 readiness is unchanged. Implementation remains uncommitted for review.

## 2026-10-03 — FP-15–FP-17 reviewed; backend tasks NP-22–NP-26 recorded

- **From:** Backend
- **To:** Frontend
- **Type:** Clarification / Requirement intake
- **Status:** Review and task creation complete; capability implementation not activated
- **Affected contract/files:** docs/next_phase.md; docs/work_current_phase.md; existing docs/frontend_architecture.md contract.
- **Message:** Reviewed the new account/document/recent-chat requirements and created backend phases with design, implementation and acceptance subtasks: NP-22 recent-chat uniqueness/order/retrieval; NP-23 profile/preferences; NP-24 logout ownership/integration; NP-25 whole-document overviews; NP-26 trustworthy counts and complete single-page/single-slide previews. Task dependencies, approval boundaries, affected areas and publication gates are recorded in the backend backlog.
- **Recent-chat readiness:** Current GET /chat/sessions returns an uncapped bare array filtered by owner, authorized workspace and non-archived state; neither store expands sessions into turns/chunks. Apparent UI duplicates remain unconfirmed. FP-15 can deduplicate by session_id and cap display at 10/20/50/100 with the existing request. Both implementations sort updated_at descending without an explicit session-ID tie-breaker; NP-22 covers deterministic ordering and any approved bounded retrieval extension. Review also found that in-memory rename/archive mutate copied detail metadata rather than persist changes; this is a separate confirmed parity defect included in NP-22. No live duplicate investigation was performed.
- **Capability readiness:** Profile/preferences/logout and overview/full-page preview endpoints are not available. Do not invent routes or interpret citation assets as complete previews. NP-24 needs gateway/identity-owner input; fixed development identity cannot be logged out by clearing UI data. NP-25/NP-26 need generation/rendering/source-lifecycle decisions before implementation. Approved contracts must be published with examples in frontend_architecture.md before integration; that contract is unchanged by this intake.
- **Action requested:** Use existing session/SSE behavior for FP-14 and the existing uncapped list for FP-15. Keep FP-16/FP-17 dependent on backend contract readiness. No frontend implementation activation or live validation is implied by this response.
- **Supersedes / follow-up:** Responds to the 2026-10-03 FP-15–FP-17 entry in frontend_to_backend.md. Prior entries remain preserved. Kotlin contract parity should be coordinated with its owner after approval.
- **Validation:** Static source/contract review and scoped documentation whitespace checks only; no application tests, live API/browser/model/database calls, migrations or service operations.


Add newest entries directly below this heading. Backend owns writing this file;
the frontend reads it and records responses in `frontend_to_backend.md`.

## 2026-10-02 — NP-21 PowerPoint ingestion and document type

- **From:** Backend
- **To:** Frontend
- **Type:** API extension / parser feature
- **Status:** Implemented and locally validated
- **Affected contract/files:** Existing `POST /ingest`, document discovery and
  source citations; `docs/frontend_architecture.md`; `docs/powerpoint_ingestion.md`.
- **Message:** `.pptx` files now use the normal ingestion lifecycle. Extract
  text/grouped shapes, tables, cached charts, speaker notes and image assets;
  chunk within slides. Catalog `document_type` adds `powerpoint`; citation `page`
  represents a one-based slide number. Image assets keep the existing response
  and authorization flow. SmartArt text and object previews are best effort;
  unavailable/unsupported content is recorded in private metadata. No OCR or
  slide rendering is performed. Migration 007 is applied locally and the API
  exposes the new type. Real SQL fixtures passed with synthetic embeddings and
  complete fixture rollback; no real model calls ran.
- **Action requested:** Add `powerpoint` to FP-12 type label/color configuration,
  retaining Unknown/Other fallback. Use slide-number wording where `.pptx`
  citations are identifiable. No new upload/ingestion frontend workflow is
  requested. Browser validation remains frontend-owned.
- **Evidence:** `docs/phase_qa/NP21-live-powerpoint-ingestion.json` and
  `tests/test_powerpoint_loader.py`; full behavior/limits documented in
  `docs/powerpoint_ingestion.md`.
- **Supersedes / follow-up:** Extends NP-20's canonical type list; existing
  response shapes and other parser behavior remain compatible.

## 2026-10-02 — NP-20 local rollout validated; FP-10–FP-12 unblocked

- **From:** Backend
- **To:** Frontend
- **Type:** API validation / integration handoff
- **Status:** Implemented, enabled and live-validated on the configured local stack
- **Affected contract/files:** `GET /workspaces/{workspace_id}/documents`;
  `docs/frontend_architecture.md`; FP-10, FP-11, FP-12.
- **Message:** Migration 006 is applied and metadata is certified for 132
  document publications across two model profiles, with 2,886 scoped chunks
  and zero SQL count mismatches. Recovered 568 legacy ID aliases from exact
  source-record matches. Preserved 32 unscoped legacy vectors, excluded with
  warnings. Unknown historical ingestion times remain null. Local listing is
  enabled; health/readiness and documents return 200. Full offline suite:
  **134 passed**. Live HTTP validated limits 1/25/100, stable traversal, counts,
  safe fields/headers and invalid requests. Real PostgreSQL fixtures validated
  two principals/workspaces, revoked access, cursor binding and changed-list
  409, zero chunks, unchanged/failed/changed replacement, synthetic warming and
  scoped directory cleanup. Fixtures rolled back; no real model calls ran.
- **Action requested:** Proceed with FP-10 against the canonical contract, then
  FP-11/FP-12 badges. Omit profile parameters initially to match chat defaults.
  Show null ingestion time as unavailable history; treat exact count 0 as valid.
  Restart page one on 409, clear protected data on 401/403, and expose retry on
  503. Record browser integration results in the frontend-owned handoff.
- **Evidence:** `docs/phase_qa/NP20-live-document-catalog.json` and
  `docs/phase_qa/NP20-reconciliation.json`; repeatable local validation runner
  `scripts/validate_document_catalog.py`. Current-state snapshot: `afee99c`.
- **Supersedes / follow-up:** Resolves the implementation checkpoint's local
  rollout gate below. Frontend browser validation remains frontend-owned.

## 2026-10-02 — NP-20 document metadata API implemented; rollout pending

- **From:** Backend
- **To:** Frontend
- **Type:** API implementation / validation status
- **Status:** Implemented and offline-validated; migration/backfill/enablement and live validation pending
- **Affected contract/files:** `GET /workspaces/{workspace_id}/documents`;
  `docs/frontend_architecture.md`; migration 006; FP-10, FP-11, FP-12.
- **Message:** The route, safe typed metadata, exact scoped counts, resolved
  profile names, signed 15-minute cursors, stable null-last keysets,
  `409 document_list_changed`, and `503 document_list_unavailable` are implemented.
  New PostgreSQL writers atomically publish vectors/metadata/revisions, preserve
  unchanged ingestion times, support zero chunks, and coordinate warming and
  scoped cleanup. Model-owned asset references preserve other profiles' images.
  The offline suite passed **132 tests**; operator CLI help checks also passed.
  No live database/model/browser requests or migrations ran.
- **Action requested:** Review the implemented contract in
  `docs/frontend_architecture.md`. Keep frontend integration pending the local
  rollout confirmation: apply migration 006 before updated PostgreSQL startup,
  review/apply `scripts/reconcile_document_catalog.py`, enable the route, and
  complete live API acceptance. The route deliberately returns safe 503 until
  configuration enablement and database readiness are both satisfied.
- **Supersedes / follow-up:** Supersedes the earlier same-day design-only status.
  Rollout instructions are in `database/README.md`; the current backend phase
  records retain the live validation gate. No frontend files changed.

## 2026-10-02 — FP-10 through FP-12 metadata API design published

- **From:** Backend
- **To:** Frontend
- **Type:** Design response / proposed API
- **Status:** Design complete; endpoint not implemented or live-validated
- **Affected contract/files:** `docs/recent_document_metadata_api_design.md`;
  future `GET /workspaces/{workspace_id}/documents`; FP-10, FP-11, FP-12.
- **Message:** NP-19 defines safe title/filename, existing opaque `doc_id`,
  canonical document type, nullable historical `last_ingested_at`, and exact
  `indexed_chunk_count` for one resolved model/chunking scope. Browser omission
  uses the same configured profiles as chat. Default page size is 25, maximum
  100; newest-known ingestion first with stable ID ordering and unknown times
  last. Revision-checked keyset pagination returns `409 document_list_changed`
  when records change, requiring a fresh first page. Unchanged skips preserve
  time/count; failed replacement retains previous success; zero-chunk successful
  documents appear with count 0; warming preserves source recency. Current
  storage needs a per-model metadata projection and publication coordination.
  First implementation targets PostgreSQL; unsupported/uninitialized catalogs
  return safe `503 document_list_unavailable` rather than misleading empty data.
- **Action requested:** Review the proposed fields and UI recovery/refresh
  behavior in the design. Keep FP-10–FP-12 pending implementation and publication
  of validated examples in `frontend_architecture.md`; do not integrate the
  proposed route as though it already exists. Type/size colors remain frontend
  configuration, and no document-selection retrieval behavior is introduced.
- **Supersedes / follow-up:** Responds to the 2026-10-02 recent-document metadata
  request. Proposed NP-20 owns implementation, migration/backfill, validation,
  and authoritative contract publication after implementation approval.

## 2026-09-13 — NP-17 optional model-profile contract implemented

- **From:** Backend
- **To:** Frontend
- **Type:** API change
- **Status:** Implemented and live-validated
- **Affected contract/files:** `POST /chat`, `POST /chat/stream`, `POST /ingest`
- **Message:** Requests may include optional `model_profile`, using the same
  letters/numbers/underscore/hyphen naming rule as `chunking_profile`. Omission
  selects the server-configured `MODEL_PROFILE` and preserves the existing UI.
  A named profile resolves its embedding provider/model, dimension, cache
  namespace, and isolated vector table. Unknown or non-ready profiles are
  rejected; `/chat` returns the standard `422 invalid_request` envelope.
- **Action requested:** None. Continue omitting `model_profile`. A visible
  selector remains a separately approved product feature.
- **Validation:** Omitted profile, explicit `bge-m3`, and explicit historical
  `default` all returned grounded responses; an unknown profile returned the
  standard `422 invalid_request` envelope.

## 2026-09-12 — NP-13 through NP-15 live validation complete

- **From:** Backend
- **To:** Frontend
- **Type:** Validation
- **Status:** Resolved
- **Affected contract/files:** `POST /chat`, `POST /chat/stream`,
  `GET /workspaces/{workspace_id}/assets/{asset_id}`,
  `docs/frontend_architecture.md`
- **Message:** Migration 004 is applied. The live local browser validated a
  grounded Hebrew Word result: the `10MB` passage from
  `general_errors_handling.docx` returned its related PNG screenshot in the
  Related source images panel. The authorized asset URL served the image and
  the existing frontend rendering handled it.
- **Action requested:** None. NP-15-FE is complete.
- **Supersedes / follow-up:** Supersedes the 2026-09-10 request for the live
  Word/image browser checklist.

## 2026-09-10 — Proposed image-bearing source citations

- **From:** Backend
- **To:** Frontend
- **Type:** API change
- **Status:** Implemented; live validation pending
- **Affected contract/files:** `POST /chat`, `POST /chat/stream`, proposed
  `GET /workspaces/{workspace_id}/assets/{asset_id}`,
  `docs/document_image_support_plan.md`
- **Message:** Proposed NP-13 through NP-15 add `.docx` ingestion and related
  image assets. A source may gain an optional `assets` array containing safe
  metadata and an application-issued content URL. The SSE sequence does not
  change, old payloads without assets remain valid, and the frontend would
  render cited images in the Sources experience rather than trusting image
  Markdown generated in the answer text.
- **Action requested:** Run the live Word/image browser checklist after the
  PostgreSQL migration is applied and the updated API is restarted.
- **Supersedes / follow-up:** Approved by the user on 2026-09-11; the contract
  is now authoritative in `docs/frontend_architecture.md`.

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
- **Supersedes / follow-up:** Introduced by NP-08. PostgreSQL migration and
  default-profile backfill validation completed 2026-09-05.

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

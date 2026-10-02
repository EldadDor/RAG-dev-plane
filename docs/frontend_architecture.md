# Frontend Architecture

## Product Shape

React + TypeScript + Vite SPA: top workspace selector, central streaming chat and citations, and a right-side per-user recent-chat pane. It is locally self-served by Vite and deployed as static assets through Nginx. Ingestion/admin UI is out of scope.

## Backend Contract

- `GET /workspaces` returns the current principal's PostgreSQL-authorized workspaces. Workspace IDs remain text values. Its success payload is:

  ```json
  {
    "principal": { "display_name": "Ada Lovelace" },
    "workspaces": [
      { "workspace_id": "platform", "display_name": "Platform", "role": "owner" }
    ]
  }
  ```

  `role` is either `owner` or `member`. Workspaces are ordered by `display_name`, then `workspace_id`.
- `POST /chat` returns a completed grounded response.
- `POST /chat/stream` is SSE. Its complete wire contract, including the named JSON events and cancellation semantics, is below.
- `GET /chat/sessions?workspace_id=<non-empty text>` lists the current user's active sessions. It returns a bare JSON array, newest `updated_at` first:

  ```json
  [
    {
      "session_id": "9b1de4f0-0d4e-4b92-a3d7-0a72ea62b7d4",
      "workspace_id": "platform",
      "title": "Release process",
      "last_preview": "The release process is…",
      "updated_at": "2026-08-29T00:45:17.000000Z"
    }
  ]
  ```

- `GET /chat/sessions/{id}` loads an owned active session and requires no `workspace_id` query parameter. The backend finds the stored session workspace and revalidates access. It returns the summary fields above plus `summary` and bounded, chronological raw turns:

  ```json
  {
    "session_id": "9b1de4f0-0d4e-4b92-a3d7-0a72ea62b7d4",
    "workspace_id": "platform",
    "title": "Release process",
    "last_preview": "The release process is…",
    "updated_at": "2026-08-29T00:45:17.000000Z",
    "summary": "The discussion covered the release checklist.",
    "turns": [
      { "role": "user", "content": "What is the checklist?", "created_at": "2026-08-29T00:43:00.000000Z" },
      { "role": "assistant", "content": "The checklist is…", "created_at": "2026-08-29T00:43:02.000000Z" }
    ]
  }
  ```

  Timestamps are RFC 3339 UTC datetimes. `role` is `user` or `assistant`. Raw turns retain the configured bounded maximum (10 by default).
- `PATCH /chat/sessions/{id}` accepts `{ "title": "…" }` and returns `{ "ok": true }`. `DELETE /chat/sessions/{id}` archives the session and returns `204 No Content`. Both act only on the current user's session.
- The backend derives office ownership from configurable gateway-validated identity headers and local ownership from a fixed server-side development subject. It never accepts a browser user ID.
- The backend revalidates workspace membership for every workspace-scoped chat and session operation. A client-provided workspace ID is a requested scope, not authorization.

## Error Contract

All non-streaming API failures use this safe JSON envelope; clients must not render server internals:

```json
{ "code": "workspace_access_denied", "message": "You do not have access to this workspace." }
```

| Status | Code | Client meaning |
| --- | --- | --- |
| 401 | `authentication_required` | The trusted gateway identity is absent; prompt for sign-in/reload through the normal authentication path. |
| 403 | `workspace_access_denied` | The requested workspace is no longer available; refresh workspace discovery and recover selection. |
| 404 | `resource_not_found` | The session/resource is unavailable; remove it from the current UI state. Ownership mismatches are deliberately indistinguishable from absence. |
| 422 | `invalid_request` | The browser sent an invalid path, query, or body; correct client state rather than displaying server detail. |
| 502 | `upstream_unavailable` | The answer provider is temporarily unavailable; offer retry. |
| 500 | `internal_error` | An unexpected backend failure occurred; offer retry. |

The envelope is also the `data` payload of a post-start SSE `error` event. A failure that is detected before SSE headers are sent uses the ordinary HTTP status/envelope instead.

## Recent Document Metadata Contract (NP-20)

Implemented and locally live-validated on 2026-10-02. Migration 006 is applied,
the catalog is reconciled/certified, and the local API has listing enabled.
Frontend FP-10 integration and FP-11/FP-12 badges may proceed against this
contract. Acceptance evidence is in `phase_qa/NP20-live-document-catalog.json`
and `phase_qa/NP20-reconciliation.json`; the offline suite passes 134 tests.
Historical ingestion timestamps remain null when their provenance is unknown.
See `recent_document_metadata_api_design.md` for the design rationale and
`../database/README.md` for rollout commands.

```http
GET /workspaces/local/documents?limit=25
Accept: application/json
```

This is a relative proxy route with gateway-derived identity and membership
checks on every request/page. Owner and member see the same workspace corpus.
There are no provider calls or source-filesystem reads on this route.

Query fields: `limit` defaults to 25 (integer 1–100), optional `cursor` is an
opaque non-empty token up to 4096 characters, and optional `model_profile` and
`chunking_profile` use the same configured-name rule as chat. Frontend initially
omits both profile fields; omission resolves through the same configured model
and chunking defaults as chat. The response always names the resolved scope.
Counts cover exactly that scope, never a sum of profiles or retrieved citations.

```json
{
  "workspace_id": "local",
  "scope": { "model_profile": "bge-m3", "chunking_profile": "default" },
  "items": [
    {
      "doc_id": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "title": "טיפול בשגיאות כלליות",
      "file_name": "general_errors_handling.docx",
      "document_type": "word",
      "last_ingested_at": "2026-10-02T08:30:15.123456Z",
      "indexed_chunk_count": 42
    }
  ],
  "page": {
    "limit": 25,
    "has_more": false,
    "next_cursor": null,
    "list_revision": "18",
    "generated_at": "2026-10-02T08:31:00.000000Z"
  }
}
```

Values above are illustrative. Authorized empty scopes return 200 with
`items: []`, `has_more: false`, and `next_cursor: null`.

- `doc_id` is the existing opaque citation document ID, scoped to its workspace.
  Re-ingestion of that identity keeps one item; a renamed or differently spelled
  source path can have a new ID. It is not a download or retrieval-filter token.
- `title` and basename-only `file_name` are non-empty sanitized display text
  limited to 300 and 255 Unicode code points respectively. No path, content,
  raw metadata, source hash, provider detail, or storage identifier is exposed.
- Canonical `document_type` values are `word`, `pdf`, `markdown`, `html`, `text`,
  `code`, and `unknown`. Code includes supported configuration files such as
  JSON/YAML/TOML/SQL. Frontend supplies text labels and configurable type colors
  and tolerates future types with an Unknown/Other fallback.
- `indexed_chunk_count` is an exact non-negative integer, including 0. It is
  bounded by JavaScript's safe-integer maximum. Zero-chunk successful documents
  are visible. Size thresholds/colors are frontend configuration; no size/color
  field is returned. Missing/invalid counts in a malformed response are Unknown,
  never interpreted as 0 or Small.
- `last_ingested_at` is a UTC RFC 3339 timestamp for this scope's last successful
  changed ingestion, or null when historical provenance is unavailable. Show
  null as "Ingestion time unavailable". Unchanged skips keep the prior count and
  time. Warming preserves source recency rather than making old content new.
  Pending/failed first ingestions are absent; failed replacement retains the
  previous successful version. Dry runs do not affect the list.
- Order is newest known `last_ingested_at` first, unknown times last, with
  bytewise `doc_id` ascending as the tie-breaker. All current documents are
  reachable; there is no hidden time window or total-record cap.

Follow `page.next_cursor` while `has_more` is true, retaining the same effective
workspace/profile scope and limit. Tokens expire after 15 minutes and are bound
to the current principal. `list_revision` is an opaque decimal string. Pagination
is revision-checked: a list mutation between pages returns safe 409 rather than
silently skipping/duplicating rows. `generated_at` is response time, not an
ingestion timestamp or historical snapshot guarantee.

Errors use the existing `{ code, message }` envelope. Existing 401/403/422/500
handling applies. Unknown/non-ready explicit profiles and malformed, tampered,
cross-subject or mismatched-scope cursors return 422. New cases:

| Status | Code | Frontend recovery |
| --- | --- | --- |
| 409 | `document_list_changed` | Restart page one and replace accumulated records; allow one automatic restart for the action, then offer Refresh if changes continue. Also used for expired valid tokens or changed omitted-profile defaults. |
| 503 | `document_list_unavailable` | Catalog disabled, not reconciled, unsupported (including Qdrant-only), configured profile unavailable, or database unavailable. Show retry while keeping chat usable. |

```json
{ "code": "document_list_changed", "message": "The document list changed. Reload it to continue." }
```

```json
{ "code": "document_list_unavailable", "message": "The document list is temporarily unavailable." }
```

Success and errors have `Cache-Control: private, no-store` and
`Vary: Cookie, Authorization`. The gateway must prevent caching by its trusted
identity mechanism too. Render application copy based on code, never raw server
detail. Clear protected records on 401/403; refresh workspace discovery on 403.

Load page one on valid workspace selection. Clear old workspace records
immediately and abort/ignore stale responses. Offer Refresh and refresh on
returning to the documents panel; initial delivery requires no polling. Append
only pages of the same scope/revision. If refresh/load-more fails, existing
authorized records may remain visibly stale with retry controls. Support
loading/empty/error, Hebrew/RTL, long names, narrow layouts, keyboard access,
screen-reader labels, and separate text badges for type and size. Document
selection must not silently restrict retrieval or invent a content-download URL.

## Streaming Wire Contract

Use `fetch`, not `EventSource`: the endpoint is a `POST` with a JSON body.
Send `Accept: text/event-stream` and `Content-Type: application/json`. The API
returns `200`, `Content-Type: text/event-stream; charset=utf-8`,
`Cache-Control: no-cache`, and `X-Accel-Buffering: no` once streaming has
started. Treat an HTTP response that is not `2xx` as the normal JSON error
contract; do not attempt to parse it as SSE.

### Request

```http
POST /chat/stream HTTP/1.1
Accept: text/event-stream
Content-Type: application/json

{
  "question": "How do I roll back a release?",
  "workspace_id": "platform",
  "session_id": "9b1de4f0-0d4e-4b92-a3d7-0a72ea62b7d4",
  "top_k": 5,
  "include_debug": false
}
```

`question` is required and non-empty. `workspace_id` is optional only when the
server has a configured default workspace. Omit `session_id` to create a new
chat; pass the `session_id` received in `meta` for the next turn. `top_k` is
optional (`1`–`20`) and `include_debug` defaults to `false`; production UI
should leave it false. It may optionally send a configured `chunking_profile`
to query an isolated
chunking experiment. Omitting it retains the existing default-profile behavior.
The same requests may optionally send `model_profile` to select a provisioned,
ready embedding/index profile. Omission selects the backend's configured
`MODEL_PROFILE`; the current frontend should continue to omit it.

### Events

Every `data:` field is exactly one JSON value. Parse it with `JSON.parse` only
after combining all physical SSE `data:` lines for that event. Events arrive
in this order: zero or more `answer`, exactly one terminal `meta` or `error`,
then exactly one `done`. Unknown event names must be ignored for forward
compatibility.

```text
event: answer
data: {"delta":"To roll back "}

event: answer
data: {"delta":"a release, run `deploy rollback`."}

event: meta
data: {"session_id":"9b1de4f0-0d4e-4b92-a3d7-0a72ea62b7d4","grounded":true,"sources":[{"doc_id":"release-guide","chunk_id":"release-guide:14","source_path":"docs/releases.md","title":"Release guide","page":null,"section":"Rollback","score":0.92,"snippet":"Run deploy rollback to restore the prior release.","assets":[]}],"debug":null}

event: done
data: {"reason":"completed"}

```

- `answer` has `{ "delta": string }`. Append `delta` verbatim; it may contain
  spaces, newlines, or an empty string. It contains answer text only, never
  citations or final state.
- `meta` has `{ "session_id": string, "grounded": boolean, "sources":
  SourceReference[], "debug": object | null }`. It is the authoritative
  completion payload: save `session_id`, replace the source drawer with
  `sources`, and use `grounded` rather than inferring grounding from sources.
  `debug` is `null` unless the request opted in.
- Each `SourceReference` has an `assets` array. It is empty for ordinary text
  citations. Image entries contain `asset_id`, `media_type`, nullable
  `width`/`height`, nullable `alt_text`/`caption`, and nullable `content_url`.
  Older payloads that omit `assets` are interpreted as an empty array.
- A non-null `content_url` is an application-issued relative route such as
  `/workspaces/local/assets/<asset-id>`. Render only these URLs, load them
  lazily, and retain the source path/snippet. A null URL means the preserved
  media type is not safe for inline browser display.
- `done` is always `{ "reason": "completed" }` after `meta`, or
  `{ "reason": "error" }` after `error`. Do not treat transport EOF without
  `done` as success.
- `error` has the ordinary safe `{ "code": string, "message": string }`
  envelope, for example:

  ```text
  event: error
  data: {"code":"stream_interrupted","message":"The answer stream was interrupted. Please try again."}

  event: done
  data: {"reason":"error"}

  ```

  Preserve any partial answer as visibly incomplete, show generic retry UI
  based on `code`, and do not render the server `message` as application copy.

### Cancellation and retry

Cancel an in-flight request with the `AbortController` passed to `fetch` when
the user presses Stop, changes workspace/chat, or leaves the view. An abort is
client-initiated: do not show an error, do not reconnect automatically, and do
not assume the server discarded an already-completed turn. A user may send the
question again explicitly; this is the only retry behavior. Because a cancelled
request can finish server-side while its response is no longer visible, refresh
the selected session before rendering a later turn if a session ID had already
been received.

### Frontend implementation conformance

The current frontend implementation uses only relative proxy routes and sends
no identity headers or user ID. It uses `fetch` with a `ReadableStream` SSE
parser (not `EventSource`), combines physical `data:` lines before JSON
parsing, ignores unknown event names, and requires the documented terminal
sequence. It appends `answer.delta` verbatim, treats `meta` as the only source
of session/citation/grounded completion state, and treats an EOF without the
appropriate `done` event as incomplete. Stop, workspace/chat changes, and
view disposal abort the browser request; an abort does not display an error or
trigger a retry. A later turn refreshes its selected session through the normal
session route when the session ID has been received.

### Source image display

The Sources pane renders image assets under their owning citation. The central
chat pane may also show a deduplicated “Related source images” section for the
active grounded response. Images link to a full-size authorized route, use
provided alt text/caption or a neutral document-derived fallback, and are not
interpreted as proof that the model examined their pixels. Workspace/session
changes clear citations and image references together.

The UI must be validated with the live backend using
`docs/frontend/integration_test_plan.md`. This is manual integration
validation, not a frontend command that starts services or calls models.

## Retention and Privacy

Sessions retain title, workspace, preview, compact summary, and the latest 10 raw turns. Older raw turns are removed after a successful summary refresh; metadata/summaries retain for 90 days by default. Langfuse is optional and raw content capture remains disabled by default.

## Local and Office Delivery

Vite proxies API/SSE traffic to a backend using its fixed server-side development subject; Vite does not select or inject user identity. Nginx must strip client-supplied identity headers, inject the authenticated office identity, proxy SSE without buffering, and serve SPA fallback. Browser bundles contain no provider, database, identity, or Langfuse secrets.

Two-user ownership isolation is validated in backend tests through FastAPI dependency overrides rather than a browser-controlled local identity mechanism.

## Unresolved Office Inputs

- Exact gateway identity header name and authentication provider.
- Nginx CI/CD, static asset path, API upstream, TLS, and CORS policy.
- User-facing wording for archive versus permanent deletion.

## Parallel Frontend Handoff

Build `frontend/` with React, TypeScript, and Vite against the contracts above. Render bounded history as a clearly labeled summary plus recent turns. Include new chat, rename/archive, sources drawer, streaming/reconnect states, and workspace filtering. Do not implement ingestion/admin screens.

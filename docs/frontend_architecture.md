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
should leave it false.

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
data: {"session_id":"9b1de4f0-0d4e-4b92-a3d7-0a72ea62b7d4","grounded":true,"sources":[{"doc_id":"release-guide","chunk_id":"release-guide:14","source_path":"docs/releases.md","title":"Release guide","page":null,"section":"Rollback","score":0.92,"snippet":"Run deploy rollback to restore the prior release."}],"debug":null}

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

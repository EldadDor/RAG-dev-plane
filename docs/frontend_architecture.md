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
- `POST /chat/stream` is SSE; it emits answer data, then `meta` with session ID, sources, and grounded state, then `done`. If a failure occurs after the stream starts, it emits `error` with the safe error envelope below, then `done`.
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

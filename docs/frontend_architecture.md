# Frontend Architecture

## Product Shape

React + TypeScript + Vite SPA: top workspace selector, central streaming chat and citations, and a right-side per-user recent-chat pane. It is locally self-served by Vite and deployed as static assets through Nginx. Ingestion/admin UI is out of scope.

## Backend Contract

- `GET /workspaces` returns the current principal's PostgreSQL-authorized workspaces as `workspace_id`, `display_name`, and `role`. Workspace IDs remain text values.
- `POST /chat` returns a completed grounded response.
- `POST /chat/stream` is SSE; it emits answer data, then `meta` with session ID, sources, and grounded state, then `done`.
- `GET /chat/sessions?workspace_id=` lists the current user's active sessions.
- `GET /chat/sessions/{id}`, `PATCH /chat/sessions/{id}`, and `DELETE /chat/sessions/{id}` load, rename, and archive only that user's session.
- The backend derives office ownership from configurable gateway-validated identity headers and local ownership from a fixed server-side development subject. It never accepts a browser user ID.
- The backend revalidates workspace membership for every workspace-scoped chat and session operation. A client-provided workspace ID is a requested scope, not authorization.

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

# Frontend Architecture

## Product Shape

React + TypeScript + Vite SPA: top workspace selector, central streaming chat and citations, and a right-side per-user recent-chat pane. It is locally self-served by Vite and deployed as static assets through Nginx. Ingestion/admin UI is out of scope.

## Backend Contract

- `POST /chat` returns a completed grounded response.
- `POST /chat/stream` is SSE; it emits answer data, then `meta` with session ID, sources, and grounded state, then `done`.
- `GET /chat/sessions?workspace_id=` lists the current user's active sessions.
- `GET /chat/sessions/{id}`, `PATCH /chat/sessions/{id}`, and `DELETE /chat/sessions/{id}` load, rename, and archive only that user's session.
- The backend derives ownership from the trusted `X-Forwarded-User` gateway header. It never accepts a browser user ID.

## Retention and Privacy

Sessions retain title, workspace, preview, compact summary, and the latest 10 raw turns. Older raw turns are removed after a successful summary refresh; metadata/summaries retain for 90 days by default. Langfuse is optional and raw content capture remains disabled by default.

## Local and Office Delivery

Vite proxies API/SSE traffic and injects a configured development user header. Nginx must strip client-supplied identity headers, inject the authenticated office identity, proxy SSE without buffering, and serve SPA fallback. Browser bundles contain no provider, database, or Langfuse secrets.

## Unresolved Office Inputs

- Exact gateway identity header name and authentication provider.
- Nginx CI/CD, static asset path, API upstream, TLS, and CORS policy.
- Workspace discovery/authorization API.
- User-facing wording for archive versus permanent deletion.

## Parallel Frontend Handoff

Build `frontend/` with React, TypeScript, and Vite against the contracts above. Render bounded history as a clearly labeled summary plus recent turns. Include new chat, rename/archive, sources drawer, streaming/reconnect states, and workspace filtering. Do not implement ingestion/admin screens.

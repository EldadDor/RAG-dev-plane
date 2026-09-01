# Frontend-to-Backend Integration Test Plan

**Status:** Ready for operator execution
**Last reviewed:** 2026-09-01

## Scope and prerequisites

Run this checklist only after the approved backend, PostgreSQL/pgvector,
embedding service, and chat model are already healthy. Use the normal Vite or
Nginx proxy route; do not add browser identity headers or call provider,
database, or model endpoints directly. Use an authorized workspace and, where
available, a second principal or a known inaccessible workspace to exercise
authorization behavior.

The checklist validates browser behavior and the documented API contract. It
does not create ingestion/admin UI and does not require modifying backend data
outside of ordinary test chats that can be archived afterward.

## Discovery, sessions, and history

| Check | UI action | Expected browser/API result |
| --- | --- | --- |
| Workspace discovery | Load the app. | `GET /workspaces` succeeds through the proxy; only authorized workspaces appear; no user ID or identity header is sent by the browser. |
| Workspace selection | Select a workspace. | `GET /chat/sessions?workspace_id=<selected>` runs; recent chats are shown newest first. |
| New chat | Select **New chat**. | Composer clears; no session is selected or deleted. |
| Session load | Open a recent chat. | `GET /chat/sessions/{id}` has no `workspace_id` query; summary and chronological bounded raw turns render with timestamps. |
| Rename | Rename the selected chat. | `PATCH /chat/sessions/{id}` sends only `{ "title": string }`; new title appears in the header and recent list. |
| Archive | Archive and confirm. | `DELETE /chat/sessions/{id}` returns `204`; the chat disappears from recent chats and is not represented as permanently deleted. |

## Streaming and citations

| Check | UI action | Expected browser/API result |
| --- | --- | --- |
| New streamed answer | Ask a documentation question in an authorized workspace. | Browser sends `POST /chat/stream` with JSON `question`, `workspace_id`, `include_debug: false`, and no user ID. It requests `text/event-stream`. |
| Incremental rendering | Observe while the answer generates. | Each named `answer` event's JSON `delta` is appended verbatim, including whitespace/newlines. The UI does not wait for a complete answer. |
| Completion | Allow the response to finish. | `meta` arrives before `done`; the returned `session_id` is used for the next turn, grounded state is shown, and sources replace the source drawer only from `meta`. The finished chat is visible in the refreshed recent list. |
| Sources | Open the Sources tab/drawer for a grounded response. | Each source shows title/path, optional section/page, and snippet without changing the answer text. A non-grounded response is labelled as not grounded rather than inferred from source count. |
| Continuation | Send a second message in the same chat. | Request includes the `session_id` received in the prior `meta`; reloading the session shows both turns in chronological order. |

## Recovery, authorization, and cancellation

| Check | UI action | Expected browser/API result |
| --- | --- | --- |
| Stop | Start a response, then choose **Stop**. | The browser aborts the fetch without an error banner or automatic retry. Existing partial text is labelled incomplete/stopped. Do not assume the server discarded the turn. |
| Post-start stream failure | Induce an approved safe stream failure, if available. | `error` uses `{ code, message }`, followed by `done` with `reason: "error"`; partial text stays visible and incomplete; UI offers only user-initiated retry and never displays server message text as product copy. |
| Transport EOF | Interrupt the stream before `done`, if safely reproducible. | UI treats it as incomplete, not a completed answer; no automatic reconnect/replay occurs. |
| Workspace switch during stream | Start a response then change workspace. | In-flight request is aborted; old partial text/citations are not shown under the new workspace. |
| Session switch during stream | Start a response then open another chat. | In-flight request is aborted; selected session loads normally without mixed turns or citations. |
| Lost access | Use an inaccessible workspace/session or revoke test access. | `403 workspace_access_denied` refreshes workspace discovery and recovers selection; `404 resource_not_found` removes the unavailable session from UI state. |
| Authentication and malformed request | Exercise gateway-missing identity and an invalid request only in an approved test environment. | `401 authentication_required` leads to normal sign-in/reload guidance; `422 invalid_request` produces generic recoverable UI and never server internals. |
| Provider outage | Temporarily make the answer provider unavailable only in an approved environment. | Pre-stream `502 upstream_unavailable` shows retry guidance; no raw backend/provider detail is rendered. |

## Evidence to capture

- Browser network entries for workspace/session operations and one completed
  stream, with request bodies/headers redacted as needed.
- Event order and payload shape for a successful stream and, if tested, a
  post-start error or intentional abort.
- Screenshots of the completed source drawer, Stop state, and one authorization
  recovery state.
- Any discrepancy recorded in `docs/agent_handoff/frontend_to_backend.md` with
  endpoint, status/event, reproduction steps, and user-visible result.

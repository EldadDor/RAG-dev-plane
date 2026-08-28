# Frontend Agent Instructions

## Scope

Work only inside `frontend/**` unless the user explicitly asks to change a
backend API contract or shared documentation.

Do not edit:
- `src/**`
- `tests/**`
- Python dependencies or `uv.lock`
- backend `.env` files
- Docker, PostgreSQL, Ollama, or FastAPI configuration

Backend contract changes must be proposed in `docs/frontend_architecture.md`
and handed back to the backend task before implementation.

## Stack

- React
- TypeScript
- Vite
- Static production build served by Nginx
- API and SSE accessed only through the configured Vite/Nginx proxy

## Product Requirements

- AI-chat layout: top workspace selector, central streaming chat, right-side
  per-user recent-chat pane, citation/source drawer.
- No ingestion or admin UI.
- Never place API keys, database credentials, model endpoints, or Langfuse
  credentials in browser code or frontend environment files.
- Use the backend-derived user identity contract; never send a user ID in an
  API request body.

## Backend Contract

Read `../docs/frontend_architecture.md` before changing API integration.
Treat it as the source of truth for sessions, streaming, retention, and the
trusted gateway identity header.

## Cross-Team Handoff

Read `../docs/agent_handoff/` before starting work that depends on the backend
or affects its contract. The asking side must record every cross-team feature,
bug, API change, clarification, validation result, or blocker in its
direction-specific file before implementation depends on it:

- Frontend writes `../docs/agent_handoff/frontend_to_backend.md`.
- Backend writes `../docs/agent_handoff/backend_to_frontend.md`.

Add new entries at the top and never rewrite or delete earlier entries. Record
explicit cross-team approvals in `../docs/agent_handoff/decisions.md`. Handoff
entries are proposals or status updates only; `../docs/frontend_architecture.md`
remains the authoritative API contract.

## Validation

- Run frontend type checks, tests, and production builds when the user permits.
- Do not start Uvicorn or use live model/database services unless explicitly
  approved.

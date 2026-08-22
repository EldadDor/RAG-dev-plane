# RAG Dev Plane — Shared Codex Workflow

## Project Areas

- `src/`, `tests/`, and Python configuration: backend.
- `frontend/`: React/Vite frontend.
- `docs/`: shared architecture, phase, and API-contract documentation.

Work only in the area requested by the user. Do not change backend files while
working on the frontend, or frontend files while working on the backend, unless
the user explicitly approves a shared API-contract change.

## Required Reading

- Read root `AGENTS.md` for backend architecture rules.
- Read `docs/frontend_architecture.md` before frontend/API integration work.
- Read `docs/work_current_phase.md` and `docs/next_phase.md` before starting a
phase; update them as work progresses when the user asks for workflow tracking.

## Local Services and Safety

Do not start, stop, or configure Uvicorn, Ollama, PostgreSQL/pgvector, Docker,
or IntelliJ/PyCharm unless explicitly requested.

Do not edit `.env`, credentials, secrets, or local service settings unless
explicitly requested. Do not run tests that contact live services without prior
approval.

## Validation and Handoff

Run the smallest relevant static check or test only when permitted. State what
was not run.

Keep backend/frontend handoffs in `docs/frontend_architecture.md`; do not put
credentials or provider/database secrets in browser code or frontend env files.

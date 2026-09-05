# Frontend Agent Instructions

The root `AGENTS.md` applies here in full — including the phase-record rule,
intake rule, safety rules, precedence, and the closing `Phase records: …` line.
This file only pins the frontend paths and its definition of done.

## Phase records
For this area the files are `../docs/frontend/work_current_phase.md` and
`../docs/frontend/next_phase.md`. Update them before and after every task,
whether or not the prompt mentions them, unless the user explicitly says not to.
Never start an item that has no row in `work_current_phase.md`; move it from
`next_phase.md` first.

The "Required Update Protocol" kept in the phase file now mirrors this section;
if they diverge, this file wins (per root precedence).

## Scope (frontend)
Work only in `frontend/**`. Treat everything outside it — `src/`, `tests/`,
`database/`, and root Python config — as **out of bounds**: do not read, edit,
search, or index it. The only backend touchpoints are the API contract in
`../docs/frontend_architecture.md` (read-first; backend owns it, frontend
proposes/requests) and the handoff files in `../docs/agent_handoff/`. If a task
seems to require a backend change, stop and record it in `frontend_to_backend.md`
instead of crossing over.

## Ignore
Never search, read, or run against these (they are generated or vendored):
`node_modules/`, `dist/`, `.vite/`, `.vite-temp/`, `coverage/`, `../out/`,
`../.venv/`, `../src/`, `../tests/`, `../database/`.
Source of truth is `frontend/src/`; static assets live in `frontend/public/`.

## Validation
- Run frontend type checks, tests, and production builds when the user permits.
- Do not start Uvicorn or use live model/database services unless explicitly
  approved.
- State what you did **not** run.
- A task is not complete until its row in
  `../docs/frontend/work_current_phase.md` records the result and evidence
  (commands, files, commit hash prefixed with the task ID, e.g. `FP-07: …`).

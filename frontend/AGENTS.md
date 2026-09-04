# Frontend Agent Instructions

The root `AGENTS.md` applies here in full — including the phase-record rule,
intake rule, safety rules, precedence, and the closing `Phase records: …` line.
This file only pins the frontend paths and its definition of done.

## Phase records
For this area the files are `../docs/work_current_phase.md`? No —
`../docs/frontend/work_current_phase.md` and `../docs/frontend/next_phase.md`.
Update them before and after every task, whether or not the prompt mentions them,
unless the user explicitly says not to. Never start an item that has no row in
`../docs/frontend/work_current_phase.md`; move it from `next_phase.md` first.

The "Required Update Protocol" kept in the phase file now mirrors this section;
if they diverge, this file wins (per root precedence).

## Scope
Work only inside `frontend/**` unless the user explicitly asks to change a shared
file. Shared docs and the API contract (`../docs/frontend_architecture.md`) are
read-first: the frontend proposes and requests contract changes; the backend owns
the decision. Record cross-boundary items via `../docs/agent_handoff/`.

## Validation
- Run frontend type checks, tests, and production builds when the user permits.
- Do not start Uvicorn or use live model/database services unless explicitly
  approved.
- State what you did **not** run.
- A task is not complete until its row in
  `../docs/frontend/work_current_phase.md` records the result and evidence
  (commands, files, commit hash prefixed with the task ID, e.g. `FP-07: …`).

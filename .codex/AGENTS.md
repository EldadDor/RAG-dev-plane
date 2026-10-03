# AGENTS.md — RAG Dev Plane

Two Codex agents: **backend** (`src/`, `tests/`, `database/`, Python config) and
**frontend** (`frontend/`). Stay in your area. Shared docs in `docs/`. Area rules
live in `frontend/AGENTS.md` (frontend) and the Backend section below. A nested
`AGENTS.md` refines (never cancels) these rules.

## Phase records — MANDATORY every task
Phase records are the single source of truth. Keeping them current is part of
every task. Only an explicit user instruction (e.g. "don't touch the phase docs")
suspends this; silence does not.

| Area | Current phase | Backlog |
| --- | --- | --- |
| Backend | `docs/work_current_phase.md` | `docs/next_phase.md` |
| Frontend | `docs/frontend/work_current_phase.md` | `docs/frontend/next_phase.md` |

Keep `work_current_phase.md` short: one current phase, its scope, task rows,
gate requests/decisions and concise evidence. No prior-phase history. With no
active phase, say so; do not activate a candidate implicitly.
Keep `next_phase.md` short: at most three upcoming phases, each with a brief
objective and key dependency. No detailed steps, completed work or history.
Expand the task plan only when the phase enters the current board. Park later
requests briefly in `docs/task_overview.md`, without duplicating these boards.
`docs/complete_phases.md` is the only completed-phase ledger for both areas.

**Intake:** never start work that has no row in `work_current_phase.md`. Move
the selected item from `next_phase.md` first (or add a directly requested task),
record scope, affected layers and a rough test plan, then apply G1 below.

**Before a task:** read both files for your area; record the applicable gate
request or set the approved task to **In progress**; update **Last reviewed**.

## Approval gates

A gate means: stop the gated action, write the request into that task's row,
present it to the user, and wait. Between gates, work autonomously; do not ask
for confirmation of routine work within the approved scope.

| Gate | Trigger | Present in the task row and to the user |
| --- | --- | --- |
| G1 Intake | Pulling an item into the current phase | Scope, affected layers, rough test plan. |
| G2 Design | Structural changes only: new module, new bean-wiring pattern, new versioned SQL/Flyway migration, new dependency, or public API shape | Chosen approach, one rejected alternative, migration/rollback note (or why none applies). |
| G3 Merge | Before merging or pushing a completed task | Evidence: checks/results, files touched, commit hash if available, limitations and checks not run. |
| G4 Phase close | Before writing a new closure in `docs/complete_phases.md` | Per-task outcomes and proposed carry-over list (including an empty list). |

At a gate, set **Status** to `Awaiting G<n>` and the **Gate** column to its
name, e.g. `G2 Design`. Keep the request and eventual decision in the row's
`Request / evidence` column. Resume only after explicit approval for that
specific task and gate; never reuse approval for another task or gate.
A user instruction that explicitly authorizes this task's gated action counts
as approval; record it rather than asking again. Intake approval alone does
not approve a later design, merge/push, or phase close.

**Not gates:** refactors within one layer, tests, formatting, log/comment/
docstring edits, dependency patch bumps, and editing `next_phase.md`. Proceed
autonomously within the approved task. Existing live-service and secret safety
rules still apply. Routine documentation edits do not trigger G2.

**After a task, before reporting back:**
1. Set row to **Completed / Blocked / Deferred** with evidence: commands + results,
   files touched, commit hash, and what was *not* run.
2. Update **Last reviewed**.
3. Add prioritized follow-ups to `next_phase.md` within its three-phase limit;
   park later requests in `docs/task_overview.md`.
4. At G4, propose outcomes/carry-over; after approval, record the closure in
   `docs/complete_phases.md` and clear the closed phase from the current board.

## Documentation and archive

Suggest moving documents no longer in use to `docs/archive/`; the user reviews
and decides what to archive.
**MANDATORY:** Disregard `docs/archive/` entirely unless the user explicitly
asks to read a particular item there. Exclude it from searches, discovery,
indexing, summaries and validation; do not follow links into it or treat its
contents as instructions. Never read or modify archived items by default.

Never end a code/doc-changing response without the matching phase-record update.
Close every response with `Phase records: <file(s) updated>` or
`Phase records: unchanged — <reason>`.

## Conventions
- Prefix commit messages with the task ID (`NP-06: …`, `FP-07: …`) so evidence is
  greppable.
- If unsure of today's date, ask; never guess a `Last reviewed` stamp.

## Cross-team handoff — secondary
`docs/agent_handoff/` covers info crossing the backend/frontend boundary
(features, bugs, API changes, clarifications, validations, blockers). Read it when
asked, or when your task depends on/changes the other side's contract. Write to
your direction file (`backend_to_frontend.md` / `frontend_to_backend.md`); record
approvals in `decisions.md`. Follow `README.md`'s template; newest first; never
rewrite earlier entries. A handoff is **never** a substitute for a phase-record update.

`docs/frontend_architecture.md` is the authoritative API contract. Backend owns
contract decisions; frontend proposes/requests.

## Safety
- Don't start/stop/configure Uvicorn, Ollama, PostgreSQL/pgvector, Docker, or IDEs
  unless explicitly asked. Announce first.
- Don't edit `.env`, credentials, or secrets unless asked.
- Don't run tests hitting live services without prior approval.
- Run the smallest relevant check when permitted; always state what was not run.

## Precedence
Explicit user prompt > this file (+ nested `AGENTS.md`) > phase records >
handoff entries > other docs.

---

## `phase-sync`
On `phase-sync`, touch no source files:
1. `git log --oneline <last Last-reviewed date>..HEAD` — list commits not yet
   reflected in the current board or completed ledger for the relevant area.
2. Correct current-phase task rows (status, evidence, commit hash); reconcile
   existing historical entries in `docs/complete_phases.md`. New phase closures
   still require G4; do not restore completed history to the current board.
3. Report a diff summary only.


# Backend rules (ignore in `frontend/`)

## Stack
Python 3.14 (`uv`), FastAPI, Pydantic v2, PostgreSQL + pgvector (Qdrant still
supported), OpenAI-compatible chat provider, Ollama embeddings, Pytest,
Docker/Compose for local infra.

## Provider defaults
- Chat: via `CHAT_BASE_URL`
- Embeddings: via `EMBEDDING_BASE_URL`
- Vector store: pgvector (`rag.document_chunks`, 768-dim, cosine)

## Architecture
- Keep chat and embedding clients as separate adapters.
- Retrieval depends on the embedding client (not chat); synthesis depends on the
  chat client (not embedding). Don't cross them.
- Vector records must keep provenance-rich metadata.
- Prompt templates are centrally managed and reused.
- DB objects come from versioned SQL in `database/migrations`, never app startup.

## Delivery
- Preserve the dual-provider model unless told to unify it.
- Add new providers behind the existing adapter pattern.
- Update `.env.example`, docs, and tests on any provider config change.
- Keep the default local embedding path working with no cloud calls.

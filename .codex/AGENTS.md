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

**Intake:** never start work that has no row in `work_current_phase.md`. Move the
item from `next_phase.md` into `work_current_phase.md` first.

**Before a task:** read both files for your area; set the task row to
**In progress** with scope + any approval dependency; update **Last reviewed**.

**After a task, before reporting back:**
1. Set row to **Completed / Blocked / Deferred** with evidence: commands + results,
   files touched, commit hash, and what was *not* run.
2. Update **Last reviewed**.
3. Add new follow-ups/scope changes to `next_phase.md`.
4. On phase close, record it in `docs/complete_phases.md`.

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

# Backend rules (ignore in `frontend/`)

## Stack
Python 3.14 (`uv`), FastAPI, Pydantic v2, PostgreSQL + pgvector (Qdrant still
supported), OpenAI-compatible chat provider, Ollama embeddings, Pytest,
Docker/Compose for local infra.

## Provider defaults
- Chat: `qwen2.5:7b-instruct-q4_K_M` via `CHAT_BASE_URL`
- Embeddings: `nomic-embed-text` (768-dim) via `EMBEDDING_BASE_URL`
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

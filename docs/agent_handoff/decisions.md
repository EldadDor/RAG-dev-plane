# Cross-Team Decisions

Record only explicit product/user approvals that affect both backend and
frontend. Add newest entries directly below this heading.

## 2026-08-29 — Archive action wording

- **Status:** Approved.
- **Decision:** Use “Archive chat” for the destructive session action and
  confirm with “Archive this chat? It will be removed from your recent chats.”
  The action maps to `DELETE /chat/sessions/{id}`, which archives rather than
  permanently deletes the session.
- **Authoritative references:** `docs/frontend/work_current_phase.md` and
  `docs/frontend_architecture.md`.

## 2026-08-29 — Backend owns API contract decisions

- **Status:** Approved.
- **Decision:** The frontend recommends requirements and requests missing
  details, but the backend is the final decision-maker for every API change.
  Only backend-approved and documented contracts may be implemented by the
  frontend.
- **Approved contract additions:** Canonical workspace/session JSON shapes,
  chronological timestamped session turns, deterministic newest-first session
  lists, and a safe `{ code, message }` error envelope. See
  `docs/frontend_architecture.md`.

## 2026-08-24 — Workspace discovery and authorization

- **Status:** Approved and implemented; live database validation pending.
- **Decision:** The frontend discovers authorized text workspace IDs through
  `GET /workspaces` and never sends a user ID. The backend derives identity and
  revalidates membership for every workspace-scoped operation.
- **Authoritative references:** `docs/work_current_phase.md`,
  `docs/frontend/work_current_phase.md`, and `docs/frontend_architecture.md`.

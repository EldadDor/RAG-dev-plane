# Cross-Team Decisions

Record only explicit product/user approvals that affect both backend and
frontend. Add newest entries directly below this heading.

## 2026-10-03 — NP-23 intake and structural design approved

- **Status:** G1, G2 and G3 approved; direct push to `origin/main` rejected by automatic review; G4 phase closure pending.
- **Decision:** User instructed “Start NP-23”, “Approved G2, procced” and “G3 approved”. Approved read-only trusted profile and per-principal recent-chat preferences, strict 10/20/50/100 values, PostgreSQL migration 008, shared local process fallback, explicit unavailable gateway/Qdrant preference capability, and G3 delivery push. Logout integration remains NP-24.
- **Evidence:** docs/account_preferences_api_design.md and docs/work_current_phase.md; chosen approach, rejected browser-only alternative and code-first rollback are recorded. Implementation is offline validated (206 passed). The automatic review rejected the combined commit/push to `origin/main` because the change set would go directly to the default branch and the remote was unverified. No Git operation occurred. SQL execution, service restart, frontend implementation, Kotlin parity and G4 closure remain outside this approval.

## 2026-10-03 — NP-22 activation and closure

- **Status:** Approved and completed.
- **Decision:** User instructed “Start NP-22”, then approved proceeding with
  implementation and closure. Preserve the uncapped bare-array session response,
  add deterministic timestamp/ID ordering and fix fallback rename/archive
  persistence. FP-15's display cap remains separate from retained raw turns.
- **Evidence:** Implementation `983e8d6`, closure `32acbb5`, 18 offline tests;
  docs/work_current_phase.md and docs/frontend_architecture.md. No live validation
  or NP-23–NP-26 activation was implied by this decision.

## 2026-08-31 — FP-06 streaming interaction and recovery

- **Status:** Approved.
- **Decision:** The frontend may implement incremental answer rendering,
  explicit cancellation, grounded-state and citation presentation, safe
  code-specific failures, and user-initiated retry. It must not automatically
  replay a streaming POST after interruption.
- **Authoritative references:** `docs/frontend/work_current_phase.md` and the
  backend-approved wire contract in `docs/frontend_architecture.md`.

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

- **Status:** Complete; migration 004 and live browser validation passed on 2026-09-12.
- **Decision:** The frontend discovers authorized text workspace IDs through
  `GET /workspaces` and never sends a user ID. The backend derives identity and
  revalidates membership for every workspace-scoped operation.
- **Authoritative references:** `docs/work_current_phase.md`,
  `docs/frontend/work_current_phase.md`, and `docs/frontend_architecture.md`.

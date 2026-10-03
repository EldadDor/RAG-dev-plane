# Cross-Team Decisions

Record only explicit product/user approvals that affect both backend and
frontend. Add newest entries directly below this heading.

## 2026-10-03 — NP-24 phase closure approved

- **Status:** G4 approved; phase closed.
- **Decision:** User instructed “G4 approved” after the delivered outcomes and carry-over request. NP24-01 approved design, NP24-02 implementation, NP24-03 offline validation/contract/delivery and NP24-04 closure are complete. Sole closure/outcomes/carry-over record: docs/complete_phases.md; current backend board is cleared.
- **Evidence/boundary:** Implementation `be26a96` and delivery records `8afaefd` are pushed to `origin/main`; 266 offline tests passed. Carry-over is live operator rollout/acceptance, frontend login/logout and mutation CSRF integration, and Kotlin gateway parity. No live-service authorization or frontend/new-backend-phase activation is implied.

## 2026-10-03 — NP-24 G3 delivery completed

- **Status:** G3 completed; G4 closure requested.
- **Decision/evidence:** The approved NP-24 implementation is committed as `be26a96` and pushed to `origin/main`. Offline evidence remains 266 provider-free tests and scoped/staged whitespace checks. Matching delivery/closure-request records are included under that G3 approval.
- **Boundary:** G4 closure remains pending. No live rollout or frontend activation occurred; operator acceptance, FP-16 integration and Kotlin gateway parity are proposed carry-over items. Existing `.env` and docs/task_overview.md edits remain outside this delivery.

## 2026-10-03 — NP-24 delivery approved

- **Status:** G3 approved; commit/push in progress.
- **Decision:** User instructed “G3 approved” in response to the explicit request to commit and push NP-24 to `origin/main`. Approval includes the implementation, contract, rollout guidance and matching delivery records; excludes pre-existing `.env` and `docs/task_overview.md` edits.
- **Evidence/boundary:** 266 provider-free tests passed; scoped whitespace checks passed. No live migration, SQL/proxy/Entra/browser acceptance, deployment, frontend activation or G4 closure is authorized by this approval.

## 2026-10-03 — NP24-01 structural design approved

- **Status:** G2 approved; implementation in progress.
- **Decision:** User instructed “Approving G2 for NP24-01”. Implement the separate Authlib/FastAPI gateway, Nginx authorization boundary, migration 009/session stores, local test identities, configurable cookie policy and application-only logout described in docs/auth_session_logout_design.md.
- **Boundary:** No live rollout, secrets, tenant provisioning, frontend activation, merge/push or phase closure authorized.

## 2026-10-03 — NP-24 expanded intake approved

- **Status:** G1 approved; concrete structural design awaits NP24-01 G2.
- **Decision:** User instructed “Approved, activate NP-24” after discussing Entra sign-in/account selection, local test identities, configurable cookie security/lifetimes and logout. Authentication gateway ownership is the approved direction; implementation library, persistence/migration and public routes are proposed in docs/auth_session_logout_design.md.
- **Boundary:** No G2/G3/G4 approval, live-service changes, tenant provisioning, credentials or frontend activation is implied. Workplace single-tenant policy is the proposed initial default; broader tenant access needs an explicit policy.

## 2026-10-03 — NP-23 intake and structural design approved

- **Status:** G1, G2, G3 and G4 approved; phase closed 2026-10-03.
- **Decision:** User instructed “Start NP-23”, “Approved G2, procced”, “G3 approved”, explicitly approved commit/push, and approved G4 closure on 2026-10-03. Approved read-only trusted profile and per-principal recent-chat preferences, strict 10/20/50/100 values, PostgreSQL migration 008, shared local process fallback, explicit unavailable gateway/Qdrant preference capability, and delivery to `origin/main`. Logout integration remains NP-24.
- **Evidence:** `5b315c8` (`NP-23: add approved account preferences`) is pushed to `origin/main`; delivery records are in `d1f5479`; G4 closure and carry-over are recorded in docs/complete_phases.md. Offline validation passed (206 tests). SQL execution, service restart, frontend implementation and Kotlin parity remain follow-ups.

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

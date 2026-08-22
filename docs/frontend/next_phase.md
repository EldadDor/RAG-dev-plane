# Next Frontend Phase — Approval Backlog

**Status:** FP-01 is proposed; no frontend implementation task is active until
its approval gates are satisfied.
**Last reviewed:** 2026-08-22
**Owner:** Frontend team

This file is the frontend-only intake and ordering record. Before a candidate
becomes active, move it into `work_current_phase.md`, define its task board,
and record the applicable approval decision.

## Candidate Work

| Priority | ID | Candidate task | Why it matters | Approval required |
| --- | --- | --- | --- | --- |
| 1 | FP-01 | Chat workspace foundation | Delivers the architecture's workspace selector, streaming chat, sources, and per-user recent-session experience. | Scope and unresolved contract inputs. |
| 2 | FP-02 | Frontend hardening and UX refinement | Strengthen accessibility, responsive behavior, error recovery, and focused test coverage after the foundation is accepted. | Acceptance criteria and test scope. |
| 3 | FP-03 | Office delivery integration | Configure the approved static deployment, proxy, identity handling, and SSE behavior with the infrastructure owner. | Gateway identity, Nginx/CI-CD/TLS/CORS, and deployment plan. |

## Recommended Next Phase

### FP-01 — Chat Workspace Foundation

**Proposed objective:** Implement the React + TypeScript + Vite chat SPA in
the documented frontend scope, using proxy-only API and SSE access.

**Acceptance checks:**

- A user can select a workspace, start/load a chat, view bounded history, rename
  or archive a session, and inspect sources.
- Streaming follows answer, `meta`, then `done`, including clear error and
  reconnect states.
- The browser never sends a user ID or exposes confidential provider,
  database, observability, or endpoint configuration.
- Type checks, relevant frontend tests, and production build complete without
  live services.

**Tracking:** See `work_current_phase.md` for the authoritative task-by-task
status, evidence, and approval gates.

## Phase Intake Checklist

- [ ] Clear objective, bounded scope, and explicit exclusions.
- [ ] Affected frontend files, dependencies, proxy behavior, and tests identified.
- [ ] Backend-contract dependencies checked against `../frontend_architecture.md`.
- [ ] Local validation and any approved live validation defined.
- [ ] Privacy, identity, and browser-secret exposure reviewed.
- [ ] Required approvals and user/product decisions recorded.
- [ ] Completion criteria and planned commit boundary recorded.

## Deferred Until Approved

- Workspace discovery or authorization API design.
- Gateway identity-header names and authentication implementation.
- Nginx CI/CD, static asset path, backend upstream, TLS, and CORS changes.
- Archive-versus-permanent-deletion wording.
- Ingestion, administration, provider, database, or backend contract changes.

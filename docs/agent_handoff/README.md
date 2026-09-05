# Backend ↔ Frontend Agent Handoff

This version-controlled directory is the shared asynchronous handoff point for
the backend and frontend agents. It is intentionally under `docs/`, rather than
inside either implementation directory, so each side can read and write it.

## How to use it

- Before an agent begins work that depends on the other side, read this
  directory and the applicable phase record.
- The asking side adds an entry to the direction-specific file whenever a
  feature, bug, requirement, proposed API change, contract clarification,
  validation result, or blocker affects the other side.
- Add new entries at the top, using the template below. Do not rewrite or delete
  prior entries; supersede them explicitly and link the newer entry.
- Keep the authoritative API specification in `docs/frontend_architecture.md`.
  A handoff entry may propose a change, but it is not an approved contract until
  that document and the relevant phase records are updated.
- Record user approvals in `decisions.md`. Do not treat an unapproved proposal
  as implementation authorization.

## Entry template

```md
## YYYY-MM-DD — Short title

- **From:** Backend | Frontend
- **To:** Frontend | Backend
- **Type:** Feature | Bug | Requirement | API change | Clarification | Validation | Blocker
- **Status:** Proposed | Needs review | Approved | Implemented | Resolved
- **Affected contract/files:** `path` or endpoint(s)
- **Message:** What changed or is needed, including enough detail to act on it.
- **Action requested:** A concrete next action, or `None`.
- **Supersedes / follow-up:** Link to a related entry, if applicable.
```

## Current cross-team state

- Backend NP-05 workspace discovery and authorization are complete and
  live-validated. The frontend's FP-01 work is implemented through FP-07;
  operator-run live integration validation and formal phase closure remain.
- Backend NP-08 is active. It may add optional profile-selection fields to
  ingestion, retrieval, and chat, but existing frontend requests must retain
  their current behavior when no profile is supplied.
- No frontend implementation is requested until NP-08 publishes an approved
  API contract change in `docs/frontend_architecture.md` and
  `backend_to_frontend.md`.

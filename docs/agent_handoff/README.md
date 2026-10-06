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
- `backend_to_kotlin.md` is the backend-owned parity handoff for the Kotlin
  runtime. It follows the same newest-first, append-only convention.
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

**Last reviewed:** 2026-10-03. These checkpoints summarize recorded validation,
not a fresh live-service health check.

- NP-20 catalog and NP-21 PowerPoint ingestion are implemented with recorded
  local rollout evidence. FP-10–FP-12 are implemented and locally validated;
  manual catalog browser integration remains unverified.
- NP-22 ordering/fallback persistence is approved and closed (`983e8d6`,
  `32acbb5`), with 18 offline tests. FP-15 can use the uncapped session list;
  FP-14 uses the existing session/SSE contract. FP-14–FP-17 remain candidates.
- NP-23/NP-24 account/preferences/logout and NP-25/NP-26 overview/full-preview
  contracts remain backend candidates required by FP-16/FP-17.
- Shared local cursor-secret configuration is recorded; fresh process/catalog
  acceptance remains an operator follow-up. Kotlin session parity is unverified.

- Backend NP-05 workspace discovery and authorization are complete and
  live-validated. Frontend FP-01 and FP-02 are complete, including operator-run
  streaming validation.
- Backend NP-08 through NP-10 are complete. Reranking remains opt-in after the
  NP-10 A/B decision.
- NP-13 through NP-15 Word ingestion and image-bearing citations were approved
  and implemented on 2026-09-11. Offline validation passes and migration 004
  is applied; live browser validation passed on 2026-09-12.

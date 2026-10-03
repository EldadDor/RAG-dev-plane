# Current Work Phase — NP-23 Profile and Preferences

**Last reviewed:** 2026-10-03
**Status:** Awaiting G4 — G3 delivery committed and pushed
**G1 approval:** User instructed “Start NP-23” on 2026-10-03.
**G2 approval:** User instructed “Approved G2, procced” on 2026-10-03;
approved the NP23-01 account/profile/preference design and migration source.
**Scope:** Trusted read-only profile/workspace details and per-user recent-chat
limit (10/20/50/100, default 10), with explicit supported capabilities.
**Affected layers:** Identity/API schemas, account route/service/store, versioned
SQL if durable preferences are approved, offline tests and frontend contract.
**Test plan:** Defaults/read/update/reload, strict validation, principal isolation,
auth failures and safe errors using offline fixtures; no live services.

| ID | Task | Status | Gate | Request / evidence |
| --- | --- | --- | --- | --- |
| NP23-01 | Inspect identity/storage and propose profile/preferences contract | Completed | G2 Design approved | User explicitly approved G2 on 2026-10-03. Chosen API, PostgreSQL migration 008, local process fallback, rejected browser-only alternative and code-first rollback are recorded in account_preferences_api_design.md. |
| NP23-02 | Implement approved API and preference persistence | Completed | — | Added account router, strict schemas, shared PostgreSQL/process/unavailable stores, dependency/lifespan/privacy/error wiring, migration 008, startup ledger and Docker/database instructions. No new dependency, provider or frontend code changes. Migration not applied; upgraded PostgreSQL startup requires it. |
| NP23-03 | Validate and publish supported frontend capabilities | Completed | G3 Merge approved | User approved G3 and exact origin/main delivery on 2026-10-03. Full offline suite: 206 passed; contract/handoff published; scoped whitespace check passed. Commit `5b315c8` (`NP-23: add approved account preferences`) pushed to `origin/main`. Files: account router/service, schemas, dependencies, main startup, PostgreSQL migration check, migration 008, Docker/database instructions, focused tests, frontend contract and task records. Not run: real SQL, live API/browser/model calls, migration execution or service operations. |
| NP23-04 | Close phase and agree remaining work | Awaiting G4 | G4 Phase close | Request: approve closure of NP-23 in complete_phases.md. Outcome: NP23-01/02/03 completed, validated offline (206 passed), and committed/pushed as `5b315c8`. Proposed carry-over: operator-authorized migration 008/local rollout and real SQL/API acceptance; gateway origin/CSRF deployment validation; frontend FP-15/FP-16 integration; Kotlin runtime parity with its owner. No application phase work remains in NP-23 after handoff. |

**Validation command:** `.venv/Scripts/python.exe -m pytest -q -p no:cacheprovider
--basetemp .np23-regression-tmp --ignore=tests/integration -m 'not integration'`
— 206 passed. Focused command used `tests/test_account.py
tests/test_workspace_authorization.py tests/test_api.py` — 65 passed before the
additional closed-pool/local-identity coverage included in the full run.
**G4 request:** Approve the NP23-01/02/03 outcomes and the NP23-04 carry-over list
above before a completed-phase entry is added.

Completed history: [sole phase ledger](complete_phases.md).

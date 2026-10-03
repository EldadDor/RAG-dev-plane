# Current Work Phase — NP-23 Profile and Preferences

**Last reviewed:** 2026-10-03
**Status:** Awaiting G3 — automatic review requires destination approval
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
| NP23-03 | Validate and publish supported frontend capabilities | Awaiting G3 | G3 Merge | User approved G3 on 2026-10-03. Automatic review rejected the combined commit and push to `origin/main`: broad change set on the default branch and repository contents sent to an unverified remote; approval did not establish this exact destination/side effect. No staging, commit or push occurred. Full offline suite: 206 passed; contract/handoff published; scoped whitespace check passed. Not run: real SQL, live API/browser/model calls, migration execution or service operations. Request: explicitly authorize pushing NP-23 to `origin/main`, or provide a destination branch/remote. G4 phase closure remains separate. |

**Validation command:** `.venv/Scripts/python.exe -m pytest -q -p no:cacheprovider
--basetemp .np23-regression-tmp --ignore=tests/integration -m 'not integration'`
— 206 passed. Focused command used `tests/test_account.py
tests/test_workspace_authorization.py tests/test_api.py` — 65 passed before the
additional closed-pool/local-identity coverage included in the full run.
**Carry-over proposal for G4:** separately authorized migration 008/local rollout
and real SQL/API acceptance; gateway origin/CSRF deployment validation;
frontend integration and Kotlin runtime parity remain with their owners.

Completed history: [sole phase ledger](complete_phases.md).

# Current Backend Work Phase

**Last reviewed:** 2026-10-03
**Status:** NP-24 Sign-in, sessions and logout — delivered; awaiting G4 closure.

**Scope:** Entra sign-in/account selection, local test identities, server-owned
sessions, configurable cookie security/lifetimes and truthful logout. Passwords
are entered at Microsoft sign-in. Workspace authorization remains explicit.
**Affected layers:** Authentication gateway/proxy, identity/configuration,
session persistence, account capabilities, API contract and deployment guidance.
**Rough tests:** Offline login/callback validation, identity isolation, expiry,
revocation, CSRF, cookie flags, gateway spoof protection and API/SSE recovery;
real Entra/browser/database acceptance requires separately authorized rollout.

| Task | Status | Gate | Request / evidence |
| --- | --- | --- | --- |
| NP24-01 Session and logout design | Completed | — | G1 approved by “Approved, activate NP-24”; G2 approved by “Approving G2 for NP24-01”. [Approved approach, alternative, migration/rollback](auth_session_logout_design.md). |
| NP24-02 Implement approved design | Completed | — | Separate `src/app/auth/` gateway; Authlib 1.8.0 + encrypted PostgreSQL/process records; migration 009; two local identities; cookie/expiry/CSRF/revocation; API identity/logout capability integration; `.env.example`, dependency lock and local/HTTPS Nginx examples. No live operations. |
| NP24-03 Validate and publish contract | Completed | — | G3 approved; implementation `be26a96` pushed to `origin/main`. Evidence: 266 provider-free tests passed with `.venv/Scripts/python.exe -m pytest -q -p no:cacheprovider --basetemp .codex-test-tmp-np24-acceptance --ignore=tests/integration -m 'not integration'`; staged whitespace checks passed. Published contract, [operations/limits](auth_gateway_operations.md), database docs and frontend handoff. Real SQL/migration, Nginx config/runtime, Entra/browser, service operations and frontend implementation unrun. One Authlib HTTPX fallback deprecation warning. Pre-existing `.env` and `docs/task_overview.md` edits excluded. |
| NP24-04 Phase closure | Awaiting G4 | G4 Phase close | Request closure: NP24-01 approved design; NP24-02 implemented gateway/session/logout; NP24-03 validated (266 offline tests), published and delivered (`be26a96`). Proposed carry-over: operator-approved migrations/role grants/private proxy/Entra rollout and real SQL/browser/cookie/SSE acceptance; FP-16 login/logout UI and CSRF on protected mutations; Kotlin gateway integration/parity. Keep admitted-request/global-Microsoft-logout limits documented; do not write the completed ledger until G4 approval. |

No service operations, secrets, tenant provisioning or deployment authorized.

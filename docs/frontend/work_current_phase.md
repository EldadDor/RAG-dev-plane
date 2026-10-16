# Current Frontend Work Phase

**Last reviewed:** 2026-10-16
**Status:** FP-16 implemented and offline-validated; uncommitted, live acceptance pending. FP-15 committed locally as a633351; no push/merge or phase closure performed.

| ID | Task | Status | Gate | Request / evidence |
| --- | --- | --- | --- | --- |
| FR-01 | Review backend handoff and current frontend readiness | Completed | G1 Intake approved | FR-01: User requested review 2026-10-16. Static inspection of handoffs, contract, api.ts and App.tsx: RAG-C-03 needs no frontend change; FP-14 stale session-load/draft confirmation gaps; FP-15 dedup/display limit absent; FP-16 menu actions are placeholders and auth/CSRF integration absent. NP-23/24 contracts published; rollout/acceptance pending. Updated both frontend boards. No commit; Git status failed (cannot change to repository root). Tests, type checks, builds, browser/live API/model/database checks not run. |

Completed history: [sole phase ledger](../complete_phases.md).
Phase-sync through `0d9431c` (2026-10-15): reviewed commits since the prior review; no frontend implementation commits. DOC-01 is closed in the shared ledger; DOC-03's pending closure is tracked in [task overview](../task_overview.md). No new phase closure was recorded.

## FP-14 Reliable New chat

Scope: existing React conversation state and request lifecycles only. Confirm New chat when a draft contains non-whitespace text or an answer/request is active; completed history alone needs no confirmation. Clear conversation UI, cancel pending work and ignore late results; preserve workspace and recent chats. No new module, dependency or API change.

| ID | Task | Status | Gate | Request / evidence |
| --- | --- | --- | --- | --- |
| FP-14 | Reliable New chat | Completed | G1 Intake approved | FP-14: User approved/start 2026-10-16. App.tsx confirms draft/active-request reset, clears conversation and focuses composer; abort/generation guards suppress stale selection, stream, completion refresh and mutation results. App.test.tsx adds 9 component-handler regression cases (mocked hooks; no DOM/effect/browser acceptance). rtk npm test: 43 passed; rtk npm run build: TypeScript and production build passed; scoped rtk git diff --check passed. Initial sandbox Vite resolution failed EPERM; offline checks passed with escalation. Files: App.tsx, App.test.tsx and both frontend boards. User approved committing all current repo changes on 2026-10-16, including the existing docs/task_overview.md and docs/work_current_phase.md edits (not reviewed by frontend). Committed all six current changed files as c453f01; staged whitespace check passed and working tree was clean after commit. No push/merge approval. G2 not triggered (existing layer, no dependency/API/module changes). Browser/live API/model/database checks not run; no services started, push/merge or G4 closure. |

## FP-15 Unique recent chats

Scope: existing API mapping and recent-chat pane. Deduplicate by session ID, retain newest record, deterministic updated-at/ID order, and display 10/20/50/100 (default 10). Keep distinct IDs with similar titles. Display choice is in-memory for now; account preference integration belongs to FP-16. Existing uncapped session API unchanged.

| ID | Task | Status | Gate | Request / evidence |
| --- | --- | --- | --- | --- |
| FP-15 | Unique recent chats and display limit | Completed | G1 Intake approved | FP-15: User approved next task 2026-10-16. api.ts deduplicates IDs retaining newest record, orders updated_at descending/null last and ordinal ID ties (preserves sub-millisecond UTC precision). App.tsx offers 10/20/50/100, default 10, caps only display and refreshes after rename; styles.css styles selector. api.test.ts/App.test.tsx cover duplicates, same titles, null/invalid timestamps, fine timestamp precision, immutability and supported display limits without refetch/selection loss. rtk npm test: 47 passed; rtk npm run build: TypeScript/production build passed; scoped rtk git diff --check passed. Files: five frontend source/test files and both frontend boards. User explicitly approved FP-15 commit on 2026-10-16; committed locally as a633351. No push/merge or phase closure approved. No new module/dependency/API shape (G2 not triggered). Browser/live API/model/database checks not run; no services started. Preference persistence remains FP-16. |

## FP-16 Profile, Settings and Logout

Scope: existing frontend API transport, account menu/panels and preference selector; read-only profile, capability-driven settings, same-origin session/CSRF and real application logout, sign-in and supported local test identities. Existing modules only; no dependencies or backend/API-shape changes. Live gateway/migration/Entra rollout remains operator-owned and unperformed.

| ID | Task | Status | Gate | Request / evidence |
| --- | --- | --- | --- | --- |
| FP-16 | Account actions and authentication integration | Completed | G1 Intake approved | FP-16: User explicitly approved 2026-10-16. Existing api.ts/App.tsx implement read-only profile, capability-driven preferences/persistence, same-origin Entra/dev sign-in, in-memory CSRF, confirmed application logout, auth generation/cancellation and expiry/visible-tab checks; DocumentsPanel.tsx distinguishes CSRF from workspace denial; styles.css and Vite account proxy updated. API/App tests now cover hooks/effects and 19 new account/session regressions. rtk npm test: 66 passed; rtk npm run build: TypeScript/production build passed; scoped whitespace checks passed. Shared integration checklist and frontend handoff updated. No new module/dependency/server API shape (G2 not triggered). No commit for FP-16; no push/merge/G4 closure, browser rendering/acceptance, migration/gateway/Nginx/Entra rollout or live API/model/database checks. Those remain operator prerequisites; no services started. |

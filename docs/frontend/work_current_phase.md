# Current Frontend Work Phase

**Last reviewed:** 2026-10-17
**Status:** TH-01–TH-04 committed as 70f50ca; TH-06 polish complete, uncommitted; TH-05 frontend acceptance complete and account synchronization deferred pending backend contract. FP-16 commit corrected to 10c6280. No new phase closure recorded.

| ID | Task | Status | Gate | Request / evidence |
| --- | --- | --- | --- | --- |
| FR-01 | Review backend handoff and current frontend readiness | Completed | G1 Intake approved | FR-01: User requested review 2026-10-16. Static inspection of handoffs, contract, api.ts and App.tsx: RAG-C-03 needs no frontend change; FP-14 stale session-load/draft confirmation gaps; FP-15 dedup/display limit absent; FP-16 menu actions are placeholders and auth/CSRF integration absent. NP-23/24 contracts published; rollout/acceptance pending. Updated both frontend boards. No commit; Git status failed (cannot change to repository root). Tests, type checks, builds, browser/live API/model/database checks not run. |
| FR-02 | Review current frontend state and tasks | Completed | G1 Intake approved | FR-02: User requested review 2026-10-17. Static boards/contract/handoff/source review confirms browser-only theme implementation; TH-05 awaits published/deployed backend theme and partial-PATCH contract. FP-14/15/16 recorded commits c453f01/a633351/10c6280; TH-01–04 recorded uncommitted; not independently Git-verified. rtk and native scoped Git status/log failed: cannot change to repository root. FP-17 remains parked on NP-25/26; live auth/catalog acceptance and delivery/G4 closure remain separate. Updated both frontend boards; no commit. Tests, type checks, builds, browser/live API/model/database checks not run; no services started. |

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
| FP-16 | Account actions and authentication integration | Completed | G1 Intake approved | FP-16: User explicitly approved 2026-10-16. Existing api.ts/App.tsx implement read-only profile, capability-driven preferences/persistence, same-origin Entra/dev sign-in, in-memory CSRF, confirmed application logout, auth generation/cancellation and expiry/visible-tab checks; DocumentsPanel.tsx distinguishes CSRF from workspace denial; styles.css and Vite account proxy updated. API/App tests now cover hooks/effects and 19 new account/session regressions. rtk npm test: 66 passed; rtk npm run build: TypeScript/production build passed; scoped whitespace checks passed. Shared integration checklist and frontend handoff updated. No new module/dependency/server API shape (G2 not triggered). FP-16 committed locally as 10c6280; no push/merge/G4 closure, browser rendering/acceptance, migration/gateway/Nginx/Entra rollout or live API/model/database checks. Those remain operator prerequisites; no services started. |

## Three-theme styling

User explicitly approved the complete plan on 2026-10-16 (G1). Existing frontend
modules, root data-theme and local cosmetic cache; no new dependency/module or
server API change (G2 not triggered for frontend). Dark default; exactly Dark,
White and New-age. Test cache/storage failure, picker keyboard/state retention,
semantic contrast, reduced motion, RTL/narrow layouts, TypeScript/build. Backend
owns account theme contract; do not send unpublished fields. Local commit of TH-01–04 explicitly authorized 2026-10-17. No push/phase closure or live operations authorized.

| ID | Task | Status | Gate | Request / evidence |
| --- | --- | --- | --- | --- |
| TH-01 | Semantic theme tokens and badges | Completed | G1 approved | TH-01: styles.css semantic surfaces/text/controls/focus/status/chat/source/badge tokens; documentBadges.ts uses CSS variables without changing labels/thresholds. Palette contrast checks cover text >=4.5:1 and control/focus >=3:1 on tested solid surfaces and both gradient endpoints. Local commit explicitly approved 2026-10-17; committed as 70f50ca. No push/merge/G4 closure. |
| TH-02 | Dark, White and New-age palettes | Completed | G1 approved | TH-02: exactly three palettes; Dark default, White/pale-gray, New-age violet/cyan with opaque fallbacks and optional glass. Shared line-height, full reduced-motion transition override, long identifier wrapping, 320px overflow fix. Fixture browser visuals at 320/900/1440px, RTL/long files/messages, menus/Settings/sources checked. Screenshots saved outside repo in task visualizations. Local commit explicitly approved 2026-10-17; committed as 70f50ca. No push/merge/G4 closure. |
| TH-03 | Header/Settings theme pickers and cache | Completed | G1 approved | TH-03: App.tsx native labelled radio groups; index.html validates cosmetic cache before React/styles; root data-theme, color-scheme and theme-color update. Browser-only/visit-only statuses honest under failed storage. App tests and fixture browser verify synchronized pickers, arrow-key selection/focus, draft/workspace/history/stream retention and reload persistence; auth loss retains cosmetic theme. No account theme calls or new module/dependency. Local commit explicitly approved 2026-10-17; committed as 70f50ca. No push/merge/G4 closure. |
| TH-04 | Backend theme preference proposal | Completed | G1 approved | TH-04: newest frontend_to_backend.md entry requests strict theme enum/default/capabilities, independent partial PATCH updates and server/process/unavailable persistence. Backend owns design/storage/migration/publication. Authoritative contract unchanged. Local commit explicitly approved 2026-10-17; committed as 70f50ca. No push/merge/G4 closure. |
| TH-05 | Synchronization and acceptance | Deferred | G1 approved | TH-05: browser-only implementation acceptance complete: rtk npm test 90 passed; TypeScript/production build passed; scoped whitespace checks passed. Fixture-only Vite browser checks at 320/900/1440px, keyboard/focus, RTL, long messages/files, source expansion and persistence; no browser errors/warnings. Preview proxy disabled, temporary fixture config removed/server stopped. Account theme sync/server precedence/partial-save/retry/late-account-response cases await backend-published contract and separately approved deployed acceptance; no speculative wire fields. No live API/model/database/gateway operations, no commit/push/G4 closure. |

## TH-06 Theme controls polish

| ID | Task | Status | Gate | Request / evidence |
| --- | --- | --- | --- | --- |
| TH-06 | Settings-only theme picker and SVG action icons | Completed | G1 approved | TH-06: User requested 2026-10-17. Existing App/DocumentsPanel/styles only; remove header picker, retain Settings picker/cache and replace Refresh/Close account panel/Refresh account text with inline SVG icons, accessible labels and tooltips. No new module/dependency/API (G2 not triggered). Validate existing regressions, TypeScript/build and whitespace. TH-01–04 committed separately as 70f50ca. TH-06: App.tsx, DocumentsPanel.tsx, styles.css and App.test.tsx updated; rtk npm test: 90 passed; rtk npm run build: TypeScript/production build passed; scoped git diff --check passed. Initial sandbox tests/build failed Vite realpath EPERM; escalated offline checks passed. New polish uncommitted. Browser visual/keyboard acceptance and live API/model/database checks not run; no services started. |

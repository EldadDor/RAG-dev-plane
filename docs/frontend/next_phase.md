# Next Frontend Phases

**Last reviewed:** 2026-10-16
**Status:** Candidates only; FP-14 is implemented on the current board. Activate a selected item through G1.

| Order | Phase | Objective | Key dependency |
| --- | --- | --- | --- |
| 1 | FP-15 Unique recent chats | Deduplicate by session ID, sort newest first, and display 10/20/50/100 sessions (default 10). | Existing uncapped session contract; keep distinct IDs with similar titles. |
| 2 | FP-16 Profile, Settings and Logout | Expose supported account/preferences/auth actions with safe unsupported states. | Published NP-23/NP-24 contracts; operator-approved rollout and real acceptance remain pending; include session/CSRF integration and no simulated logout. |

Later requests: [parked work](../task_overview.md). Expand steps at intake.

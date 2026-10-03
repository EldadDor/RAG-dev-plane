# Next Frontend Phases

**Last reviewed:** 2026-10-03
**Status:** Candidates only; activate a selected item through G1.

| Order | Phase | Objective | Key dependency |
| --- | --- | --- | --- |
| 1 | FP-14 Reliable New chat | Always reach a fresh conversation; confirm interruption of an active answer or unsent draft and suppress stale responses. | Existing session/SSE contract; confirm active-chat predicate at intake. |
| 2 | FP-15 Unique recent chats | Deduplicate by session ID, sort newest first, and display 10/20/50/100 sessions (default 10). | Existing uncapped session contract; keep distinct IDs with similar titles. |
| 3 | FP-16 Profile, Settings and Logout | Expose supported account/preferences/auth actions with safe unsupported states. | NP-23/NP-24 contracts and product decisions; no simulated logout. |

Later requests: [parked work](../task_overview.md). Expand steps at intake.

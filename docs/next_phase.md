# Next Backend Phases

**Last reviewed:** 2026-10-03
**Status:** Candidates only; activate a selected item through G1.

| Order | Phase | Objective | Key dependency |
| --- | --- | --- | --- |
| 1 | NP-23 Profile and preferences | Define trusted account fields and supported preferences, initially recent-chat limits 10/20/50/100. | Product scope and G2 API/persistence design; supports FP-16. |
| 2 | NP-24 Logout | Establish session invalidation ownership and a truthful signed-out contract, including unsupported local mode. | Gateway/identity-provider owner decision and G2 contract; supports FP-16. |
| 3 | NP-25 Whole-document overview | Define authorized, revision-bound overviews with trustworthy document coverage and generation limits. | G2 source/model-processing/cache design; coordinate preview capabilities with NP-26. |

Later requests: [parked work](task_overview.md). Expand steps at intake.

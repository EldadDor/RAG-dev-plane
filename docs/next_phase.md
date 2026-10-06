# Next Backend Phases

**Last reviewed:** 2026-10-03
**Status:** Candidates only; activate a selected item through G1.

| Order | Phase | Objective | Key dependency |
| --- | --- | --- | --- |
| 1 | Authentication rollout acceptance (NP-24 carry-over) | Validate real session durability, proxy/Entra login, cookies, logout and SSE recovery. | Explicit activation and operator approval for migrations, role grants, secrets and service/proxy/tenant operations. |
| 2 | NP-25 Whole-document overview | Define authorized, revision-bound overviews with trustworthy document coverage and generation limits. | G2 source/model-processing/cache design; coordinate preview capabilities with NP-26. |
| 3 | DOC-03 RAG ingestion and chat flow diagram | Create a Mermaid flow showing the full document ingestion and chat/retrieval/synthesis paths, including key stores and boundaries. | G1 intake approval; verify nodes and flow against the current backend implementation and architecture docs. |

Later requests: [parked work](task_overview.md). Expand steps at intake.

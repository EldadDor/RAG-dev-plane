# Project Task Overview

**Last reviewed:** 2026-10-03

Current work and the next three candidates per area live in the
[backend current board](work_current_phase.md), [backend next phases](next_phase.md),
[frontend current board](frontend/work_current_phase.md) and
[frontend next phases](frontend/next_phase.md).
All finished-phase outcomes and evidence live only in
[complete_phases.md](complete_phases.md).

## Pending workflow approval

| ID | Status | Gate | Request / evidence |
| --- | --- | --- | --- |
| DOC-03 RAG flow diagram | In progress | — | G1 approved by user 2026-10-06 (“start DOC-03”). Current phase board contains the documentation-only scope, affected area, rough validation plan and active task row. DOC-01 G4 closure and carry-over are recorded in complete_phases.md. |

## Parked work beyond the next three phases

These requests are retained for later prioritization; none is activated.

| ID / area | Request / dependency |
| --- | --- |
| NP-26 | Trustworthy page/slide counts and complete single-page PDF/DOCX or single-slide PowerPoint previews; define safe rendering, private source storage and revision lifecycle with NP-25. DOCX pagination needs an agreed renderer. |
| FP-17 | Document action menu, whole-document overview and complete single-page preview; depends on NP-25/NP-26, with explicit unsupported/multipage states. |
| NP-06 | Separate required unit/API CI from a manual environment-specific live lane. |
| NP-07 | Answer conciseness/groundedness tuning, starting with retrieval context assembly and evaluation evidence. |
| NP-12 / FP-03 | Azure/office delivery; infrastructure-owned gateway identity, proxy, SSE, TLS/CORS and deployment decisions. See AZURE_DEPLOYMENT_PLAN.md. |
| Observability | Nested RAG spans beyond the tracing foundation. |
| Quality / UI | Further semantic-splitter experiments, browser chunking-profile selection and any reranking default change require their own scoped decisions. |
| Operator acceptance | Fresh-process cursor/catalog acceptance, frontend catalog browser integration and PowerPoint badges need separately scoped follow-up. |
| Kotlin owner | Runtime parity with approved Python contracts; gateway authorization for profile warming needs a separate design. |

Move a prioritized request into a next-phase slot; define its detailed plan at G1.

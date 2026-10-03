# Next Phase — Approval Backlog

**Status:** NP-22 approved, committed as 983e8d6 and closed 2026-10-03. NP-23–NP-26 remain candidates.
**Last reviewed:** 2026-10-03

This is the ordered backlog for the next approved phase. Each item must have a
defined scope, acceptance checks, and an approval decision before implementation.

## Candidate Work

| Priority | ID | Candidate task | Why it matters | Approval required |
| --- | --- | --- | --- | --- |
| 1 | NP-01 | Refresh architecture documentation | Complete in `df37f9b`. | Completed 2026-08-20 |
| 2 | NP-02 | Decide the Qdrant warning policy | Complete: production check retained; mocked tests disable the probe. | Completed 2026-08-20 |
| 3 | NP-03 | Parser-aware Kotlin chunking | Complete: Tree-sitter symbols, line ranges, fallback behavior, and unit validation. | Completed 2026-08-21 |
| 4 | NP-04 | Add operational observability | Foundation complete: optional safe root tracing. Nested RAG spans are deferred. | Completed 2026-08-21 |
| 5 | NP-05 | Workspace discovery and authorization | PostgreSQL-backed authorization, frontend contract, migrations/local seed, live API validation, and documentation indexing complete. | Completed 2026-08-29 |
| 6 | NP-06 | Define CI test lanes | Separate required unit/API CI from a manual environment-specific live lane. | Queued |
| 7 | NP-07 | Answer conciseness and groundedness tuning | Tune retrieval-side context assembly before prompt wording. | Queued after NP-08 and NP-09 |
| 8 | NP-08 | Non-destructive chunking experimentation lab | Profile-scoped indexing, dry runs, and isolated retrieval are implemented and live-validated. | Completed 2026-09-07 |
| 9 | NP-09 | Golden evaluation set and regression harness | Default-profile baseline, offline smoke lane, and local artifact runner are complete. | Completed 2026-09-09 |
| 10 | NP-10 | Activate retrieval reranking | Optional cross-encoder reranking was evaluated; default remains off because precision/recall was saturated and mean latency rose 50%. | Complete 2026-09-10 |
| 11 | NP-11 | Frontend live validation and phase closure | FP-01 closure and live streaming validation are recorded by the frontend phase records. | Completed 2026-09-05 |
| 12 | NP-12 | Azure and office deployment | Execute `AZURE_DEPLOYMENT_PLAN.md` after quality tooling and deployment scope are approved. | Queued |
| 13 | NP-13 | Structured Microsoft Word ingestion | Safe `.docx` structure extraction, image anchors, and image-aware hashing implemented. | Complete — live validated 2026-09-12 |
| 14 | NP-14 | Embedded image asset lifecycle | Content-addressed asset storage, migration 004, and profile-scoped chunk associations implemented. | Complete |
| 15 | NP-15 | Authorized image citations and chat display | Authorized asset route, compatible citation metadata, and accessible previews implemented. | Complete — live browser validated 2026-09-12 |
| 16 | NP-16 | Hebrew and multilingual RAG evaluation | Hebrew golden-set evaluation established bge-m3 retrieval and DictaLM chat as the recommended local pairing. | Complete — closed 2026-09-13 |
| 17 | NP-17 | Embedding model profiles and embedding cache | Registry-backed isolated profile storage, cache, selection plumbing, and local-only dry-run warming are implemented. | Complete — closed 2026-09-13 |
| 18 | NP-18 | Spring Boot backend handoff | Current backend API/behavior and Kotlin Spring AI 2.0 migration design, retaining the frontend contract. | Complete — closed 2026-09-17 |
| 19 | NP-19 | Recent document metadata API design | Full proposed contract and publication/lifecycle implementation plan in recent_document_metadata_api_design.md. | Design complete 2026-10-02. |
| 20 | NP-20 | Implement recent document metadata API | Catalog storage, lifecycle integration, authorized listing, reconciliation tooling and frontend contract implemented. | Complete 2026-10-02: 134 offline tests; migration/backfill, enablement and live acceptance validated. |
| 21 | NP-21 | PowerPoint ingestion | Slide text, images, tables, cached charts, notes, scoped chunking and catalog type implemented. | Complete 2026-10-02: 149 offline tests, migration 007 and provider-free local SQL validation. |
| 22 | NP-22 | Recent-chat uniqueness, ordering and retrieval contract | Deterministic session ordering and in-memory rename/archive persistence; uncapped response retained. | Complete 2026-10-03: 18 offline tests; approved commit 983e8d6. |
| 23 | NP-23 | Authenticated profile and user preferences | Define and deliver approved account capabilities for FP-16. | Contract/product scope and persistence design before implementation. |
| 24 | NP-24 | Logout ownership and signed-out contract | Resolve gateway/identity-provider ownership for FP-16. | Infrastructure owner decision; separate from NP-12/FP-03 deployment. |
| 25 | NP-25 | Whole-document overview capability | Define and deliver authorized, revision-scoped overview actions for FP-17. | Design first; model processing and persistence require phase approval. |
| 26 | NP-26 | Trustworthy page counts and single-page previews | Define and deliver complete one-page PDF/DOCX and one-slide PowerPoint previews for FP-17. | Rendering/source storage design and dependencies require phase approval. |

## Frontend handoff task breakdown — 2026-10-03

Source: [FP-15–FP-17 handoff](agent_handoff/frontend_to_backend.md).
NP-22 was activated by the user on 2026-10-03; its authoritative task board is
in work_current_phase.md. NP-23–NP-26 remain backend-owned backlog items,
not implemented endpoints or approved migrations. FP-14 uses the existing
new-session/SSE contract and needs no backend task. FP-15 can implement its local
display cap against the current uncapped session list while NP-22 is reviewed.

### NP-22 — Recent chats (FP-15)

- **NP22-01, audit:** Trace session creation, list/load, refresh and archive paths;
  distinguish duplicate IDs from valid similarly titled sessions. Current route
  returns an uncapped bare array of owned, non-archived workspace sessions.
  PostgreSQL and in-memory stores sort by updated_at but lack an explicit ID
  tie-breaker. In-memory rename/archive mutate a copied detail object rather than
  stored metadata; include that confirmed parity defect in the approved fix scope.
- **NP22-02, contract and correction:** Specify newest-first ordering with a
  stable session-ID tie-breaker and null timestamp handling for both stores.
  Preserve the bare-array response unless a separately published extension is
  approved. Decide whether optional limit/pagination is needed; if so define
  bounds, cursor scope, refresh and ordering under concurrent updates. Defaults
  10 and choices 10/20/50/100 are display preferences, not raw-turn retention.
- **NP22-03, acceptance/publication:** Offline checks for ownership/workspace
  isolation, unique IDs, equal timestamps, archive/rename persistence, similar
  titles, more than 100 sessions and any approved pagination. Publish examples
  and cap semantics in frontend_architecture.md and respond through the handoff.
- **Affected:** chat router/schemas, conversation_store.py, focused session/API
  tests and shared contract. No data deletion, retention change or live calls.
  Planned commit: `NP-22: stabilize recent chat listing`.

### NP-23 — Profile and preferences (FP-16)

- **NP23-01, design:** Inventory trustworthy principal fields and approved
  workspace details; define read-only versus explicitly editable fields and
  unsupported capabilities. Propose recent_chat_limit only: 10/20/50/100,
  default 10; decide local versus per-principal persistent preferences and
  cross-login behavior. Never accept a browser-selected identity.
- **NP23-02, approved implementation:** Add agreed read/update schemas and
  operations with validation, defaults, persistence and safe errors. Any durable
  storage uses a reviewed versioned migration with rollout/rollback; identity,
  account administration and provider/database configuration remain outside scope.
- **NP23-03, acceptance/publication:** Offline tests cover supported/unsupported
  fields, invalid values, unknown fields, default/read/update/reload, independent
  principals and auth failures. Publish request/response/error examples before
  frontend integration. Depends on product approval of NP23-01; logout is NP-24.
- **Affected:** identity/dependencies, new account route/service/schemas, approved
  storage/migration, tests, contract. Planned commit: `NP-23: add approved account preferences`.

### NP-24 — Logout (FP-16)

- **NP24-01, ownership decision:** With the trusted gateway/infrastructure owner,
  establish whether gateway, identity provider or backend invalidates sessions.
  Current identity.py resolves a fixed local principal or trusted request headers;
  there is no backend logout capability. Local mode must explicitly report
  unavailable logout rather than simulate authentication termination.
- **NP24-02, contract then approved integration:** Define method/route or approved
  redirect, CSRF protection where applicable, cookie/session invalidation, safe
  redirects, success/failure and signed-out/reauthentication behavior. Do not
  invent an identity provider or silently expand office deployment scope.
- **NP24-03, acceptance/publication:** Offline mocks verify unavailable local
  behavior, failed invalidation, supported success and unsafe redirect rejection;
  coordinate separately approved gateway/browser validation. Specify when the
  frontend clears protected data and suppresses late responses. Draft/stream
  interruption confirmation belongs to FP-16.
- **Affected:** identity/auth integration, approved gateway configuration and
  contract/tests. Depends on NP24-01 and relevant FP-03 infrastructure decisions.
  Planned commit: `NP-24: publish and integrate approved logout flow`.

### NP-25 — Whole-document overview (FP-17)

- **NP25-01, design:** Define supported actions keyed by doc_id and authorized
  workspace/model/chunking scope. Choose precomputed versus on-demand generation;
  establish a trustworthy whole-document input, coverage/truncation disclosure,
  revision/hash identity, provenance, freshness, cost/latency/output/input limits,
  timeout/retry and concurrency semantics. An arbitrary retrieved chunk cannot
  stand in for a whole-document overview.
- **NP25-02, approved implementation:** Add agreed authorized capability/overview
  routes, source resolution and any scoped cache. Revalidate membership each
  request; invalidate on changed/deleted/re-ingested source and profile changes.
  Preserve safe errors and private cache policy; avoid paths/provider error leaks.
  Do not write turns to active chat or alter retrieval scope.
- **NP25-03, acceptance/publication:** Provider-free tests with mocked generation
  cover scope isolation, source identity, unsupported/missing/deleted content,
  revision invalidation, limits, retries, failure and auth loss. Publish concrete
  examples and availability in the contract/handoff before FP-17 integration.
- **Affected:** document catalog/routes/schemas, source lifecycle, approved
  overview service/cache, tests and contract. Depends on NP25-01 approval and
  approved model-processing/storage scope. Planned commit: `NP-25: add authorized document overviews`.

### NP-26 — Counts and full single-page preview (FP-17)

- **NP26-01, feasibility/design:** Define canonical type, nullable page/slide count
  and provenance; exact one-page PDF/DOCX or one-slide PowerPoint is eligible.
  DOCX requires a chosen renderer/pagination definition. Determine source-byte
  availability, safe rendering, supported formats, dependencies/resource limits
  and storage lifecycle. Chunk counts and citation images prove neither page
  count nor availability of a complete page/slide preview.
- **NP26-02, approved implementation:** Publish supported actions and count data
  compatibly with NP-20; implement agreed browser-safe media and authorized
  relative content routes. Bind previews to document revision/profile, enforce
  membership on every request, and invalidate assets on replacement/deletion.
  Define unsupported, multipage, unknown-count, oversized and failed rendering
  responses plus private cache policy; no internal paths or public source URLs.
- **NP26-03, acceptance/publication:** Offline synthetic fixtures cover full
  one-page PDF/DOCX and one-slide preview, multipage/unknown/unsupported input,
  deleted/replaced revisions, hostile packages, limits and denied access.
  Publish media/route/error examples and rendering limitations. Live/rendering
  tool installation or service validation requires its separately approved scope.
- **Affected:** loaders/ingestion, catalog metadata and reviewed migration if
  needed, private source/asset storage, document/asset routes, tests and contract.
  Depends on NP26-01 approval; coordinate capability shape with NP-25. Multipage
  navigation/download, OCR and visual interpretation remain separate scope.
  Planned commit: `NP-26: add authorized single-page document previews`.

### Delivery order and completion gate

Review NP-22 first. NP-23 and NP-24 can be designed independently; FP-16 needs
both readiness responses. Design NP-25 and NP-26 together so FP-17 receives a
consistent capability/revision contract, then implement each approved slice.
Before activation, move the selected phase to work_current_phase.md, record
approval, exact files, offline checks, data impact/rollback and any live gate.
Each phase closes with contract examples and a backend-to-frontend readiness
entry stating supported capabilities and remaining limitations. Kotlin runtime
parity is a follow-up for its owner once contracts are approved, not an implicit
change to the parallel repository.

## Latest Completed-Phase Record

### NP-21 — PowerPoint Ingestion

Implemented and locally validated 2026-10-02. See `powerpoint_ingestion.md` for
content coverage, explicit object limits and normal ingestion usage. Migration
007 is applied; the updated local API is healthy. Real SQL synthetic ingestion
fixtures validated publication/count/type, slide citations, images, unchanged,
failed/changed and blank-deck behavior, with fixture rollback and no real model
calls. Evidence: `phase_qa/NP21-live-powerpoint-ingestion.json`. Changes remain
uncommitted for review. Frontend handoff requests the new powerpoint label/color.

### NP-20 — Recent Document Metadata API

Complete and locally live-validated 2026-10-02. Snapshot: `afee99c`.
Migration 006 is applied, the catalog is certified, and listing is enabled.
All 132 document publications reconcile to 2,886 scoped chunks across two
profiles; 32 unscoped legacy chunks remain untouched/excluded. The offline
suite passes 134 tests. Live HTTP and real SQL fixture checks passed with no
real model calls and fixture rollback. Evidence: `phase_qa/NP20-live-document-catalog.json`
and `phase_qa/NP20-reconciliation.json`. FP-10–FP-12 may proceed against
`frontend_architecture.md`.

### NP-19 — Recent Document Metadata API Design

Completed 2026-10-02. See
[`recent_document_metadata_api_design.md`](recent_document_metadata_api_design.md)
for the proposed GET route, profile-specific counts/times, revision-checked
pagination, lifecycle corrections, safe errors, migration/backfill/rollback,
frontend acceptance, and NP20-01 through NP20-05 implementation tasks.
The proposal is not an implemented browser contract. NP-20 implementation and
migration execution remain subject to their recorded approval scope.

### NP-13 through NP-15 — Word and Embedded Images

Completed and live-validated 2026-09-12: structured Word ingestion, private
content-addressed image persistence, authorized image delivery, and frontend
citation previews. See [`document_image_support_plan.md`](document_image_support_plan.md).

### NP-16 — Hebrew and Multilingual RAG Evaluation

The committed 13-case Hebrew and 19-case English artifacts support bge-m3
retrieval with DictaLM chat for local operation. The default nomic profile is
preserved for rollback and comparison. See
[`work_current_phase.md`](work_current_phase.md).

### NP-17 — Embedding Model Profiles and Embedding Cache

Migration 005, profile/cache adapters, API selection, and the workspace-scoped
local warmer are complete. The warmer remains unavailable in gateway deployments
until a dedicated operator-authorization design is approved. See
[`embedding_model_profiles_plan.md`](embedding_model_profiles_plan.md).

## Phase Intake Checklist

Before a candidate becomes active, record:

- [ ] A clear objective and bounded scope.
- [ ] Explicit exclusions.
- [ ] Affected code, configuration, docs, and tests.
- [ ] Local and live validation requirements.
- [ ] Data/model/database impact and rollback plan, if applicable.
- [ ] Required user approvals or credentials.
- [ ] Completion criteria and a planned commit boundary.

## Deferred / Out of Scope Until Approved

- Provider changes or model swaps.
- Unapproved pgvector schema changes beyond the versioned baseline and approved migrations.
- Making live model/database tests mandatory in CI.
- Production deployment changes.
- Replacing the dual chat/embedding provider architecture.

## Cross-runtime cursor configuration follow-up — 2026-10-03

User-approved shared persistent DOCUMENT_LIST_CURSOR_SECRET is installed in Python and Kotlin local .env files; Kotlin listing is enabled. Configuration checks passed without printing the secret. On the next operator-started backend processes, refresh prior document cursors and verify the UI catalog response. No startup, live acceptance, provider calls or migrations were performed by this configuration task.

# Current Work Phase — NP-20 Recent Document Metadata API

**Status:** Complete — local rollout validated, closed 2026-10-02
**Activated:** 2026-10-02
**Owner:** Backend team
**Approval:** User approved NP-19 implementation and the local live rollout.
Current state committed as `afee99c` before migration/backfill/enablement.

## Objective and scope — NP-20

Deliver the approved recent-document API: additive PostgreSQL catalog/revisions,
atomic publication across ingestion/warming/cleanup, authorized discovery,
revision-checked cursors, safe display metadata, reconciliation and frontend
contract. The local rollout is complete. Frontend integration/browser validation
belongs to FP-10–FP-12; other environments require their own rollout.

## Task Board — NP-20

| ID | Task | Status | Evidence / outcome |
| --- | --- | --- | --- |
| NP20-01 | Metadata migration and catalog store | Complete | Migration 006 applied locally; per-model metadata/revisions, model-owned assets, readiness, scoped snapshot reads and startup checks. |
| NP20-02 | Coordinate ingestion, warming and directory publication | Complete | Atomic publication, per-model unchanged guards, zero chunks, scan protection, workspace-safe internal IDs, shared asset ownership and pinned publication locks. |
| NP20-03 | Authorized route, schemas, cursors and safe errors | Complete | Principal/membership on every page; configured scopes; HMAC cursors, revision/keyset pagination, safe typed fields, private/no-store headers. |
| NP20-04 | Reconciliation and regression validation | Complete | 134 offline tests passed; reviewed/applied backfill, exact legacy alias recovery, idempotent final report and zero all-scope SQL count mismatches. |
| NP20-05 | Frontend contract and handoff | Complete | frontend_architecture.md and backend_to_frontend.md publish validated contract; FP-10–FP-12 unblocked. |
| NP20-LIVE | Local rollout and live acceptance | Complete | 132 publications across 2 profiles; 2,886 scoped chunks, 32 unscoped preserved/excluded. Listing enabled, API healthy; acceptance evidence saved. |

## Validation and Outcome — NP-20

- Full offline suite: **134 passed** using
  `.venv/Scripts/python.exe -m pytest -q -p no:cacheprovider --basetemp .np20-test-tmp --ignore=tests/integration`.
  Workspace-local temp/cache handling avoids the existing Windows permissions issue.
- Stopped this project's older API writer, applied additive migration 006,
  reviewed read-only reconciliation, backfilled and certified, enabled the
  local `.env` flag, and restarted the updated API on port 8000.
- Exact source identity/path matches recovered 568 scoped `document_id` aliases
  as canonical metadata without re-embedding or changing vector/chunk IDs.
  Thirty-two pre-authorization vectors without workspace identity remain
  untouched and excluded; unknown historical times/hashes were not fabricated.
- Live validation exposed a JSON codec bug in the recovery write. Corrected
  native-object encoding and repaired those rows; final verification found
  zero non-object metadata rows and zero publication/count mismatches.
- Live HTTP health/readiness and enabled listing passed. Limits 1/25/100 fully
  traversed both local default-chunking model scopes with stable ordering,
  safe field allowlists, cache headers and exact SQL counts. Local bge-m3:
  62 documents / 1,347 chunks; default: 59 documents / 1,134 chunks. The global
  catalog includes other authorized workspace/chunking scopes as well.
- Production ASGI routes with real PostgreSQL fixtures validated two principals,
  two workspaces, cursor subject binding, revoked membership, zero chunks,
  unchanged/failed/changed replacement, revision 409, synthetic warming with
  count/time parity, and scoped cleanup preserving other model/workspace data.
  Fixture transaction always rolled back. No real embedding/chat calls ran.
- Final read-only reconciliation is idempotent: no aliases remain to recover,
  no errors/orphans/unassigned historical zero rows; database readiness true.
- Evidence: `phase_qa/NP20-live-document-catalog.json` and
  `phase_qa/NP20-reconciliation.json`. Operator rollout/rollback and repeatable
  provider-free acceptance commands are in `../database/README.md`.
- No frontend code or production deployment changed. Frontend browser checks
  may now proceed through the canonical contract and shared handoff.

---

# Prior phase — NP-19 Recent Document Metadata API Design

**Status:** Complete — design only, closed 2026-10-02
**Activated:** 2026-10-02
**Owner:** Backend team
**Approval:** User requested full API design on 2026-10-02.

## Objective and scope — NP-19

Design the workspace-authorized recent-document metadata API requested by
frontend FP-10 through FP-12. Resolve identity, display metadata, profile-specific
counts, successful ingestion timestamps, pagination, lifecycle, safe errors,
storage changes, rollout, and acceptance checks from the current implementation.
Deliver a proposal and backend handoff; implementation, schema application,
frontend changes, and live services are outside this design task.

## Task Board — NP-19

| ID | Task | Status | Evidence / outcome |
| --- | --- | --- | --- |
| NP19-01 | Inspect current storage and publish the full recent-document API design and frontend response. | Complete | NP-19: 2026-10-02: Reviewed ingestion, PostgreSQL/Qdrant storage, source/asset/profile lifecycle, loaders, identity and workspace authorization. Published docs/recent_document_metadata_api_design.md and a backend-to-frontend design response; added NP-20 implementation backlog. |

## Validation and Outcome — NP-19

- Published the detailed proposed route/schema, profile semantics, stable
  identity limits, ingestion/warming/empty/failure/deletion lifecycle, exact
  counts, revision-checked keyset pagination, safe error/recovery contract,
  PostgreSQL metadata projection, Qdrant support boundary, migration/backfill,
  rollout/rollback, frontend acceptance, and implementation task plan.
- Validation: reviewed document consistency against the current source and ran
  scoped `git diff --check` for the changed tracked documentation. Checked the
  new design file separately for trailing whitespace/conflict markers. No
  application tests, browser automation, services, model calls, database access,
  or migration execution ran; this task produces a design only.
- Files touched: `docs/recent_document_metadata_api_design.md`,
  `docs/agent_handoff/backend_to_frontend.md`, this record, `docs/next_phase.md`.
  Planned commit boundary: `NP-19: design recent document metadata API`; no
  commit requested or created. NP-20 implementation is proposed in the backlog.

---

# Prior phase — NP-18 Spring Boot Backend Handoff

**Status:** Complete — closed 2026-09-17
**Activated:** 2026-09-17
**Owner:** Project team
**Prerequisite:** User-approved documentation handoff; no application behavior changes.

## Objective

Produce a backend-only implementation handoff for the parallel Kotlin/Spring Boot
project. It will preserve the existing frontend HTTP contract while mapping the
current FastAPI backend's API surface, data model, retrieval/ingestion behavior,
security boundaries, and operational requirements to Spring AI 2.0, with an
optional, isolated Embabel-agent future integration path.

## Scope and exclusions

- In scope: repository inspection, current public API and persistence contract,
  Spring Boot/Kotlin/Spring AI 2.0 design and phased migration plan.
- Out of scope: editing frontend code, changing the Python runtime, starting live
  services, modifying database schema, or choosing immutable dependency versions.

## Task Board

| ID | Task | Status |
| --- | --- | --- |
| NP18-01 | Create Spring Boot backend handoff document from the current implementation and verified upstream documentation. | Complete |

## Validation and Outcome — NP-18

- Created `docs/spring_boot_backend_handoff.md`, covering the fixed frontend
  contract, all current backend routes, authorization, storage, ingestion,
  retrieval, model-profile/cache behavior, Kotlin/Spring AI design, Embabel
  adoption boundary, migration phases, and acceptance gates.
- Verified current Spring AI and Embabel recommendations against their upstream
  documentation on 2026-09-17; the document recommends Boot 4.1.x and Spring
  AI 2.0.x, with Embabel deferred until behavioral parity is proven.
- Validation: `git -c safe.directory=E:/Workspace/AI_Stuff/RAG-dev-plane diff --check`
  completed with no whitespace errors. No application tests were run because
  this task changes documentation only and live services were not authorized.
- Files touched: `docs/spring_boot_backend_handoff.md`, this phase record, and
  `docs/next_phase.md`. No commit created.

## Prior phase record — NP-17 (closed 2026-09-13)

Make embedding-model selection a profile change rather than a re-parsing or
destructive vector-dimension migration. Keep the historical `default` profile
intact while allowing locally warmed or future Azure profiles to coexist.

## Delivered

- Migration 005 provides the `rag.model_profiles` registry and persistent
  `rag.embedding_cache`; profile storage remains provisioned through reviewed
  SQL rather than application DDL.
- Profile-aware ingestion, retrieval, and chat select model dimensions,
  prefixes, storage tables, and cache keys together. Omitted API fields still
  resolve through `MODEL_PROFILE`.
- The active local bge-m3 profile uses its isolated 1024-dimension table;
  the 768-dimension nomic default remains a rollback/reference path.
- The local operator warmer copies one authorized workspace's chunk text and
  provenance into a target profile without re-chunking. Its dry-run response
  reports chunks, cached embeddings, and estimated provider calls.
- The warmer is deliberately unavailable outside `APP_ENV=local`. A gateway
  deployment requires a separately approved operator-authorization design.

## Task Board

| ID | Task | Status |
| --- | --- | --- |
| NP17-01 | Registry/cache migration and profile-table provisioning. | Complete. |
| NP17-02 | Typed profile and cache stores. | Complete. |
| NP17-03 | Prefix-aware cached embedding client with dimension validation. | Complete. |
| NP17-04 | Profile resolution through ingestion, retrieval, and chat. | Complete and live-validated. |
| NP17-05 | Workspace-scoped warmer and dry-run API. | Complete; batched cache inspection and API/unit coverage added. |
| NP17-06 | bge-m3 live warm and multilingual benchmark validation. | Complete: 1,150 chunks warmed; Hebrew and English artifacts recorded. |

## Validation and Outcome

- Full test suite: **86 passed, 1 skipped** (2026-09-13).
- bge-m3 delivered 100% Hebrew source precision, recall, and MRR on the
  13-case golden set. DictaLM completed all Hebrew cases without generation
  failure and materially improved answer relevance/faithfulness over the
  original chat baseline.
- The recommended local pairing is bge-m3 retrieval with DictaLM chat. Keep
  `default`/nomic storage for rollback and comparison.

## Handoff

NP-17 is closed. Future work should select the next explicitly approved item
from `next_phase.md`; Azure exposure of the warmer is intentionally not part of
this phase.

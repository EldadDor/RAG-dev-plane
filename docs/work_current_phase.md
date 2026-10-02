# Current Work Phase — NP-20 Recent Document Metadata API

**Status:** Implementation complete — offline validated; live rollout pending
**Activated:** 2026-10-02
**Owner:** Backend team
**Approval:** User approved NP-19 design and requested implementation on 2026-10-02.

## Objective and scope — NP-20

Implement the approved design in `recent_document_metadata_api_design.md`:
additive PostgreSQL metadata/revision storage, publication lifecycle integration,
authorized listing and signed keyset cursors, offline backfill/reconciliation
tooling, regression coverage, and authoritative frontend documentation.
No frontend changes, production deployment, model calls, live database access,
or migration execution are included in this implementation turn.

## Task Board — NP-20

| ID | Task | Status | Evidence / outcome |
| --- | --- | --- | --- |
| NP20-01 | Metadata migration and catalog store | Complete | NP-20: Added migration 006, per-model metadata/revisions, model-owned asset references, readiness state, consistent scoped reads and PostgreSQL startup validation. Fresh Docker initialization includes migrations 005/006. Migration not executed. |
| NP20-02 | Coordinate ingestion, warming, and directory publication | Complete | NP-20: Atomic vector/catalog publication; per-model hashes and concurrent unchanged guards; zero-chunk replacement; failed-file/scan-coverage protection; workspace-scoped internal UUIDs; immutable asset version IDs and shared lifecycle; profile locks with pinned connections for warm/backfill pool safety. |
| NP20-03 | Authorized list route, schemas, signed cursors and safe errors | Complete | NP-20: GET documents uses principal/membership checks, profile defaults, HMAC cursors, keyset/revision checks, typed safe payloads, private/no-store headers and 409/503 recovery. No model/client/source-loader dependency on GET. |
| NP20-04 | Backfill/reconciliation tooling and offline validation | Offline complete; live pending | NP-20: Read-only default reconciliation and explicit atomic apply/certification; malformed/duplicate/orphan/historical data reporting; updated local workspace-scoped warming CLI. Full offline suite: 132 passed. Migration, real-data reconciliation, and live acceptance not run. |
| NP20-05 | Publish implemented frontend contract and handoff | Complete | NP-20: Updated docs/frontend_architecture.md, database/README.md and backend_to_frontend.md with implemented wire examples, errors/recovery, rollout commands and the remaining live gate. Frontend integration remains pending rollout confirmation. |
| NP20-LIVE | Apply migration/backfill, enable listing, and validate the approved local stack | Pending separate live authorization | NP-20: Required before live phase closure and FP-10 integration. Review read-only backfill report first; no model calls needed for metadata rollout. |

## Validation and Outcome — NP-20

- Full offline command:
  `.venv/Scripts/python.exe -m pytest -q -p no:cacheprovider --basetemp .np20-test-tmp --ignore=tests/integration`
  passed **132 tests** (2026-10-02). Coverage includes safe API authorization,
  configured scopes, normal/unknown-time pagination, cursor tampering/expiry,
  revoked membership, profile/default changes, transaction boundaries/failures,
  concurrent unchanged publication, zero chunks, protected scan failures,
  warming failure/retry, pinned lock adapters, shared image identity, metadata
  sanitization and read-only reconciliation.
- Both operator scripts' `--help` commands passed. Reviewed SQL migration and
  catalog query/write paths; PostgreSQL execution itself is unverified. Scoped
  diff whitespace checks passed. Test temporary files were removed after use.
- The first targeted run hit an existing Windows temp/cache permission issue;
  rerunning with workspace-local `--basetemp` and disabled pytest cache resolved
  it. No application failure remained.
- No frontend changes, browser automation, live database/model/service calls,
  migration application, backfill against real data, enablement, or deployment
  ran. The catalog stays gated until reviewed reconciliation certifies it.
- Files: migration 006; PostgreSQL/Qdrant/protocol adapters; catalog service,
  documents router/schemas; config/dependencies/startup; ingestion/model-profile
  stores/warmer; two operator scripts; .env.example and Docker initialization;
  three focused test modules; API/database/handoff/phase documentation.
- No commit requested or created. NP20-LIVE remains pending as required by the
  approved design's separately authorized live-validation step.

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

# Current Work Phase — NP-22 Recent Chats

**Last reviewed:** 2026-10-03
**Status:** Implementation complete — offline validated; pending commit/phase closure
**Approval:** User instructed “Start NP-22” after committing the intake snapshot as `0eccf9d` (secret-bearing local .env excluded).
**Scope:** Audit session uniqueness, stabilize ordering and fix in-memory rename/archive persistence. Preserve the uncapped bare-array API; FP-15 applies display limits locally. No pagination extension is needed for this phase. No schema, retention, provider, frontend or service configuration changes; rollback is a code revert.

| ID | Task | Status | Evidence / outcome |
| --- | --- | --- | --- |
| NP22-01 | Audit session creation/list/refresh/archive and duplicate semantics | Completed | chat_service uses UUID for new sessions and ensures existing IDs; PostgreSQL session_id is a primary key and fallback metadata is keyed by ID. List filters owner/workspace/non-archived, has no joins/cap; frontend refresh replaces rows. Apparent UI duplicates remain unconfirmed without live reproduction. |
| NP22-02 | Stabilize ordering and fix fallback mutations | Completed | Both stores use updated_at descending, null last, session_id ascending. In-memory rename/archive persist scope-guarded changes under lock; rename matches 200-character store bound, list returns metadata copies. No pagination API added. |
| NP22-03 | Offline regression checks and contract/handoff publication | Completed | 18 focused store/API tests passed, including 105 sessions, duplicate ensure, same titles, timestamp ties/nulls, scope guards, mutation isolation and API rename/archive. Mocked PostgreSQL checks scope/order query; no real SQL execution. Contract and readiness handoff published; diff --check passed. |

**Validation command:** `.venv/Scripts/python.exe -m pytest -q -p no:cacheprovider --basetemp .codex-test-tmp-np22 tests/test_conversation_store.py tests/test_workspace_authorization.py tests/test_api.py` — 18 passed. `git -c safe.directory=E:/Workspace/AI_Stuff/RAG-dev-plane diff --check` — passed.
**Files touched:** src/app/services/conversation_store.py; tests/test_conversation_store.py; tests/test_workspace_authorization.py; docs/frontend_architecture.md; docs/agent_handoff/backend_to_frontend.md; docs/next_phase.md; this record.
**Commit:** Intake snapshot `0eccf9d`; NP-22 implementation uncommitted for review. Formal complete_phases.md entry deferred until committed, as that file requires. Not run: full suite, live PostgreSQL/API/browser/model calls, migrations or services. No frontend/runtime configuration changes.

## Frontend requirements review and backend task intake — 2026-10-03

**Last reviewed:** 2026-10-03
**Scope:** Review the FP-15–FP-17 handoff and create backend phase tasks. User authorization covers this review and planning; feature implementation and live operations remain separate.

| ID | Task | Status | Evidence / outcome |
| --- | --- | --- | --- |
| BE-INTAKE-20261003 | Review frontend requirements, inspect existing contracts/code and record actionable backend tasks | Completed | Reviewed FP-15–FP-17 against chat router, conversation stores, identity, document routes and authoritative contract. Created NP-22–NP-26 with 15 design/implementation/acceptance subtasks, dependencies and approval boundaries in docs/next_phase.md; responded in docs/agent_handoff/backend_to_frontend.md. Scoped git diff --check passed; task-ID/reference review passed. Files touched: these three shared docs. Commit: none. Not run: application tests, browser/live API/model/database calls, migrations or services. |

## Approved cross-runtime configuration follow-up — 2026-10-03

| ID | Task | Status | Evidence / outcome |
| --- | --- | --- | --- |
| RDP20-CONFIG | Persist the shared document-list cursor secret for Python/Kotlin | Completed | User explicitly approved matching secrets and enabling Kotlin listing. Generated a cryptographically random 32-byte secret encoded as 64 ASCII hex characters; securely verified both .env values match and unrelated settings are preserved. Python listing flag remains unchanged. Files: local ignored .env and phase records; commit: none. Not run: tests, live HTTP/browser, providers, database, migrations or service restart. Record was added after the configuration edit; Kotlin intake was recorded before editing. |

Existing NP phase records below are preserved. The updated secret is loaded on the next Python process start; prior process-local cursor tokens must be refreshed.

# Current Work Phase — NP-21 PowerPoint Ingestion

**Status:** Complete — implemented and locally validated 2026-10-02
**Owner:** Backend team
**Approval:** User requested `.pptx` ingestion with text, images, tables, charts
and PowerPoint object handling, integrated with the existing parser behavior.

## Task Board — NP-21

| ID | Task | Status | Evidence / outcome |
| --- | --- | --- | --- |
| NP21-01 | Add safe `.pptx` loader and dependency | Complete | python-pptx 1.0.2, locked dependencies, bounded OOXML validation, registry/directory discovery. |
| NP21-02 | Extract slide content and assets | Complete | Slide/group text, Unicode, tables, cached category/XY/bubble charts, speaker notes, hidden slides, image/preview assets, SmartArt text and explicit unsupported-object metadata. |
| NP21-03 | Preserve slide provenance through normal ingestion | Complete | Slide-local configured chunking with global offsets, citation page/section, package hashing and normal scoped publication/skip/cleanup. |
| NP21-04 | Catalog type and local rollout | Complete | Canonical powerpoint type; migration 007 applied, startup ledger check, Docker initialization, updated API healthy. |
| NP21-05 | Regression/live validation and frontend handoff | Complete | 149 offline tests; real SQL ingestion with synthetic vectors and fixture rollback; usage/extraction limits and frontend type handoff documented. |

## Validation and Outcome — NP-21

- Offline command:
  `.venv/Scripts/python.exe -m pytest -q -p no:cacheprovider --basetemp .np21-test-tmp --ignore=tests/integration`.
  Covers mixed slides, tables, charts/caches, groups, notes, hidden/blank slides,
  SmartArt, OLE previews, Hebrew, source offsets, image-only hash changes,
  external/unavailable content, unsafe packages and normal dry-run/skip/assets.
- Applied the additive catalog constraint migration 007 to the configured local
  PostgreSQL stack and restarted only the project API. Existing data/vectors
  were not re-embedded or rebuilt.
- `scripts/validate_powerpoint_ingestion.py` verified real PostgreSQL publication,
  slide numbers, exact catalog count/type, asset ownership, unchanged timestamp,
  failed/changed replacement and blank-deck cleanup. Temporary SQL records always
  roll back; generated presentation files and in-memory image bytes are removed.
  No real embedding/chat calls or user-deck ingestion ran.
- Evidence: `phase_qa/NP21-live-powerpoint-ingestion.json`. Actual HTTP health,
  readiness and OpenAPI confirm the updated local API and `powerpoint` enum.
- Extraction reads cached text/data and original embedded bytes. It does not
  render slides, perform OCR/visual reasoning, fetch linked resources, interpret
  SmartArt topology, or open embedded files/media. Limits are explicit in
  `powerpoint_ingestion.md`.
- Canonical frontend contract/handoff now advertises `powerpoint` and slide
  citation semantics. No frontend code changed. New feature changes remain
  uncommitted for review; no additional commit was requested in this feature turn.

---

# Prior phase — NP-20 Recent Document Metadata API

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

# Completed Phases

**Purpose:** Sole completed-phase ledger for backend and frontend. New closures
require G4 approval after validation and the approved G3 delivery boundary.
Historical consolidation preserves recorded evidence; it does not grant new approval.

## Phase: NP-23 Profile and Preferences

**Status:** Complete — G4 approved 2026-10-03
**Commit:** `5b315c8` (`NP-23: add approved account preferences`), pushed to `origin/main`; delivery record `d1f5479`.
**Approval:** G1 intake, G2 structural design, G3 delivery and G4 closure explicitly approved by the user.
**Delivered:** Read-only trusted profile/workspace details; strict per-principal recent-chat limit (10/20/50/100, default 10); PostgreSQL persistence with an additive versioned migration; process-lifetime local fallback and explicit unavailable capability; privacy headers and safe errors; published frontend contract and handoff. Existing session-list and retention semantics remain unchanged.
**Validation:** `.venv/Scripts/python.exe -m pytest -q -p no:cacheprovider --basetemp .np23-regression-tmp --ignore=tests/integration -m 'not integration'` — 206 passed. Focused account/workspace/API run — 65 passed. Scoped `git diff --check` passed. No real SQL/API/browser/model calls, migration execution or service operations ran.
**Carry-over:** Operator-authorized migration 008/local rollout and real SQL/API acceptance; gateway origin/CSRF deployment validation; frontend FP-15/FP-16 integration; Kotlin runtime parity with its owner. Migration 008 must be applied before restarting an upgraded PostgreSQL writer.

## Phase: NP-22 Recent Chats

**Status:** Complete — user-approved closure 2026-10-03
**Commit:** `983e8d6` (`NP-22: stabilize recent chat listing`)
**Validation:** 18 focused offline tests passed using `.venv/Scripts/python.exe -m pytest -q -p no:cacheprovider --basetemp .codex-test-tmp-np22 tests/test_conversation_store.py tests/test_workspace_authorization.py tests/test_api.py`; diff whitespace checks passed.

**Delivered:** Deterministic newest-first session listing with null timestamps last and ordinal session-ID ties; persistent, scope-guarded in-memory rename/archive operations; copied list metadata; published unchanged uncapped bare-array contract for FP-15 and frontend readiness handoff.

**Limits:** Apparent frontend duplicates remain unconfirmed. PostgreSQL ordering query tested with mocks; no live SQL/API/browser/model traffic, full suite, migrations or service operations ran. Kotlin runtime parity remains with its owner. NP-23–NP-26 remain backlog candidates.

## Phase: NP-21 PowerPoint Ingestion

**Status:** Complete — implementation/local validation recorded 2026-10-02; historical ledger synchronized 2026-10-03.
**Commit:** `a7e6ce0` (`NP-21: add PowerPoint ingestion support`)
**Delivered:** Safe PPTX extraction of text, groups, tables, cached charts, notes and embedded images; slide-local chunking/provenance; canonical powerpoint catalog type and migration 007.
**Validation:** The preserved NP-21 record below documents 149 offline tests, migration/local rollout and provider-free real SQL fixture validation with rollback; evidence in docs/phase_qa/NP21-live-powerpoint-ingestion.json. No checks rerun during synchronization. No real provider calls, OCR, slide rendering or visual interpretation were claimed. Frontend PowerPoint badge integration remains with its owner.

## Phase: NP-20 Recent Document Metadata API

**Status:** Complete — locally live-validated 2026-10-02  
**Evidence:** `afee99c` (approved-state snapshot), `25ea33b` (local rollout,
recovery fixes, repeatable acceptance and frontend handoff).

**Delivered:**

- Workspace-authorized, profile-scoped document metadata with exact chunk
  counts, safe titles/types, nullable historical times and revision-checked
  signed pagination.
- Migration 006, atomic ingestion/warming/cleanup publication, shared image
  ownership, deployment-wide readiness and operator reconciliation.
- Configured local rollout certified 132 document publications / 2,886 scoped
  chunks across two model profiles. Preserved 32 unscoped legacy vectors,
  excluded with warnings; recovered 568 exact legacy identity aliases.
- Full offline suite: 134 passed. Live HTTP and real PostgreSQL fixtures
  verified count parity, pagination, access/cursors, rollback, zero chunks,
  synthetic warming and scoped cleanup. Fixtures rolled back; no real model
  calls ran. Local health/readiness/listing return 200.
- FP-10–FP-12 frontend integration unblocked in the canonical contract and
  backend handoff. Evidence: `phase_qa/NP20-live-document-catalog.json` and
  `phase_qa/NP20-reconciliation.json`. Browser integration remains frontend-owned.

## Phase: Core RAG Foundation

**Status:** Complete  
**Evidence:** Historical commits through the initial chat/embedding flow,
including `a1caf85` and subsequent correctness fixes.

**Delivered:**

- FastAPI RAG API foundation with separate chat and embedding adapters.
- Document ingestion, chunking, vector-store abstractions, and grounded chat
  answers with source references.
- Local-model configuration and the initial test suite.

## Phase: Durable Chat and Retrieval Quality

**Status:** Complete  
**Evidence:** `ef345b4`, `bec9a48`, `9c1e1bb`, and `df10801`.

**Delivered:**

- Durable conversation memory and session summaries.
- Retrieval safeguards and hybrid semantic plus lexical retrieval.
- Local-model performance controls and safe operational logging.

## Phase: Code-Aware Ingestion and Workspace Source Lifecycle

**Status:** Complete  
**Evidence:** `60c1efb`, `0c8a501`, and `66841f7`.

**Delivered:**

- Python parser-aware chunking with symbols and line ranges.
- Java Tree-sitter parsing with graceful malformed-source fallback.
- Workspace-aware ingestion, content-hash skipping, atomic source replacement,
  and stale-document removal for rescanned directories.
- Workspace filtering through retrieval and chat.

## Phase: Python 3.14 and Expanded Code Support

**Status:** Complete  
**Evidence:** `60113d7` and `deebd8e`.

**Delivered:**

- Python 3.14 project/runtime declaration and Docker image alignment.
- Kotlin loader support with language and repository metadata.
- Supporting test and documentation updates.

## Phase: Validation and Developer Workflow

**Status:** Complete
**Completed:** 2026-08-20
**Commit:** `a73eea9` (`Adding phases docs`)

**Delivered so far:**

- Opt-in live integration test covering the running API, pgvector, embeddings,
  chat grounding, source attribution, workspace isolation, and cleanup.
- Testing guide with unit/integration summaries and PyCharm settings.
- Successful validation: 36 isolated tests, then 37 tests with live integration
  enabled.
- Testing guide indexed into the default workspace.

**Validation:** 36 isolated tests passed; 37 tests passed with the live
integration test enabled. The testing guide was indexed into the default
workspace.

## Phase: Architecture Documentation Refresh

**Status:** Complete
**Completed:** 2026-08-20
**Commit:** `df37f9b` (`Refresh RAG architecture documentation`)
**Validation:** Documentation review, clean diff check, and indexing of the
architecture plus phase records.

**Delivered:**

- Replaced the starter architecture description with the implemented API,
  ingestion, workspace lifecycle, retrieval, memory, provider, persistence,
  and testing flows.
- Added diagrams for system context and chat/retrieval execution.
- Removed the obsolete architecture gap list; approved future work remains in
  `docs/next_phase.md`.

## Phase: NP-08 Non-Destructive Chunking Experimentation Lab

**Status:** Complete
**Completed:** 2026-09-07
**Commit(s):** `d1182fb`, `6ac9570`
**Validation:** `53 passed, 1 skipped` in the isolated suite; migration
`003_chunking_profiles` applied to PostgreSQL; live PowerShell default and
experiment-profile chat queries returned isolated source IDs.

**Delivered:**

- Profile-scoped source-document identity, chunk metadata, ingestion lifecycle,
  semantic retrieval, lexical retrieval, and chat filtering.
- `dry_run` chunk-statistics mode that does not embed or persist data.
- Migration backfill that preserves existing rows as `default`.
- Live experiment evidence: 56 default sources / 465 chunks and one
  `experiment-small` source / 48 chunks, stored separately.

**Deferred:**

- NP-09 evaluates which profile improves retrieval and answer quality.

## Phase: NP-09 Golden Evaluation Set and Regression Harness

**Status:** Complete
**Completed:** 2026-09-09
**Commit(s):** `0de699b`, `4afe8a6`, `5916672`, `c159a94`
**Validation:** `58 passed, 1 skipped` in the offline suite; an approved local
19-case default-profile benchmark wrote
`evaluation/results/baseline-default-expanded.json`.

**Delivered:**

- Strict, human-authored JSONL golden-case schema, loader, and validation
  tests.
- Offline metric and runner seam for source hints, lexical fact coverage,
  faithfulness proxy, failure classification, and retrieval determinism.
- Opt-in local `/chat` benchmark runner with configuration and result artifacts
  that does not alter the document index.
- Decision-grade default-profile baseline: all 19 retrievals deterministic and
  source-hint precision/recall 1.0; `soil` is recorded as the sole
  generation-stage failure.

**Deferred:**

- NP-10 uses this baseline to evaluate cross-encoder reranking.
- Add golden cases only for a new document type, profile, or meaningful
  failure mode.

## Phase: NP-10 Activate Retrieval Reranking

**Status:** Complete
**Completed:** 2026-09-10
**Commit(s):** `dbcb04a`, `3c2a941`
**Validation:** 19 cases × 2 passes for control and reranked configurations;
both runs deterministic.

**Delivered:**

- Optional local cross-encoder reranking over a wider retrieval candidate set.
- Safe disabled-mode and unavailable-model fallback behavior.
- A/B evidence in `evaluation/results/np10-control-rerank-off.json` and
  `evaluation/results/np10-rerank-on.json`.
- Decision to retain `RERANK_ENABLED=false`: context precision/recall were
  saturated and reranking added 50.0% mean latency.

**Deferred:**

- Any future default-enable proposal needs a precision-discriminating dataset
  and an explicit latency budget.

## Record Template

Use this structure for future completed phases:

```markdown
## Phase: <name>

**Status:** Complete
**Completed:** YYYY-MM-DD
**Commit(s):** `<hash>`
**Validation:** <commands/results>

**Delivered:**

- <outcome>

**Deferred:**

- <explicit follow-up, if any>
```

## Historical consolidation — 2026-10-03

The following records were moved from active boards by explicit user request.
They preserve original task outcomes, approvals, validation and limitations.
Statements about pending commits, candidates or old workflow constraints are
historical; the current rules and leading phase entries take precedence.
No new phase closure or application validation is implied by this move.

### Earlier completed backend items

| ID | Recorded outcome | Completion / evidence |
| --- | --- | --- |
| NP-01 | Architecture documentation refresh | 2026-08-20; df37f9b; detailed entry above. |
| NP-02 | Retained production Qdrant warning check; mocked tests disable probe | 2026-08-20; no task-specific commit recorded in the former backlog. |
| NP-03 | Parser-aware Kotlin symbols, line ranges, fallback and unit validation | 2026-08-21; no task-specific commit recorded in the former backlog. |
| NP-04 | Optional safe root tracing foundation | 2026-08-21; nested RAG spans deferred. |
| NP-05 | Workspace discovery/authorization, PostgreSQL migrations/local seed, frontend contract, live validation and documentation indexing | 2026-08-29; no task-specific commit recorded in the former backlog. |
| NP-11 / FP-01 | Frontend closure and live streaming validation | Closure 2026-09-05; unit/type/build checks passed. |
| NP-13–NP-15 / NP-15-FE | Structured Word extraction, private image lifecycle, authorized citations and frontend previews | Live browser validation 2026-09-12. |
| NP-16 | Hebrew/multilingual evaluation; bge-m3 retrieval with DictaLM chat recommended; default/nomic preserved | Closed 2026-09-13; 13 Hebrew and 19 English cases recorded. |
| FP-04 | Workspace selection and session list/load/new-chat flow | Completed 2026-08-29 against approved contract. |
| FP-05 | Bounded history, rename and archive | Completed 2026-08-29. |
| FP-06 | Streaming, citations, cancellation and recovery | Operator browser/API validation 2026-09-03 through IPv4 proxy and live stack. |

### Preserved backend task evidence

### Current Work Phase — NP-22 Recent Chats

#### Phase synchronization — 2026-10-03

| ID | Task | Status | Evidence / outcome |
| --- | --- | --- | --- |
| PHASE-SYNC-20261003 | Reconcile current/backlog/overview/handoff records with committed work | Completed | Reviewed backend/frontend phase boards, handoff, contract and Git history. Updated task_overview.md, next_phase.md, complete_phases.md, agent_handoff/README.md, agent_handoff/decisions.md and this record. Reconciled NP-22 closure, historical NP-21 commit/ledger, frontend readiness and queued dependencies. Git diff --check and targeted status/reference reads passed. Commit: none for this sync; evidence 983e8d6, 32acbb5, a7e6ce0, 0eccf9d. No application tests, live API/browser/model/database calls, migrations or service operations ran. Frontend-owned boards preserved; no new phase activated. |

**Last reviewed:** 2026-10-03
**Status:** Complete — approved, committed and closed 2026-10-03
**Approval:** User instructed “Start NP-22” after committing the intake snapshot as `0eccf9d` (secret-bearing local .env excluded).
**Scope:** Audit session uniqueness, stabilize ordering and fix in-memory rename/archive persistence. Preserve the uncapped bare-array API; FP-15 applies display limits locally. No pagination extension is needed for this phase. No schema, retention, provider, frontend or service configuration changes; rollback is a code revert.

| ID | Task | Status | Evidence / outcome |
| --- | --- | --- | --- |
| NP22-01 | Audit session creation/list/refresh/archive and duplicate semantics | Completed | chat_service uses UUID for new sessions and ensures existing IDs; PostgreSQL session_id is a primary key and fallback metadata is keyed by ID. List filters owner/workspace/non-archived, has no joins/cap; frontend refresh replaces rows. Apparent UI duplicates remain unconfirmed without live reproduction. |
| NP22-02 | Stabilize ordering and fix fallback mutations | Completed | Both stores use updated_at descending, null last, session_id ascending. In-memory rename/archive persist scope-guarded changes under lock; rename matches 200-character store bound, list returns metadata copies. No pagination API added. |
| NP22-03 | Offline regression checks and contract/handoff publication | Completed | 18 focused store/API tests passed, including 105 sessions, duplicate ensure, same titles, timestamp ties/nulls, scope guards, mutation isolation and API rename/archive. Mocked PostgreSQL checks scope/order query; no real SQL execution. Contract and readiness handoff published; diff --check passed. |

**Validation command:** `.venv/Scripts/python.exe -m pytest -q -p no:cacheprovider --basetemp .codex-test-tmp-np22 tests/test_conversation_store.py tests/test_workspace_authorization.py tests/test_api.py` — 18 passed. `git -c safe.directory=E:/Workspace/AI_Stuff/RAG-dev-plane diff --check` — passed.
**Files touched:** src/app/services/conversation_store.py; tests/test_conversation_store.py; tests/test_workspace_authorization.py; docs/frontend_architecture.md; docs/agent_handoff/backend_to_frontend.md; docs/next_phase.md; this record.
**Commit:** Intake snapshot `0eccf9d`; approved NP-22 implementation `983e8d6`. User approved proceeding on 2026-10-03; closure recorded in complete_phases.md. Not run: full suite, live PostgreSQL/API/browser/model calls, migrations or services. No frontend/runtime configuration changes.

#### Frontend requirements review and backend task intake — 2026-10-03

**Last reviewed:** 2026-10-03
**Scope:** Review the FP-15–FP-17 handoff and create backend phase tasks. User authorization covers this review and planning; feature implementation and live operations remain separate.

| ID | Task | Status | Evidence / outcome |
| --- | --- | --- | --- |
| BE-INTAKE-20261003 | Review frontend requirements, inspect existing contracts/code and record actionable backend tasks | Completed | Reviewed FP-15–FP-17 against chat router, conversation stores, identity, document routes and authoritative contract. Created NP-22–NP-26 with 15 design/implementation/acceptance subtasks, dependencies and approval boundaries in docs/next_phase.md; responded in docs/agent_handoff/backend_to_frontend.md. Scoped git diff --check passed; task-ID/reference review passed. Files touched: these three shared docs. Commit: none. Not run: application tests, browser/live API/model/database calls, migrations or services. |

#### Approved cross-runtime configuration follow-up — 2026-10-03

| ID | Task | Status | Evidence / outcome |
| --- | --- | --- | --- |
| RDP20-CONFIG | Persist the shared document-list cursor secret for Python/Kotlin | Completed | User explicitly approved matching secrets and enabling Kotlin listing. Generated a cryptographically random 32-byte secret encoded as 64 ASCII hex characters; securely verified both .env values match and unrelated settings are preserved. Python listing flag remains unchanged. Files: local ignored .env and phase records; commit: none. Not run: tests, live HTTP/browser, providers, database, migrations or service restart. Record was added after the configuration edit; Kotlin intake was recorded before editing. |

Existing NP phase records below are preserved. The updated secret is loaded on the next Python process start; prior process-local cursor tokens must be refreshed.

### Current Work Phase — NP-21 PowerPoint Ingestion

**Status:** Complete — implemented and locally validated 2026-10-02
**Owner:** Backend team
**Approval:** User requested `.pptx` ingestion with text, images, tables, charts
and PowerPoint object handling, integrated with the existing parser behavior.

#### Task Board — NP-21

| ID | Task | Status | Evidence / outcome |
| --- | --- | --- | --- |
| NP21-01 | Add safe `.pptx` loader and dependency | Complete | python-pptx 1.0.2, locked dependencies, bounded OOXML validation, registry/directory discovery. |
| NP21-02 | Extract slide content and assets | Complete | Slide/group text, Unicode, tables, cached category/XY/bubble charts, speaker notes, hidden slides, image/preview assets, SmartArt text and explicit unsupported-object metadata. |
| NP21-03 | Preserve slide provenance through normal ingestion | Complete | Slide-local configured chunking with global offsets, citation page/section, package hashing and normal scoped publication/skip/cleanup. |
| NP21-04 | Catalog type and local rollout | Complete | Canonical powerpoint type; migration 007 applied, startup ledger check, Docker initialization, updated API healthy. |
| NP21-05 | Regression/live validation and frontend handoff | Complete | 149 offline tests; real SQL ingestion with synthetic vectors and fixture rollback; usage/extraction limits and frontend type handoff documented. |

#### Validation and Outcome — NP-21

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

### Prior phase — NP-20 Recent Document Metadata API

**Status:** Complete — local rollout validated, closed 2026-10-02
**Activated:** 2026-10-02
**Owner:** Backend team
**Approval:** User approved NP-19 implementation and the local live rollout.
Current state committed as `afee99c` before migration/backfill/enablement.

#### Objective and scope — NP-20

Deliver the approved recent-document API: additive PostgreSQL catalog/revisions,
atomic publication across ingestion/warming/cleanup, authorized discovery,
revision-checked cursors, safe display metadata, reconciliation and frontend
contract. The local rollout is complete. Frontend integration/browser validation
belongs to FP-10–FP-12; other environments require their own rollout.

#### Task Board — NP-20

| ID | Task | Status | Evidence / outcome |
| --- | --- | --- | --- |
| NP20-01 | Metadata migration and catalog store | Complete | Migration 006 applied locally; per-model metadata/revisions, model-owned assets, readiness, scoped snapshot reads and startup checks. |
| NP20-02 | Coordinate ingestion, warming and directory publication | Complete | Atomic publication, per-model unchanged guards, zero chunks, scan protection, workspace-safe internal IDs, shared asset ownership and pinned publication locks. |
| NP20-03 | Authorized route, schemas, cursors and safe errors | Complete | Principal/membership on every page; configured scopes; HMAC cursors, revision/keyset pagination, safe typed fields, private/no-store headers. |
| NP20-04 | Reconciliation and regression validation | Complete | 134 offline tests passed; reviewed/applied backfill, exact legacy alias recovery, idempotent final report and zero all-scope SQL count mismatches. |
| NP20-05 | Frontend contract and handoff | Complete | frontend_architecture.md and backend_to_frontend.md publish validated contract; FP-10–FP-12 unblocked. |
| NP20-LIVE | Local rollout and live acceptance | Complete | 132 publications across 2 profiles; 2,886 scoped chunks, 32 unscoped preserved/excluded. Listing enabled, API healthy; acceptance evidence saved. |

#### Validation and Outcome — NP-20

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

### Prior phase — NP-19 Recent Document Metadata API Design

**Status:** Complete — design only, closed 2026-10-02
**Activated:** 2026-10-02
**Owner:** Backend team
**Approval:** User requested full API design on 2026-10-02.

#### Objective and scope — NP-19

Design the workspace-authorized recent-document metadata API requested by
frontend FP-10 through FP-12. Resolve identity, display metadata, profile-specific
counts, successful ingestion timestamps, pagination, lifecycle, safe errors,
storage changes, rollout, and acceptance checks from the current implementation.
Deliver a proposal and backend handoff; implementation, schema application,
frontend changes, and live services are outside this design task.

#### Task Board — NP-19

| ID | Task | Status | Evidence / outcome |
| --- | --- | --- | --- |
| NP19-01 | Inspect current storage and publish the full recent-document API design and frontend response. | Complete | NP-19: 2026-10-02: Reviewed ingestion, PostgreSQL/Qdrant storage, source/asset/profile lifecycle, loaders, identity and workspace authorization. Published docs/recent_document_metadata_api_design.md and a backend-to-frontend design response; added NP-20 implementation backlog. |

#### Validation and Outcome — NP-19

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

### Prior phase — NP-18 Spring Boot Backend Handoff

**Status:** Complete — closed 2026-09-17
**Activated:** 2026-09-17
**Owner:** Project team
**Prerequisite:** User-approved documentation handoff; no application behavior changes.

#### Objective

Produce a backend-only implementation handoff for the parallel Kotlin/Spring Boot
project. It will preserve the existing frontend HTTP contract while mapping the
current FastAPI backend's API surface, data model, retrieval/ingestion behavior,
security boundaries, and operational requirements to Spring AI 2.0, with an
optional, isolated Embabel-agent future integration path.

#### Scope and exclusions

- In scope: repository inspection, current public API and persistence contract,
  Spring Boot/Kotlin/Spring AI 2.0 design and phased migration plan.
- Out of scope: editing frontend code, changing the Python runtime, starting live
  services, modifying database schema, or choosing immutable dependency versions.

#### Task Board

| ID | Task | Status |
| --- | --- | --- |
| NP18-01 | Create Spring Boot backend handoff document from the current implementation and verified upstream documentation. | Complete |

#### Validation and Outcome — NP-18

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

#### Prior phase record — NP-17 (closed 2026-09-13)

Make embedding-model selection a profile change rather than a re-parsing or
destructive vector-dimension migration. Keep the historical `default` profile
intact while allowing locally warmed or future Azure profiles to coexist.

#### Delivered

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

#### Task Board

| ID | Task | Status |
| --- | --- | --- |
| NP17-01 | Registry/cache migration and profile-table provisioning. | Complete. |
| NP17-02 | Typed profile and cache stores. | Complete. |
| NP17-03 | Prefix-aware cached embedding client with dimension validation. | Complete. |
| NP17-04 | Profile resolution through ingestion, retrieval, and chat. | Complete and live-validated. |
| NP17-05 | Workspace-scoped warmer and dry-run API. | Complete; batched cache inspection and API/unit coverage added. |
| NP17-06 | bge-m3 live warm and multilingual benchmark validation. | Complete: 1,150 chunks warmed; Hebrew and English artifacts recorded. |

#### Validation and Outcome

- Full test suite: **86 passed, 1 skipped** (2026-09-13).
- bge-m3 delivered 100% Hebrew source precision, recall, and MRR on the
  13-case golden set. DictaLM completed all Hebrew cases without generation
  failure and materially improved answer relevance/faithfulness over the
  original chat baseline.
- The recommended local pairing is bge-m3 retrieval with DictaLM chat. Keep
  `default`/nomic storage for rollback and comparison.

#### Handoff

NP-17 is closed. Future work should select the next explicitly approved item
from `next_phase.md`; Azure exposure of the warmer is intentionally not part of
this phase.

### Preserved frontend task evidence

### Current Frontend Work Phase — FP-02 Frontend Hardening and UX Refinement

**Status:** FP-02 completed; FP-10–FP-12 implemented and locally validated
**Last reviewed:** 2026-10-03
**Owner:** Frontend team

#### Objective

Harden the accepted React chat experience with focused accessibility,
responsive-layout, recovery-state, and regression-test work. The phase is
limited to the existing frontend and proxy-only API contract.

#### Scope and Guardrails

- Work only in `frontend/**`; the API contract is read-only unless separately
  approved by the backend owner.
- Keep the existing relative Vite/Nginx proxy integration. Do not add browser
  secrets, identity headers, direct backend URLs, or live-service traffic.
- Keep automated coverage unit-focused. Browser automation, end-to-end tests,
  visual regression tooling, and new dependencies require separate approval.
- Do not change archive wording, office deployment, ingestion, or
  administrative features.

#### Task Board

| ID | Task | Status | Evidence / outcome |
| --- | --- | --- | --- |
| FP2-01 | Audit and harden keyboard, screen-reader, and recoverable-error behavior | Completed | 2026-09-05: Added in-place workspace/session retry controls, `aria-busy` chat state, alert/status semantics for recoverable stream states, a labelled rename form, source updates, and `aria-current` on the active session. Added an SSE-incomplete unit regression. Passed Vitest (4 tests), `tsc -b`, and Vite production build; no live services or browser automation ran. |
| FP2-02 | Refine narrow and wide responsive layout behavior | Completed | 2026-09-05: Preserved the existing desktop grid and added narrow-layout safeguards for the workspace picker, chat heading/actions, rename controls, pane padding/tabs, and conversation bubble width. Passed Vitest (4 tests), `tsc -b`, and Vite production build; no browser automation or live services ran. |
| FP2-03 | Extend focused unit regression coverage | Completed | 2026-09-05: Added Node-environment coverage for session-detail mapping, encoded rename/archive requests, incomplete SSE streams, and safe terminal SSE errors. Vitest now passes 6 tests; `tsc -b` and the production build pass. No new dependencies, browser automation, or live services were used. |
| FP2-04 | Run local validation and prepare phase handoff | Completed | 2026-09-05: Passed Vitest (6 tests), `tsc -b`, Vite production build, and `git diff --check`. The audit found no API-contract discrepancy, so no backend handoff was required. Browser automation and live-stack validation did not run because they are outside the approved scope. Changes are ready for review and commit. |
| FP-07 | Restructure the Vite frontend for independently buildable applications | Completed | 2026-09-13: Moved the existing SPA to `frontend/apps/rag-dev-plane`, added app-scoped Vite configuration and root `build:all`/`build:rag-dev-plane` scripts, and configured output at `frontend/build/dist/rag-dev-plane`. Passed Vitest (7 tests), `tsc -b`, direct Vite production build, and `git diff --check`; the sandbox runtime provides Node but not npm, so `npm run build:all` itself was not invoked. No live services or browser automation ran. Branch: `codex/multi-app-vite-structure`. |
| FP-08 | Make source citations individually expandable | Completed | 2026-09-14: Source citations now start collapsed, expose an accessible per-source toggle, and animate their metadata, excerpt, and linked image content independently. The transition disables under reduced-motion preferences; collapsed image links are not keyboard-focusable. Passed Vitest (7 tests), `tsc -b`, direct Vite production build, and `git diff --check`. No live services or browser automation ran. |
| FP-09 | Record UI enhancement tasks and document metadata dependency | Completed | FP-09: 2026-10-02: Added FP-10 recent documents, FP-11 configurable chunk-size indicators, and FP-12 document-type colors with acceptance criteria, dependencies, validation, and commit boundaries in next_phase.md. Recorded missing metadata contract in docs/agent_handoff/frontend_to_backend.md. Verified written records with targeted reads; no application code changed. Type checks, tests, builds, browser automation, and live services were not run (documentation-only intake). |
| FP-10 | Recent ingested documents in the left panel | Completed | FP-10: 2026-10-02: Implemented api.ts, documentCatalog.ts, DocumentsPanel.tsx, App.tsx and styles.css: relative scoped API, newest-first server ordering, refresh/load-more, no polling, abort/stale guards, one 409 restart, scope/revision checking, 401/403 clearing and 403 discovery, 503 retry, null ingestion history, valid zero counts, Hebrew/long-name and narrow-layout handling. Passed 34 Vitest tests including pagination/restart/abort regressions, tsc -b, Vite build and git diff --check. No browser automation or live services ran; manual browser integration remains unverified. Commit: c58e667. |
| FP-11 | Configurable chunk-count size indicators | Completed | FP-11: 2026-10-02: documentBadges.ts centralizes inclusive upper bounds 25/100/500 and size colors; Small/Medium/Big/Extra-Large text badges, exact chunk totals and expandable guide render in DocumentsPanel.tsx. Zero is Small; invalid/missing counts are Unknown. Boundary/invalid-value unit coverage passed in 34-test suite; tsc -b and production build passed. Commit: c58e667. |
| FP-12 | Configurable document-type colors | Completed | FP-12: 2026-10-02: documentBadges.ts maps word/pdf/markdown/html/text/code/unknown to configurable color pairs and explicit text labels; separate type/size badges in DocumentsPanel.tsx with future-type fallback. Unit tests cover canonical, future and inherited object keys. Passed 34 Vitest tests, tsc -b, Vite production build and git diff --check; no dependencies, browser automation or live services added. Commit: c58e667. |
| FP-13 | Record UI behavior requirements and backend API handoff | Completed | FP-13: 2026-10-03: Added FP-14 through FP-17 requirements, acceptance criteria, ordering, dependencies and validation in next_phase.md; recorded account/preferences/logout, document overview/preview and session-list clarification in docs/agent_handoff/frontend_to_backend.md. Evidence: read frontend_architecture.md first; rtk read next_phase.md and targeted handoff/phase rereads verified records. Documentation only; no application code, API contract edits or commit. Type checks, tests, builds, browser automation and live services not run. |

#### Acceptance Checks

- Keyboard and screen-reader behavior is verified for workspace, session,
  composer, citation, rename, and archive interactions.
- Narrow and wide layouts preserve readable chat, recent-session, and source
  navigation.
- Recoverable API/SSE failures have consistent retry and focus behavior.
- Focused regression tests, type checks, and the production build pass without
  live backend/model/database services.
- Approved live-stack validation, if requested, passes the existing operator
  checklist for streaming completion and cancellation.

#### Approval Gates

- [x] Approve FP-01 acceptance and FP-02 activation, acceptance criteria, and
  unit-test scope. Approved 2026-09-05.
- [ ] Approve any additional dependency, proxy/authentication change, browser
  automation, visual-regression tooling, or live-service validation before use.
- [x] Approve FP-02 phase closure after its accepted local-scope checks pass.
  Approved 2026-09-05.

#### Execution Constraints

- Update the task board and **Last reviewed** before and after every task.
- Do not start a planned task until its prior task is recorded as completed,
  blocked, or deferred.
- Do not start Uvicorn or contact model/database services without explicit
  approval. Record backend gaps in the frontend-to-backend handoff instead of
  changing backend code.

#### Phase Handoff

Keep existing proxy-only API behavior: no browser user ID or identity headers;
refresh workspace discovery for `403`; and remove unavailable sessions for
`404`. Raise any contract gap through the frontend-to-backend handoff. FP-02
was formally closed with the approved unit-focused validation scope on
2026-09-05.

Status review, 2026-09-12: FP-02 remains complete. The backend's
image-bearing-citation handoff is contract-aligned with the implemented
frontend, and the live browser checklist passed: a grounded Hebrew Word result
rendered its associated PNG in Related source images. No frontend code or
contract change was required.

Hebrew-ingestion review, 2026-09-12: this is backend-owned work, so no
frontend task was started. Recorded the benchmark-first and profile-isolation
requirements in `docs/agent_handoff/frontend_to_backend.md`. Evidence: reviewed
the supplied Perplexity thread, official DICTA and Ollama model documentation,
and official OpenAI embedding documentation. No application code, service,
model, database, or frontend validation command ran.

UI enhancement validation, 2026-10-02: user authorized proceeding after the
NP-20 rollout handoff. Local commands passed:
`node node_modules/typescript/bin/tsc -b`,
`node node_modules/vitest/vitest.mjs run` (34 tests),
`node node_modules/vite/bin/vite.js build --config apps/rag-dev-plane/vite.config.ts`,
and scoped `git diff --check` with a per-command safe.directory override.
Direct Node entry points were used because npm is not available in the sandbox.
No Uvicorn, model/database calls, live API traffic, browser automation, or
manual browser integration ran. No commit created. Backend contract unchanged.

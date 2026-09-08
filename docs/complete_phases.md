# Completed Phases

**Purpose:** Immutable-style record of completed, validated work. Add a new
entry only after its phase is approved, verified, and committed.

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

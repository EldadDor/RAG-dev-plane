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

**Status:** In progress — close only after the approval gate in
`docs/work_current_phase.md` is accepted and the working tree is committed.

**Delivered so far:**

- Opt-in live integration test covering the running API, pgvector, embeddings,
  chat grounding, source attribution, workspace isolation, and cleanup.
- Testing guide with unit/integration summaries and PyCharm settings.
- Successful validation: 36 isolated tests, then 37 tests with live integration
  enabled.
- Testing guide indexed into the default workspace.

**Outstanding:** Commit the approved workflow/documentation cleanup and record
the resulting commit hash here.

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

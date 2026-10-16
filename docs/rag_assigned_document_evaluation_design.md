# RAG-C-03: assigned-document evaluation

**Reviewed:** 2026-10-16. **Status:** G2 approved; implemented and offline-validated. Live acceptance pending.
**Decision already approved:** Retain pypdf as the production default.

## Problem and chosen approach

The [saved-answer review](../evaluation/pdf_parsers/corpus/STAGE_C_ANSWER_REVIEW.md)
shows wrong-document answers even when the expected document was retrieved.
The five frozen negatives describe absence within an assigned document, not
the entire workspace. Current chat requests cannot enforce that boundary;
`GoldenCase` also requires nonempty positive facts.

Add one optional `document_id` to the existing chat request and thread it through
both chat routes, retrieval and vector-store search. Apply exact document
filtering together with workspace/model/chunking scope **before candidate ranking
and LIMIT**, in both semantic and lexical search. Keep document-scoped calls
stateless so other documents' conversation history cannot contaminate them.
Extend the existing evaluator to represent negatives and score exact abstention
separately. Use existing modules, dependencies, data and migrations.

Rejected alternatives:

- Filtering returned top-k citations: other documents can crowd out the assigned
  document before filtering, and generation may already have seen their text.
- One new workspace per document/treatment: avoids an API change but requires
  duplicate publication, authorization and lifecycle state for up to 43 currently
  publishable treatment/document pairs; it also tests a different corpus layout.
- Adding the filename to the question: changes frozen question bytes and cannot
  enforce retrieval scope.

## Approved HTTP behavior

`POST /chat` and `POST /chat/stream` gain optional
`document_id: string | null`, exactly 64 lowercase hexadecimal characters,
matching current `make_doc_id` output. Omitted/null preserves existing behavior.
The ID is an exact opaque identity, not a path, substring or authorization grant.
Existing workspace authorization and model/profile validation still apply.

For an explicit document ID:

- Reject a supplied `session_id` with the existing safe 422 envelope, before
  opening an SSE response. No session history, rewriting, summaries or conversation
  writes run. Return `session_id: null`, including the stream meta event.
- Use only that document's chunks in the resolved authorized workspace and
  model/chunking scope. Missing document/no eligible chunks yields the existing
  ungrounded empty-source answer; never broaden to another document or profile.
  This does not assert that the document was successfully indexed.
- Check returned chunk IDs' document identities before generation; a backend
  returning an out-of-scope chunk fails closed through the safe upstream-error
  envelope (or existing SSE error/done sequence), rather than silently filtering
  an already limited set or sending it to the model.
- Preserve source payloads, 300-character snippets and SSE event names. Do not
  expose complete chunks through public debug output. `grounded` keeps its current
  meaning (retrieved context exists), not correctness or abstention acceptance.

This intentionally introduces no document-selector UI or scoped chat memory.
The current frontend continues omitting the field. Update the authoritative
[API contract](frontend_architecture.md) only after implementation/validation;
the API document records the implemented behavior and live-validation limits.

## Store and service changes

Add an optional trailing document parameter to existing `VectorStore.search`,
`LexicalSearchVectorStore.search_text` and `RetrievalService.retrieve` signatures.
Preserve omission behavior for existing callers, adapters and test doubles.
Both semantic and lexical branches receive the same filter before fusion and
reranking; changing candidate limits is not a substitute for filtering.

PostgreSQL: add a parameterized exact metadata doc-ID predicate to both existing
search statements. Keep workspace/chunking predicates and selected profile table.
No string interpolation of user IDs, new table, migration or startup DDL.
Qdrant: add an exact `doc_id` must-condition to the existing workspace/chunking
filter; preserve semantic-only behavior where lexical search is unsupported.
An unsupported adapter must fail closed on a scoped call, never retry unscoped.

`ChatService` selects the stateless branch before session creation/history access
and uses the same answer/context construction as ordinary chat. Thread the ID
through synchronous and streaming wrappers. Empty retrieval uses existing
abstention behavior but skips all session writes in scoped mode. No provider or
parser default changes, new wiring pattern, dependency or SQL migration.

## Dataset, runner and negative scoring

Extend existing evaluation models with optional `document_id` and
`answerable: bool = true`. Existing datasets remain valid. Positives require
nonempty facts; negatives require an explicit false boolean, empty facts and
an explicit document ID. Reject inconsistent values and non-boolean flags.
Preserve frozen questions, facts, IDs and negative-scope annotations in derived
data; omit only the already recorded invalid descriptive reference fact.

Update the existing preparation script with an explicit assigned-document mode.
Resolve source identities using `make_doc_id` and the frozen manifest. Include
positives and negatives only for successfully indexed documents with chunks;
retain all exclusions in availability evidence. Keep current workspace-wide
positive-only preparation as the default. A scoped run is a new experiment:
do not relabel or overwrite Stage C's 99 original workspace-wide answers.

The live adapter forwards document scope on both deterministic retrieval probes
and answer lookup. Include document ID in its response-cache key. Record both
probe responses in a new private artifact so the answer, citations and retrieved
order from each request remain attributable. Current probes invoke generation
twice; report that cost explicitly. They expose snippets, not complete contexts.

For negatives, set positive fact-coverage/faithfulness proxies to null. Record
`abstained` as 1 only when a nonempty successful answer, after whitespace
normalization, exactly equals one of the two existing canonical refusals:

- `I don't have enough information in the indexed documents to answer this question.`
- `I don't know based on the indexed documents.`

Other successful answers score 0 under this strict observable policy. Empty
answers, transport/provider failures, malformed payloads, scope violations and
unavailable documents are failures/unavailable, never successful abstentions.
A refusal followed by an invented value scores 0. Noncanonical but appropriate
refusals require manual review; do not call their 0 score factual fabrication.
Do not use an empty fact list's current coverage=1 behavior, `grounded=false`,
absence of citations or substring matching to declare success. Report negative
counts separately from positive proxy metrics and extraction availability.

Expected eligible negatives from current publication evidence (not fresh checks):

| Case | pypdf | No OCR | OCR |
| --- | --- | --- | --- |
| pdf-001-q3 | Available | Available | Available |
| pdf-002-q3 | Available | Unavailable | Unavailable |
| pdf-003-q3 | Available | Available | Available |
| pdf-008-q3 | Available | Unavailable | Unavailable |
| pdf-010-q3 | Available | Unavailable | Available |

Thus at most 5/2/3 negative answers are eligible without new extraction.
pdf-003-q3 retains its page-9 qualifier. This proposal enforces document scope,
not a page filter: its approved absence check also reports no numeric thresholds
in the full document. Cross-page attribution and subsection-specific distractors
(such as the duel timer versus solo rules) still require source-based review.
Do not generalize these five references into whole-workspace absence judgments.

## Validation, rollout and rollback

After G2 approval, add focused offline tests in existing test modules for:

1. Old payloads/datasets and unscoped session/SSE behavior remain compatible;
   malformed IDs and scoped-plus-session requests reject before streaming.
2. Workspace denial is unchanged; another workspace/profile/document cannot
   supply context. Scoped calls do not read/write any conversation state.
3. Semantic/lexical SQL and Qdrant filters apply before LIMIT; hybrid/reranker
   paths preserve scope and leaked candidates fail before generation.
4. Positive/negative schema consistency, strict refusal policy, fabricated
   refusal suffixes, unavailable documents and transport failures stay distinct.
5. Cache keys and saved first/second responses include exact request scope;
   preparation preserves hashes/questions and the 5/2/3 availability calculation.

Run the smallest relevant API/service/store/evaluation/preparation suites with
mocks, plus whitespace/link checks. Do not infer live acceptance from mocks.
Live reruns need operator approval for the concrete API reload and benchmark
calls. They must verify authentication and current publication identity/counts
before running; no implicit service restart, model download or reingestion.
Save new artifact names/hashes and label scope; compare candidates only on
matching cases and never overwrite the frozen release or old reports.

Rollback is a source revert of this additive API/evaluator change. No database
migration or data rollback is required. Existing callers omit the field and keep
their behavior; scoped datasets/artifacts remain separate and cannot be run on
an older API as though scope had been enforced. Check API capability explicitly
before a scoped live run, since an older server may ignore an unknown field.
Do not count matching returned citations alone as proof the request was scoped.

## Approved G2 scope

User approved the optional single-document, stateless chat mode; exact store-side
semantic/lexical filtering in PostgreSQL and Qdrant; and the existing-module
evaluator/preparation changes above. Migration: none. Alternatives and rollback
are stated above. Full retrieved-chunk capture, page-filter APIs, scoped session
memory and independent correctness acceptance remain separate work.

Design preparation on 2026-10-15 performed source/contract tracing and frozen negative
availability checks only. No application implementation/tests, providers,
stores, service changes, push/merge or phase closure were performed.


## Implementation evidence (2026-10-16)

G2 was explicitly approved by the user for RAG-C-03. Implemented in the existing
API/service/store/evaluation modules and preparation/benchmark scripts. The
[API contract](frontend_architecture.md) owns request/stateless-response behavior;
[runner instructions](../evaluation/pdf_parsers/README.md) own operational use.
`CaseResult.response_indices` points into the private paired-response artifact;
the report records its hash and the dataset hash. Faithfulness proxies use the
second probe's snippets, matching the generated answer, while retrieval
precision/recall/MRR and stored chunk IDs describe the first probe.
Zero-count unchanged ingestion reports cannot establish document availability.
No new module, dependency, migration or default-parser change.

114 focused offline tests passed, using mocked API/providers/stores and synthetic
prepared-PDF fixtures. The first sandbox run stalled and was interrupted;
fixture runs under the repository and home temp were rejected by the existing
private-output guards. The final run used a new external, non-Git scratch directory.
Full application/integration suites, live API reload, benchmark calls and
independent answer acceptance were not run. Local changes are uncommitted;
G3 push/merge and G4 closure remain separate.


Frozen-corpus preparation was subsequently exercised without live services:
47/30/32 eligible cases, comprising 42/28/29 positives and 5/2/3 negatives.
[Preparation evidence](../evaluation/pdf_parsers/corpus/RAG_C03_PREPARATION.json)
records the six new private artifact hashes; all 17 original Stage C artifact
hashes were rechecked. This establishes dataset readiness from saved reports,
not current database publication or benchmark acceptance.

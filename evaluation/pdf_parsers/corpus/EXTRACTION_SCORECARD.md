# Frozen-case extraction review and picture-child correction

**Task:** RAG-B-SCORE / RAG-B-CHILD
**Reviewed:** 2026-10-14
**Decision:** Keep pypdf as production default. A normalization omission is corrected in the experimental Docling adapter.

**Later follow-up:** [v4 text audit and v5 corrections](NORMALIZATION_FIDELITY_REVIEW.md)
preserve picture-parent links and recover `document_index` tables. The earlier
upstream-contents diagnosis below is corrected: raw cells existed but were
normalized as empty text. Original/v4 scores are retained; v5 has no aggregate score.

## Scope and scoring

Codex reviewed the approved facts against the original cold normalized text on each recorded evidence page. These are assistant qualitative judgments against human-approved references, not independent human adjudication or generated-answer scores. The original runs are preserved. One cold result per case is scored; warm outputs are stability checks, not extra samples.

R = retained; P = partial, corrupted identifier or reading-order reconstruction required; M = missing; U = unavailable due to original timeout; X = excluded reference defect. Benign punctuation spacing/Unicode ligatures are tolerated, but words are not reordered and arbitrary glyph repairs are not inferred. Grouped reference facts remain indivisible.

47 cases comprise 42 answerable cases and five assigned-document negatives reserved for retrieval/answer evaluation. Of 153 expected-fact groups, one descriptive source-page claim in pdf-007-q3 is excluded because it contradicts the approved evidence. The requested Egan/publication/page-25 fact is scored. Frozen bytes remain unchanged.

## Original-output coverage

| Original treatment | All valid facts retained in case | R / 152 | P | M | U |
| --- | --- | --- | --- | --- | --- |
| pypdf baseline | 36/42 | 139/152 | 9 | 4 | 0 |
| PDFium no OCR | 30/42 | 109/152 | 6 | 25 | 12 |
| PDFium Tesseract OCR | 29/42 | 104/152 | 6 | 21 | 21 |

These counts describe the original outputs, before the picture-child correction. They are not pass rates for the changed adapter. The case denominator includes timeouts. Facts are unevenly grouped: the 17-label question carries much more fact weight than most prose questions; use case and fact counts together.

## Corrected omission

Docling Core 2.101.1 defaults iterate_items(traverse_pictures=False), visiting picture captions but skipping other nested children. The raw exports contain the beginner-die fact and diagram labels which our default traversal omitted. The existing adapter now explicitly traverses picture children and uses normalization policy picture_children_export_clamp_pages_without_boxes_v4, giving changed processing/block identities. Existing geometry-warning and partial-output handling remain in place.

47 focused offline adapter/loader tests passed. Replaying all 31 available saved Docling exports through the changed adapter adds 1,743 blocks while preserving every old source-ref text and image-byte hash; new IDs are disjoint and normalized offsets/provenance validate. This replay uses recorded pipeline settings, does not initialize models, and does not establish fresh cold/warm timing or native-runtime acceptance. Original timeout cases remain unavailable.

| Targeted replay review, both treatments | Original | Replayed |
| --- | --- | --- |
| pdf-002-q1 component facts | 3/4 retained | 4/4; beginner die recovered |
| pdf-003-q1 diagram labels | 0/17 retained | 16/17 retained, one partial: upstream Wayfinding glyph corruption remains |
| pdf-004-q3 contents entry/page | 0/2 retained | 0/2 in v4; raw document-index cells were omitted by adapter mapping, corrected in v5 |
| pdf-012-q1 fine-tuning diagram facts | 1 retained / 1 partial / 1 missing | 3/3 retained; graph topology not certified |

The replay is a separate treatment. No full-corpus score is assigned to it: newly exposed OCR noise and associations require their own review. [Replay evidence](PICTURE_CHILD_REPLAY.json) records raw/normalized hashes and source-ref counts; detailed outputs stay outside Git. The first failed helper attempt is retained separately; r2 is the successful replay.

## Remaining fidelity work

1. Review v4 newly exposed text, particularly OCR garbage in pictures, without suppressing real labels. Separate fact coverage from added false text.
2. Contents omission diagnosed and corrected in v5 document-index mapping; malformed font/glyph decoding remains. Do not patch text from expected answers or introduce an implicit fallback.
3. Preserve table row/column links: pdf-014 stage-5 continuation appears in stage-6 row; other tables show merged/shifted cells.
4. Preserve logical RTL and mixed-script identifiers: Item New Add / Form Web / aspx.Default remain wrong in pdf-015; pdf-002 section order remains wrong.
5. Retain fixed-budget timeouts and unresolved geometry limits. Complete-case text coverage does not waive provenance/resource gates before Stage C.

No CER is reported: the references are selective facts/quotes, not complete page transcripts. Diagram label presence does not certify leader-line edges. This review does not certify all table cells, whole-document text, zero wrong boxes or aggregate RTL reading order. Five negatives cannot be scored by declaring the parser abstained. No live providers, stores, SQL, production ingestion or model reruns occurred.

## Original case-level review

R count / eligible fact groups; suffixes show P/M, or U for timeout. The dagger identifies the reference exclusion. Full rationale, fact-index grades and artifact/page-text hashes are in [the review data](COLD_CASE_REVIEW.json).

| Case | pypdf | No OCR | OCR |
| --- | --- | --- | --- |
| pdf-001-q1 | 2/2 | 2/2 | 2/2 |
| pdf-001-q2 | 3/3 | 3/3 | 3/3 |
| pdf-002-q1 | 4/4 | 3/4 +1M | 3/4 +1M |
| pdf-002-q2 | 4/4 | 4/4 | 4/4 |
| pdf-003-q1 | 16/17 +1P | 0/17 +17M | 0/17 +17M |
| pdf-003-q2 | 4/4 | 3/4 +1P | 3/4 +1P |
| pdf-004-q1 | 4/4 | 4/4 | 4/4 |
| pdf-004-q2 | 5/5 | 5/5 | 5/5 |
| pdf-004-q3 | 2/2 | 0/2 +2M | 0/2 +2M |
| pdf-005-q1 | 3/3 | 3/3 | 3/3 |
| pdf-005-q2 | 3/3 | 3/3 | 3/3 |
| pdf-005-q3 | 3/3 | 3/3 | 3/3 |
| pdf-006-q1 | 4/4 | 4/4 | 0/4 +4U |
| pdf-006-q2 | 2/2 | 2/2 | 0/2 +2U |
| pdf-006-q3 | 3/3 | 3/3 | 0/3 +3U |
| pdf-007-q1 | 0/2 +2P | 2/2 | 2/2 |
| pdf-007-q2 | 0/5 +5P | 5/5 | 5/5 |
| pdf-007-q3 | 1/1 † | 1/1 † | 1/1 † |
| pdf-008-q1 | 2/2 | 2/2 | 2/2 |
| pdf-008-q2 | 4/4 | 4/4 | 4/4 |
| pdf-009-q1 | 2/2 | 2/2 | 2/2 |
| pdf-009-q2 | 2/2 | 2/2 | 2/2 |
| pdf-009-q3 | 3/3 | 3/3 | 3/3 |
| pdf-010-q1 | 0/1 +1M | 0/1 +1M | 1/1 |
| pdf-010-q2 | 0/3 +3M | 0/3 +3M | 3/3 |
| pdf-011-q1 | 2/2 | 2/2 | 2/2 |
| pdf-011-q2 | 3/3 | 3/3 | 3/3 |
| pdf-011-q3 | 4/4 | 4/4 | 4/4 |
| pdf-012-q1 | 3/3 | 1/3 +1P +1M | 1/3 +1P +1M |
| pdf-012-q2 | 3/3 | 3/3 | 3/3 |
| pdf-012-q3 | 4/4 | 4/4 | 4/4 |
| pdf-013-q1 | 2/2 | 2/2 | 2/2 |
| pdf-013-q2 | 5/6 +1P | 6/6 | 6/6 |
| pdf-014-q1 | 5/5 | 4/5 +1P | 4/5 +1P |
| pdf-014-q2 | 4/4 | 4/4 | 4/4 |
| pdf-015-q1 | 2/2 | 2/2 | 2/2 |
| pdf-015-q2 | 5/5 | 2/5 +3P | 2/5 +3P |
| pdf-016-q1 | 3/3 | 0/3 +3U | 0/3 +3U |
| pdf-016-q2 | 6/6 | 0/6 +6U | 0/6 +6U |
| pdf-016-q3 | 3/3 | 0/3 +3U | 0/3 +3U |
| pdf-017-q1 | 3/3 | 3/3 | 3/3 |
| pdf-017-q2 | 6/6 | 6/6 | 6/6 |

## Integrity evidence

192 original normalized outputs and 51 source/reference snapshot pairs were verified against the frozen release; available cold/warm text and IDs are stable. Original manifest SHA-256: a84483eabfeeba04232dc365709f9e8bec26b9c2b195983e5f9b94dc4126abdd. The current relocated manifest is a location-only derivative. No source/reference bytes were changed.

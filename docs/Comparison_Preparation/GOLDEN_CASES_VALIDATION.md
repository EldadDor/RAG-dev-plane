# Frozen golden-case release — 2026-10-13

Human approval recorded in [HUMAN_APPROVAL.md](HUMAN_APPROVAL.md).

**17 PDFs / 313 pages / 47 included cases: 42 answerable and 5 unanswerable.** Each PDF has at least two answerable cases. The original 51 submitted cases and worksheets are preserved.

The actual comparison loader accepted [corpus.frozen.json](corpus.frozen.json). Source and JSONL SHA-256 values, unique IDs, bilingual fields, viewer-page bounds and answerability consistency passed. These are validation results, not parser quality scores.

## Excluded optional cases

| Case | Reason |
| --- | --- |
| pdf-013-q3 | Mixed question: the end condition is answerable; a numerical winning score is not. Excluded rather than silently rewrite the approved question. |
| pdf-014-q3 | Mixed question: the 85% figure is answerable; the feedback collection method is not. Excluded rather than score a partial answer as a complete abstention. |
| pdf-015-q3 | Ambiguous printed threshold (±100) and incorrect submitted redirect literal. The source says Response.Redirect("win.aspx"). A replacement question would require a separate reference revision. |
| pdf-017-q3 | Mixed question: the unnoticed-illegal-clue rule is stated; a numerical effect on the final score is not. Excluded rather than silently rewrite the question. |

Full original case content is retained in [excluded-cases.json](excluded-cases.json). A later revision may split the three mixed questions or replace the ambiguous code question after human review. This does not block the included cases.

## Applied normalization

Approved questions are preserved verbatim after Markdown formatting removal. Background facts outside the question's scope are retained as submission trace, not mandatory scoring requirements. Page/quote corrections use the previous source review, not treatment outputs.

- pdf-003-q1: Bar and Video Walls are separate labels; Audio is a label rather than an asserted global connector.
- pdf-007-q1: source says unreported money, rather than illegal money. Grade the requested state-tax argument.
- pdf-013-q1: seven symbols in the supplied list/source, correcting its contradictory six-symbol count; omit the unsupported three-properties assertion.
- pdf-007-q2/q3: viewer page 5. pdf-013-q2: pages 5–6. pdf-014-q1: page 2; q2: pages 4–6.
- pdf-008: CTP external supply belongs to page 10; page 11's battery supply concerns CTP-Rotate. Remove speculative absence explanations from grading.

All per-case normalization and source/submission hashes are in [golden-cases-validation.json](golden-cases-validation.json). Submitted worksheet files were not edited.

## Next execution

The final pypdf baseline completed **17 documents / 68 extraction passes** (one cold plus three warm passes per document) at `E:/Workspace/AI_Stuff/Pdf_Examples/Comparison_Runs/pypdf-baseline-2026-10-13-r2`. The private `artifact-validation.json` verifies manifest/source/reference snapshot identity, stable cold/warm text and normalized offset/page consistency. The first run is retained as superseded because a final mandatory-fact scope cleanup changed its reference identity.

Pypdf extracted no text on pdf-010's scanned page; pdf-004 pages 2 and 47 also had no extracted text. Completion is not a quality score. No OCR, Docling model run or indexed RAG evaluation has occurred.

Next is the [concrete isolated Docling/OCR setup request](DOCLING_RUNTIME_PREPARATION.md): pinned packages, local English/Hebrew model artifacts, CPU-only serial execution, 8 GiB worker cap and 180-second time ceiling. Its separate preparation approval is required by the existing design before downloads/model execution. All extraction outputs remain outside Git; no production ingestion is part of this step.

The manifest stores absolute local paths required by the existing runner. If the checkout moves, regenerate paths and manifest identity while keeping source/reference hashes fixed. Results remain outside Git.

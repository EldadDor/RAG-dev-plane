# pypdf / Docling without OCR — execution comparison

**Task:** RAG-B-RUNTIME
**Last reviewed:** 2026-10-13

Execution status: **failed**; 30/34 document/parser treatments completed.
All 34 treatments were attempted: 30 completed, 2 partial and 2 failed in the
original retained run. This is execution evidence, not an adoption verdict.
Integrity audit checked 128 normalized passes, 113 frozen package pins and unchanged model hashes.
Quality/adoption status: **manual rubric inspection pending**. Timing and character/block counts do not establish evidence accuracy.

Private output: `E:/Workspace/AI_Stuff/Pdf_Examples/Comparison_Runs/pypdf-docling-no-ocr-2026-10-13`.
Frozen manifest SHA-256: `a84483eabfeeba04232dc365709f9e8bec26b9c2b195983e5f9b94dc4126abdd`.

One cold and three warm passes per completed treatment; CPU only; 8192 MiB worker lifetime peak cap; 180-second initialization/extraction deadline.
Cold means a fresh converter/process, not a flushed disk cache. Warm time below is the median; initialization is recorded separately in report.json.

| Document | pypdf cold / warm median (s) | Docling cold / warm median (s) | Docling peak (GiB) | Docling outcome |
| --- | --- | --- | --- | --- |
| pdf-001 | 0.10 / 0.09 | 12.57 / 13.05 | 1.79 | completed (4/4 recorded passes) |
| pdf-002 | 0.90 / 0.86 | 9.59 / 9.46 | 1.50 | completed (4/4 recorded passes) |
| pdf-003 | 0.14 / 0.13 | 41.56 / 40.97 | 2.12 | completed (4/4 recorded passes) |
| pdf-004 | 0.41 / 0.40 | 114.02 / 107.44 | 2.48 | completed (4/4 recorded passes) |
| pdf-005 | 0.50 / 0.48 | 19.97 / 19.69 | 1.65 | completed (4/4 recorded passes) |
| pdf-006 | 2.00 / 1.97 | 153.35 / 154.79 | 2.36 | completed (4/4 recorded passes) |
| pdf-007 | 0.20 / 0.20 | 18.95 / 18.68 | 1.69 | completed (4/4 recorded passes) |
| pdf-008 | 0.38 / 0.36 | 89.96 / 89.55 | 1.93 | completed (4/4 recorded passes) |
| pdf-009 | 0.15 / 0.14 | 3.05 / 2.92 | 1.31 | completed (4/4 recorded passes) |
| pdf-010 | 1.04 / 0.98 | 22.54 / 18.37 | 1.28 | partial (4/4 recorded passes) |
| pdf-011 | 0.14 / 0.10 | 13.07 / 12.64 | 1.17 | completed (4/4 recorded passes) |
| pdf-012 | 0.50 / 0.50 | 67.53 / 65.29 | 2.00 | completed (4/4 recorded passes) |
| pdf-013 | 4.81 / 4.70 | unavailable / unavailable | unavailable | failed (1/4 recorded passes) |
| pdf-014 | 0.35 / 0.33 | 21.66 / 22.66 | 1.79 | completed (4/4 recorded passes) |
| pdf-015 | 0.38 / 0.38 | 30.97 / 31.00 | 1.89 | partial (4/4 recorded passes) |
| pdf-016 | 3.02 / 2.97 | unavailable / unavailable | unavailable | failed (0/4 recorded passes) |
| pdf-017 | 0.64 / 0.63 | 18.55 / 19.37 | 1.74 | completed (4/4 recorded passes) |

## Integrity and limitations

- Source and human-reference hashes match the frozen corpus; parsed reference snapshots are equal to the approved JSONL records.
- Text files agree with normalized assembled text; Unicode offsets and one-based page references are consistent; linked image bytes match their hashes.
- Model artifacts still match the immutable pre-run SHA-256 inventory.
- All available cold/warm text is stable; failed treatments without artifacts are unavailable.
- OCR is disabled; scanned-page text is unsupported in this treatment. Five negative cases require retrieval/answer evaluation and are not scored by extraction.
- Human evidence includes descriptive notes and shortened quotations. Whole-string substring matching is not a valid case score; inspect the actual facts, table cells, labels and source associations.
- No chat/embedding/provider/store/SQL requests or production ingestion were performed. Subsequent experiment-adapter/OCR changes passed 43 focused offline tests; the full application suite was not run.

## Explicit failures / partial results

- pdf-010 / docling (partial): Block 2: table cells unavailable; Block 3: table cells unavailable; Block 4: table cells unavailable; Block 5: table cells unavailable
- pdf-013 / docling (failed): ExtractionError: Invalid normalized bounding box
- pdf-015 / docling (partial): Block 40: table cells unavailable
- pdf-016 / docling (failed): Extraction worker exceeded 180 second timeout

The bounding-box failure was subsequently handled as an explicit partial result:
six out-of-frame upstream boxes are retained in raw output and omitted from
normalized coordinates, while source text/page identity is preserved. The
normalization policy is separately identified. Four stable/integrity-checked
partial passes are in `Comparison_Runs/docling-bbox-partial-pdf-013-2026-10-13`;
the original failed run/report remain unchanged. Thus the supplemental no-OCR
outcome is 13 completed / 3 partial / 1 timeout for Docling.

The approved [Tesseract OCR design](HEBREW_OCR_DESIGN.md) has been implemented and
prepared. [Native OCR evidence](TESSERACT_RUNTIME_RESULTS.md) found decoder access
violations; corpus OCR awaits the [explicit PDF backend revision](PDF_BACKEND_REVISION.md).

During the timed-out agriculture-document extraction, the upstream table postprocessor logged 49 of 319 PDF cells dropped because they did not match the proposed 147x2 grid. This terminal diagnostic is a manual-inspection lead, not a scored denominator or a completed extraction result.

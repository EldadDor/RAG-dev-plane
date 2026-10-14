# Paired PDFium no-OCR / Hebrew-English OCR comparison

**Follow-up 2026-10-14:** [Original-case scorecard and picture-child correction](EXTRACTION_SCORECARD.md).
The counts below remain the original execution evidence. The new adapter policy
was checked by saved-export replay, not by rerunning or relabeling these treatments.

**Task:** RAG-B-OCR
**Last reviewed:** 2026-10-13
**Status:** Both original PDFium corpus treatments and paired integrity audit completed: no-OCR 13 complete / 3 partial / 1 timeout; OCR 14 complete / 1 partial / 2 timeouts. All 124 available outputs are stable and integrity-checked. Eight separately identified telemetry passes verify the final export/provenance fixes; keep pypdf as production default.

Both Docling treatments select `PyPdfiumDocumentBackend`, pypdfium2 5.14.0,
with the same frozen 17-PDF / 313-page corpus and 47 human-approved cases.
OCR recognition uses the prepared Tesseract `heb eng` models. The earlier pypdf
baseline and native-decoder results are retained. No automatic fallback occurs.

Limits remain CPU only, serial workers, one cold/three warm passes per treatment,
180 seconds per initialization/extraction, 8192 MiB worker lifetime peak working
set, and an additional 8192 MiB aggregate job private-commit ceiling for OCR.
Cold means a new worker/converter, not a flushed disk cache. Original bytes,
references, model/native hashes and configuration must pass the final audit.

Private runs under `E:/Workspace/AI_Stuff/Pdf_Examples/Comparison_Runs`:

- `pypdf-baseline-2026-10-13-r2` (reused baseline).
- `docling-pdfium-no-ocr-2026-10-13`.
- `docling-pdfium-ocr-2026-10-13` (follows no-OCR serially).

The final OCR directory contains `paired-integrity-audit.json` and
`paired-golden-case-review.md`: frozen references alongside the three treatments'
source-page text and links to raw/normalized blocks, boxes and assets.

## Original corpus execution results

All 34 Docling document/treatment combinations were attempted. The original
reports return exit code 1 because partials/timeouts are retained explicitly.
These counts predate the separately identified provenance-policy fix below;
pdf-008's original completed status is not a clean-provenance acceptance.

| Treatment | Complete | Partial | Timeout | Audited outputs | Peak worker working set | Peak job private commit |
| --- | --- | --- | --- | --- | --- | --- |
| pypdf reused baseline | 17 | 0 | 0 | 68 (prior audit) | See baseline report | Not applicable |
| PDFium no OCR | 13 | 3 | 1 | 64 | 1.9866 GiB | Not applicable |
| PDFium Tesseract OCR | 14 | 1 | 2 | 60 | 1.9303 GiB | 2.1894 GiB |

The paired audit verifies all 124 available Docling outputs, stable text/block
IDs, Unicode offsets, page bounds and asset hashes, source/reference snapshots,
113 actual installed package pins, 138 native files, four OCR artifacts and eight
Docling artifacts. It does not establish semantic source fidelity from legal
coordinate ranges. Original text exports remain unchanged; 124 exact UTF8
companions were added after lossless verification, without reparsing.

Cold/warm timings exclude initialization; warm is the median of three passes.
The pypdf timings come from the earlier baseline, so cross-batch speed differences
are descriptive and may reflect host load/cache effects.

| PDF | pypdf cold / warm median (s) | PDFium no OCR: outcome; cold / warm (s) | PDFium OCR: outcome; cold / warm (s) |
| --- | --- | --- | --- |
| pdf-001 | 0.08 / 0.07 | completed; 14.82 / 12.53 | completed; 12.46 / 12.73 |
| pdf-002 | 0.59 / 0.60 | partial; 9.16 / 8.47 | partial; 15.19 / 15.42 |
| pdf-003 | 0.12 / 0.10 | completed; 43.51 / 43.58 | completed; 50.35 / 46.15 |
| pdf-004 | 0.30 / 0.30 | completed; 127.99 / 105.94 | completed; 112.80 / 115.78 |
| pdf-005 | 0.36 / 0.36 | completed; 20.71 / 19.12 | completed; 22.17 / 21.20 |
| pdf-006 | 1.45 / 1.51 | completed; 162.86 / 167.58 | failed; 180s timeout |
| pdf-007 | 0.15 / 0.15 | completed; 21.20 / 18.40 | completed; 22.18 / 23.55 |
| pdf-008 | 0.29 / 0.29 | completed; 87.16 / 84.53 | completed; 117.72 / 110.41 |
| pdf-009 | 0.13 / 0.11 | completed; 3.13 / 2.99 | completed; 13.04 / 12.54 |
| pdf-010 | 0.79 / 0.78 | partial; 13.37 / 13.17 | completed; 17.88 / 18.44 |
| pdf-011 | 0.08 / 0.07 | completed; 12.57 / 12.17 | completed; 14.15 / 14.08 |
| pdf-012 | 0.40 / 0.39 | completed; 61.58 / 60.11 | completed; 64.94 / 62.68 |
| pdf-013 | 3.73 / 3.90 | completed; 33.61 / 33.13 | completed; 37.94 / 38.14 |
| pdf-014 | 0.32 / 0.30 | completed; 20.95 / 22.33 | completed; 25.52 / 25.74 |
| pdf-015 | 0.32 / 0.32 | partial; 31.32 / 30.84 | completed; 40.75 / 40.95 |
| pdf-016 | 2.58 / 2.58 | failed; 180s timeout | failed; 180s timeout |
| pdf-017 | 0.50 / 0.48 | completed; 18.47 / 18.67 | completed; 35.00 / 35.03 |

## Source-reviewed diagnostic sample

This is a limited source inspection, not a score across the whole corpus.
The original [page 1 preview](previews/pdf-002-page-001.png),
[page 2 preview](previews/pdf-002-page-002.png) and frozen `pdf-002` cases were
checked against cold artifacts. The source visibly numbers the Hebrew sections
1/2 in the right column before section 3 in the left column; page 2 places the
play sequence in the right column before answer checking on the left.

| Diagnostic | pypdf baseline | PDFium no OCR | PDFium OCR |
| --- | --- | --- | --- |
| pdf-002-q1: four approved component facts | 4/4 retained, with fragmented label/number order | 3/4 retained; the one beginner-die quantity/label is absent from assembled source text | 3/4; the same fact remains absent |
| pdf-002-q2: four approved answer-check facts | Not yet scored in this sample | Facts retained, but answer checking is assembled before the play sequence | Pending |
| pdf-002 page 1 section order | Not yet scored in this sample | Sections 3, 1, 2 rather than the source's numbered order | Same 3, 1, 2 order; OCR does not correct it |
| pdf-006-q1: four CHR.02/H95 dimensions | Structured cells unavailable by baseline contract; text not scored here | 4/4 critical cells with model-column association: 950 / 620 / 380 / 355 mm | Unavailable: cold extraction timed out at 180 seconds |
| pdf-006-q2: widest 600 mm deep rectangle table | Not scored in this sample | 2/2 critical dimensions retained with MTB.R.206 column association: 2000 × 600 mm | Unavailable: same timeout |
| pdf-006-q3: features, packaging and optional upgrade | Not scored in this sample | All three grouped reference facts retained, including 25 mm top, 2 mm edging, flatpack/pallet and chrome-plated legs | Unavailable: same timeout |
| pdf-010-q1/q2: four approved weather/wind/wave facts | 0/4; image-only page has no text layer | 0/4; detected tables have no cells and searchable fact text is empty | All requested facts recovered; 3/3 wind/wave fields exact with source-row association. Metro weather statement contains an extra OCR `y` token |

The missing beginner-die fact is a concrete regression even though the text is
otherwise readable. Invalid boxes on source page 3 make this treatment partial;
they are explicitly omitted from normalized coordinates while text and raw
upstream coordinates remain available. These are distinct quality/provenance
issues. Do not select Docling as a universal replacement based on extraction
completion or character counts. The OCR cold output still omits the one
beginner-die quantity/label; it does not recover this critical fact.

The furniture [page 2 preview](previews/pdf-006-page-002.png) confirms those four
dimension cells in the CHR.02/H95 column. The no-OCR table rendering preserves
them and their labels/units. Other school-chair tables on that page merge some
catalogue/production-code rows or misplace cells; the passing critical sample
does not certify every table cell or its header structure.
The [page 6 preview](previews/pdf-006-page-006.png) and extracted rows also confirm
the widest 600 mm deep table dimensions and the separately labeled feature,
packaging and optional-upgrade text. Compound reference groups are not counted
as individual table-cell matches.

The [weather forecast preview](previews/pdf-010-page-001.png) was also inspected
before OCR comparison: its critical evidence includes the Metro Manila weather
row and the Northern/Central Luzon wind/wave row with 1.5–2.8 meters. The OCR cold
table retains Moderate to Strong, Northeast to East and Moderate to Rough
(1.5 to 2.8 meters) in the correct Northern/Central Luzon row. The Metro Manila
weather cell reads “Cloudy skies with scattered rains y and thunderstorms”;
its requested meaning is retained with an extra token, not an exact transcript.
Other rows lose labels/values, the Metro Manila cause cell loses LPA, and tide
heights are corrupted. Do not generalize the passing critical wind/wave sample
to all tables or numerical cells. The five
negative cases remain reserved for retrieval/answer evaluation in Stage C.

## Additional reference/provenance limitations

The 64 no-OCR artifacts passed source/reference/model/package, text/offset/page,
asset-hash and cold/warm checks. PDFium retains embedded carriage returns in
four documents. Python's universal-newline `read_text()` changes these, so the
audit reads UTF-8 bytes and reverses only the runner's Windows LF-to-CRLF export
translation. This lossless reversal matches all 64 authoritative JSON texts;
16 artifacts contain embedded carriage returns. Original exports are retained.
Use normalized JSON or exact UTF8 companions for offsets; the current runner
writes exact UTF8 bytes and a regression test covers mixed carriage returns.
Peak worker working set was 1.9866 GiB; median successful cold parse 21.07 seconds.
No matching Windows Application Error events were present from the first PDFium
smoke through both complete corpus runs and the post-fix validations. The final
event-log read succeeded. This is scoped stability evidence,
not a claim about untested files or indefinite converter reuse. The private
event audit is `Parser_Experiment/pdfium-native-events-final.json`.

During pdf-008's first extraction, upstream `docling-core` emitted repeated
coordinate-clamping warnings on pages 12 and 19. Examples included page-12
left=612.2416 exceeding width=595.276 and page-19 negative coordinates. These
pages have zero PDF rotation and ordinary matching media/crop boxes. The
upstream exporters can validate/clamp document copies after conversion returns;
the original adapter's conversion-only capture missed these warnings. Normalized
bounds therefore cannot establish source-location fidelity or recover pre-clamp values.
This terminal diagnostic is separate from the adapter's explicit omitted-box
warnings. Do not interpret an execution-completed status as clean provenance.
The original treatments were retained unchanged while comparing. A first
separate telemetry attempt (`pdfium-warning-fix-no-ocr-pdf-008-2026-10-13`)
verified exact UTF8 export but still missed the export-time warnings; it is
retained as a failed warning-policy diagnostic. The revised
`export_clamp_pages_without_boxes_v3` captures across conversion and export,
marks affected pages partial and conservatively omits their normalized boxes.
Text/page IDs and raw upstream output remain available; raw coordinates may
already be clamped. Separate `r2` no-OCR/OCR telemetry reruns validate this fix.

Both final telemetry treatments completed one cold/three warm passes as explicit
partials. All eight outputs preserve the respective original treatment's text
and image hashes, have distinct versioned block IDs with stable warm IDs, exact
UTF8 bytes/offsets, and no normalized boxes on affected pages 12/18/19. Each
captures 448 clamping warnings; omitting boxes is conservative disclosure, not a
geometry repair. File/source/reference/model/native/package hashes still match.
The first capture attempt remains separate and is not counted as a passing fix.

Final outputs: `pdfium-warning-fix-no-ocr-pdf-008-2026-10-13-r2` and
`pdfium-warning-fix-ocr-pdf-008-2026-10-13-r2`. The latter contains
`warning-policy-integrity-audit.json`. All passes stayed within the unchanged
180-second / 8192 MiB limits. The full 17-file corpus was not silently rerun or
relabeled under the newer policy; original counts above remain original evidence.

A reference inconsistency also remains in pdf-007-q3: its second expected-fact
string says printed page 3 / viewer page 4, while the frozen evidence and visible
source put footnote 8 on printed page 4 / viewer page 5. Earlier validation
corrected the evidence page but left that descriptive fact string intact.
The question asks for the cited publication/page 25, not the source's viewer
page. Score the requested bibliographic fact separately; do not count a parser
as wrong for preserving the correct source page. Frozen reference bytes remain
unchanged; flag this discrepancy before any complete-case aggregate score.

## Validation boundary

46 focused offline tests passed, including explicit backend selection/identity,
unknown selection rejection, no retry/fallback, offsets/assets/provenance,
timeout/crash handling and native-child memory/cleanup controls. Digital and
Hebrew/English raster smoke each completed four stable passes. Raster signed
number/unit and logical Hebrew order matched exactly; all prepared hashes matched.
Sparse-fixture orientation warnings were retained.

## Extraction decision

Keep pypdf as the production default. The scanned weather sample demonstrates
useful OCR recovery, but both Docling treatments lose an approved game fact
that pypdf retains, Hebrew column order remains wrong, some table values are
corrupted and larger files exceed the fixed deadline. The zero-wrong-provenance
criterion is not established. This is sufficient to reject a universal default
switch under the existing rubric without inventing a full-corpus pass percentage.

The 47-case packet supports further fact/cell/label/RTL review. Full aggregate
golden-case scoring and indexed answer/retrieval evaluation are still distinct
from these extraction results; the five negatives need their assigned-document
scope preserved. No new questions or repeated approval of the worksheets is
required. Resolve the documented source-fidelity gaps before Stage C selection.

Full application tests, live providers/stores/SQL, production ingestion and
indexed RAG comparison have not run. G3 push/merge and G4 phase closure remain
separate decisions. Human reference approval is complete and does not need repeating.

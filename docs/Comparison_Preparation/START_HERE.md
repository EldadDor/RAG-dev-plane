# PDF comparison corpus — human review complete

**Current status (2026-10-13):** Eldad approved all 17 `worksheets-done` files in the chat. The frozen release contains 47 valid cases (42 answerable / 5 unanswerable); four optional mixed/ambiguous cases are preserved outside scoring. No repeated human signoff is needed.

Use [corpus.frozen.json](corpus.frozen.json) with the comparison runner. See [validation and exclusions](GOLDEN_CASES_VALIDATION.md), [recorded human approval](HUMAN_APPROVAL.md), and [machine validation](golden-cases-validation.json). The dataset passed the actual comparison loader; all 17 PDFs retain their original source hashes.

`corpus.draft.json` and `reference-review-2026-10-11` are historical drafts. The current `golden-cases/*.jsonl` files are populated, frozen and hashed. The user explicitly chose to copy, commit and push the source corpus and review artifacts in this repository; extraction run outputs remain outside Git.

## Original worksheet instructions (completed)

1. Open each worksheet below and its original PDF. Write **two answerable questions per PDF**. An optional third question can test a difficult table/diagram or something the PDF does not answer. This gives 34–51 cases across 17 PDFs.
2. For each question, write the required answer facts and supporting evidence: **PDF viewer page number, counting the cover as page 1**, plus an exact quote, table cells (row/column labels and units), or visible diagram labels. Add your name and verification date. Questions may be Hebrew or English; include some English questions about Hebrew evidence if you want cross-language coverage.
3. For an unanswerable case, leave facts/evidence empty, record the missing information and check the entire assigned PDF. Aim for 3–5 such optional cases across the corpus. Before a later test against all PDFs together, we must also check that another PDF does not supply the answer.
4. Save the completed worksheets and tell me **“Golden cases ready.”** I will validate the references, add any evidence pages you chose, convert worksheets to JSONL, recompute hashes and freeze the manifest. You do not need to edit both formats.

Do not infer an answer from a suggested topic. Use only facts you verify in the original PDF. For facts on pages beyond the suggestions, simply record the actual viewer page; I will update the manifest.

| Worksheet | Original filename | PDF pages | Language | Suggested viewer pages |
| --- | --- | --- | --- | --- |
| [pdf-001](worksheets-done/pdf-001.md) | 10-common-hibernate-mistakes-that-cripple-your-performance-free.pdf | 6 | en | 1, 2, 3 |
| [pdf-002](worksheets-done/pdf-002.md) | 9rules.pdf | 4 | he | 1, 2, 3 |
| [pdf-003](worksheets-done/pdf-003.md) | Alpha_Casino_LeadMagnet_V28.pdf | 18 | en | 1, 2, 8, 9 |
| [pdf-004](worksheets-done/pdf-004.md) | Catalogue_of_Czech_TOYS-and-GAMES.pdf | 48 | en | 1, 3, 7, 24 |
| [pdf-005](worksheets-done/pdf-005.md) | Full Process for Coding with AI Coding Assistants.pdf | 9 | en | 1, 2, 3, 5 |
| [pdf-006](worksheets-done/pdf-006.md) | gurkan03tableschairs.pdf | 11 | en | 1, 2, 6 |
| [pdf-007](worksheets-done/pdf-007.md) | Herbrew_Casino1.pdf | 7 | he | 1, 2, 4 |
| [pdf-008](worksheets-done/pdf-008.md) | imc_telemetry-solutions_EN-201810_WEB.pdf | 20 | en | 1, 2, 10, 12 |
| [pdf-009](worksheets-done/pdf-009.md) | Maven, IntelliJ Build & Run Guide-2.pdf | 1 | en | 1 |
| [pdf-010](worksheets-done/pdf-010.md) | phillippine_weather_PAGASA.pdf | 1 | en | 1 |
| [pdf-011](worksheets-done/pdf-011.md) | Print-Ready-file-for-Know-the-Odds-4pg-brochure__165223_GAMING_V01.pdf | 2 | en | 1, 2 |
| [pdf-012](worksheets-done/pdf-012.md) | Qwopus3-5-27b-Colab_complete_guide_to_llm_finetuning.pdf | 26 | en | 1, 2, 13 |
| [pdf-013](worksheets-done/pdf-013.md) | t4.pdf | 16 | he | 1, 2, 6, 8 |
| [pdf-014](worksheets-done/pdf-014.md) | Technion_AI_change_cse.pdf | 9 | he, en | 1, 2, 4, 5 |
| [pdf-015](worksheets-done/pdf-015.md) | Technion_programing_casino.pdf | 14 | he, en | 1, 2, 4, 7 |
| [pdf-016](worksheets-done/pdf-016.md) | חוברת חקלאות מוגבר-חגית חלד.pdf | 113 | he | 1, 2, 57, 88 |
| [pdf-017](worksheets-done/pdf-017.md) | שם-קוד.pdf | 8 | he | 1, 2, 3, 4 |

## What has been prepared

All 17 PDFs opened successfully; they contain 313 pages. Source-byte hashes and per-page text/image diagnostics are in `inventory.json`. Selected-page visual review uses 55 page previews and 17 contact sheets. Original PDFs were not modified. Languages/layouts describe the reviewed samples and text diagnostics; they do not certify every page's layout or parser accuracy.

The corpus includes English, Hebrew, mixed Hebrew/English, tables, diagrams, columns and an image-only document for OCR. A confirmed document mixing scanned and selectable-text pages has not been established. Malformed/encrypted fixtures remain separate from these real files.

`corpus.draft.json` is retained for preparation traceability. It is not the executable manifest. Use the frozen manifest linked above.

## What follows your golden cases

The pypdf baseline and paired no-OCR run are complete, including recorded partials/failures; see [runtime results](DOCLING_RUNTIME_RESULTS.md) and [the comparison](NO_OCR_COMPARISON.md). The user separately approved Tesseract setup on 2026-10-13 because EasyOCR cannot process Hebrew. [Native OCR results](TESSERACT_RUNTIME_RESULTS.md) verify the fixture text and record default PDF decoder faults. The [explicit PDFium backend revision](PDF_BACKEND_REVISION.md) now awaits G2 before corpus OCR. Score evidence fidelity, failures, time and memory across completed treatments; the private golden-case review packet puts approved references beside extracted source-page text. After selecting treatments, a separately approved indexed RAG comparison uses identical questions, retrieval settings and answer model in two test workspaces. Production ingestion and live RAG evaluation still require their own approval.

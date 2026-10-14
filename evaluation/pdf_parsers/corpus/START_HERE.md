# PDF comparison corpus — human review complete

**Current status (2026-10-13):** Eldad approved all 17 `worksheets-done` files in the chat. The frozen release contains 47 valid cases (42 answerable / 5 unanswerable); four optional mixed/ambiguous cases are preserved outside scoring. No repeated human signoff is needed.

Use [corpus.relocated.json](corpus.relocated.json) with the comparison runner. See [validation and exclusions](GOLDEN_CASES_VALIDATION.md), [recorded human approval](HUMAN_APPROVAL.md), and [machine validation](golden-cases-validation.json). The dataset passed the actual comparison loader; all 17 PDFs retain their original source hashes.

The original preparation drafts and blank worksheets were [archived with owner approval](RETIREMENT_PROPOSAL.md). `reference-review-2026-10-11` remains historical review evidence. The current `golden-cases/*.jsonl` files are populated, frozen and hashed. The user explicitly chose to copy, commit and push the source corpus and review artifacts in this repository; extraction run outputs remain outside Git.

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

Preparation traceability is retained in the [retirement record](RETIREMENT_PROPOSAL.md). Use the relocated manifest linked above for current runs.

## What follows your golden cases

Both PDFium no-OCR and Hebrew/English OCR treatments have run on all 17 files;
see [results, source diagnostics and the extraction decision](PDFIUM_COMPARISON.md).
All 124 available outputs and eight separate correctness-fix outputs passed their
integrity audits. Keep pypdf as the production default: scanned-weather OCR gains
do not remove observed fact loss, RTL/table errors or fixed-budget timeouts.
The private paired review packet puts all 47 approved cases beside source-page
text from the three treatments. Your worksheets and frozen reference bytes remain
unchanged; **no new questions or repeated human approval are needed**.

The next work is to resolve the documented fidelity gaps and complete fact/cell/
label/RTL scoring with those existing cases before selecting indexed treatments.
The separately gated Stage C comparison then uses identical questions, retrieval
settings and answer model in test workspaces. Production ingestion and live RAG
evaluation require their own design/operator approvals. Original native-decoder
failures and the [approved PDFium revision](PDF_BACKEND_REVISION.md) remain recorded.

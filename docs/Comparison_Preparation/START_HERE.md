# Your next step: fill the PDF golden-case worksheets

1. Open each worksheet below and its original PDF. Write **two answerable questions per PDF**. An optional third question can test a difficult table/diagram or something the PDF does not answer. This gives 34–51 cases across 17 PDFs.
2. For each question, write the required answer facts and supporting evidence: **PDF viewer page number, counting the cover as page 1**, plus an exact quote, table cells (row/column labels and units), or visible diagram labels. Add your name and verification date. Questions may be Hebrew or English; include some English questions about Hebrew evidence if you want cross-language coverage.
3. For an unanswerable case, leave facts/evidence empty, record the missing information and check the entire assigned PDF. Aim for 3–5 such optional cases across the corpus. Before a later test against all PDFs together, we must also check that another PDF does not supply the answer.
4. Save the completed worksheets and tell me **“Golden cases ready.”** I will validate the references, add any evidence pages you chose, convert worksheets to JSONL, recompute hashes and freeze the manifest. You do not need to edit both formats.

Do not infer an answer from a suggested topic. Use only facts you verify in the original PDF. For facts on pages beyond the suggestions, simply record the actual viewer page; I will update the manifest.

| Worksheet | Original filename | PDF pages | Language | Suggested viewer pages |
| --- | --- | --- | --- | --- |
| [pdf-001](worksheets/pdf-001.md) | 10-common-hibernate-mistakes-that-cripple-your-performance-free.pdf | 6 | en | 1, 2, 3 |
| [pdf-002](worksheets/pdf-002.md) | 9rules.pdf | 4 | he | 1, 2, 3 |
| [pdf-003](worksheets/pdf-003.md) | Alpha_Casino_LeadMagnet_V28.pdf | 18 | en | 1, 2, 8, 9 |
| [pdf-004](worksheets/pdf-004.md) | Catalogue_of_Czech_TOYS-and-GAMES.pdf | 48 | en | 1, 3, 7, 24 |
| [pdf-005](worksheets/pdf-005.md) | Full Process for Coding with AI Coding Assistants.pdf | 9 | en | 1, 2, 3, 5 |
| [pdf-006](worksheets/pdf-006.md) | gurkan03tableschairs.pdf | 11 | en | 1, 2, 6 |
| [pdf-007](worksheets/pdf-007.md) | Herbrew_Casino1.pdf | 7 | he | 1, 2, 4 |
| [pdf-008](worksheets/pdf-008.md) | imc_telemetry-solutions_EN-201810_WEB.pdf | 20 | en | 1, 2, 10, 12 |
| [pdf-009](worksheets/pdf-009.md) | Maven, IntelliJ Build & Run Guide-2.pdf | 1 | en | 1 |
| [pdf-010](worksheets/pdf-010.md) | phillippine_weather_PAGASA.pdf | 1 | en | 1 |
| [pdf-011](worksheets/pdf-011.md) | Print-Ready-file-for-Know-the-Odds-4pg-brochure__165223_GAMING_V01.pdf | 2 | en | 1, 2 |
| [pdf-012](worksheets/pdf-012.md) | Qwopus3-5-27b-Colab_complete_guide_to_llm_finetuning.pdf | 26 | en | 1, 2, 13 |
| [pdf-013](worksheets/pdf-013.md) | t4.pdf | 16 | he | 1, 2, 6, 8 |
| [pdf-014](worksheets/pdf-014.md) | Technion_AI_change_cse.pdf | 9 | he, en | 1, 2, 4, 5 |
| [pdf-015](worksheets/pdf-015.md) | Technion_programing_casino.pdf | 14 | he, en | 1, 2, 4, 7 |
| [pdf-016](worksheets/pdf-016.md) | חוברת חקלאות מוגבר-חגית חלד.pdf | 113 | he | 1, 2, 57, 88 |
| [pdf-017](worksheets/pdf-017.md) | שם-קוד.pdf | 8 | he | 1, 2, 3, 4 |

## What has been prepared

All 17 PDFs opened successfully; they contain 313 pages. Source-byte hashes and per-page text/image diagnostics are in `inventory.json`. Selected-page visual review uses 55 page previews and 17 contact sheets. Original PDFs were not modified. Languages/layouts describe the reviewed samples and text diagnostics; they do not certify every page's layout or parser accuracy.

The corpus includes English, Hebrew, mixed Hebrew/English, tables, diagrams, columns and an image-only document for OCR. A confirmed document mixing scanned and selectable-text pages has not been established. Malformed/encrypted fixtures remain separate from these real files.

`corpus.draft.json` and the blank `golden-cases/*.jsonl` files are **drafts, not a frozen runnable dataset**. Blank answers and verification fields must be completed first. The inspection draft is retained for traceability. Keep this entire folder outside Git; it contains private filenames and source snippets.

## What follows your golden cases

First we prepare the isolated parser environment and local OCR models. Then we compare pypdf and Docling on the same frozen source files, scoring extraction/evidence fidelity, failures, time and memory. After selecting treatments, a separately approved indexed RAG comparison uses identical questions, retrieval settings and answer model in two test workspaces. No ingestion, model installation/download or live RAG evaluation has been performed during preparation.

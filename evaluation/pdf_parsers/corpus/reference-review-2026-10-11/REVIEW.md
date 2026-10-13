# Review complete - human verification before freezing

Reviewed all 17 submitted worksheets (51 cases). Prepared 51 normalized candidates: 44 answerable and 7 unanswerable. Submitted worksheets and original PDFs are unchanged. This is a reviewed DRAFT, not a frozen golden dataset or a parser comparison result.

## Your precise next step

1. Read the corrections table below, then review [all 51 candidate cases](ALL_CASES_REVIEWED.md) against the linked original PDFs. Each case shows its question, required facts, viewer pages and edits. Start with the corrections; unchanged submitted cases still have pending verification fields.
2. For the seven unanswerable cases, confirm the stated missing information within the assigned PDF (or the explicit page scope). Do not certify absence using text extraction alone; inspect images/diagrams too. These negatives apply to one assigned document, not an unrestricted search across all 17 PDFs.
3. Fill [HUMAN_SIGNOFF.md](HUMAN_SIGNOFF.md): your verifier name, date, and check each PDF whose three candidate cases you verified. Note any remaining corrections. A single file records the check; you need not retype answers or fill 51 duplicate metadata fields.
4. Tell me **“Human source verification complete.”** I will apply final corrections, populate verification metadata from your signoff, validate with the existing loader and freeze the manifest. The next execution step is the pypdf baseline. Isolated Docling/OCR installation, local model artifacts and resource budget still need concrete preparation before a two-parser run.

The existing comparison protocol requires human-verified references even for extraction-only runs. All supplied verification fields were pending/blank, so I have not inserted your name or treated model-assisted source review as your verification. The loader intentionally rejects this draft.

## Corrections to check first

| Cases | Concrete correction |
| --- | --- |
| pdf-003-q1 | Separate Bar / Video Walls labels; Audio is only a label. |
| pdf-007-q2/q3 | Evidence is viewer page 5, not 4. |
| pdf-008-q1 | Battery statement concerns CTP-Rotate on page 11; CTP external supply is on page 10. |
| pdf-013-q1 | Seven symbols on viewer page 4, not six on page 2. |
| pdf-013-q2/q3 | Solo instructions span pages 5–6; hide-and-seek is on 13–14, not 8. Partial negative rewritten to missing numerical score only. |
| pdf-014-q1/q2 | Stage 5 is page 2; timeline is page 4 and related prose pages 5–6. |
| pdf-014-q3 | Ask only the missing feedback-collection method; 85% itself is answerable. |
| pdf-015-q3 | Viewer page 9; code is Response.Redirect("win.aspx"). Printed ±100 threshold is ambiguous, so ask explicit redirect/reset operations instead. |
| pdf-016-q3 | Chapter B also names Venus flytrap. |
| pdf-017-q3 | Ask the stated unnoticed/detected illegal-clue rules; remove hypothetical numeric penalty. |

Other edits make grading match the question: remove unrelated mandatory facts or broaden wording explicitly when the full list is intended. Every semantic edit is noted in its candidate worksheet. Source transcripts use selected visible quotes/labels or labeled summaries; they are not whole-page reference transcripts. OCR character-error/read-order scoring still needs separate manual transcripts if requested.

## Candidate worksheets

| Worksheet | Original filename | Cases | Cases with explicit review notes |
| --- | --- | --- | --- |
| [pdf-001](worksheets-reviewed/pdf-001.md) | 10-common-hibernate-mistakes-that-cripple-your-performance-free.pdf | 3 | 2 |
| [pdf-002](worksheets-reviewed/pdf-002.md) | 9rules.pdf | 3 | 1 |
| [pdf-003](worksheets-reviewed/pdf-003.md) | Alpha_Casino_LeadMagnet_V28.pdf | 3 | 2 |
| [pdf-004](worksheets-reviewed/pdf-004.md) | Catalogue_of_Czech_TOYS-and-GAMES.pdf | 3 | 2 |
| [pdf-005](worksheets-reviewed/pdf-005.md) | Full Process for Coding with AI Coding Assistants.pdf | 3 | 2 |
| [pdf-006](worksheets-reviewed/pdf-006.md) | gurkan03tableschairs.pdf | 3 | 3 |
| [pdf-007](worksheets-reviewed/pdf-007.md) | Herbrew_Casino1.pdf | 3 | 3 |
| [pdf-008](worksheets-reviewed/pdf-008.md) | imc_telemetry-solutions_EN-201810_WEB.pdf | 3 | 3 |
| [pdf-009](worksheets-reviewed/pdf-009.md) | Maven, IntelliJ Build & Run Guide-2.pdf | 3 | 0 |
| [pdf-010](worksheets-reviewed/pdf-010.md) | phillippine_weather_PAGASA.pdf | 3 | 1 |
| [pdf-011](worksheets-reviewed/pdf-011.md) | Print-Ready-file-for-Know-the-Odds-4pg-brochure__165223_GAMING_V01.pdf | 3 | 2 |
| [pdf-012](worksheets-reviewed/pdf-012.md) | Qwopus3-5-27b-Colab_complete_guide_to_llm_finetuning.pdf | 3 | 2 |
| [pdf-013](worksheets-reviewed/pdf-013.md) | t4.pdf | 3 | 3 |
| [pdf-014](worksheets-reviewed/pdf-014.md) | Technion_AI_change_cse.pdf | 3 | 3 |
| [pdf-015](worksheets-reviewed/pdf-015.md) | Technion_programing_casino.pdf | 3 | 2 |
| [pdf-016](worksheets-reviewed/pdf-016.md) | חוברת חקלאות מוגבר-חגית חלד.pdf | 3 | 1 |
| [pdf-017](worksheets-reviewed/pdf-017.md) | שם-קוד.pdf | 3 | 2 |

## Validation and limits

All 17 source hashes still match the inspection inventory; all submitted worksheet hashes were checked. IDs, JSONL encoding/types, per-PDF three-case coverage, answerability/fact/evidence consistency, source/reference hashes and actual page ranges were checked. Added evidence pages to the draft manifest. No frozen manifest, ingestion, installation, model download, service operation or parser benchmark was performed. Visual review covers referenced pages/selected figures; it does not certify absence across every page. The corpus identity warnings in the submitted text were not supported by the originals: page counts, photographs, tables and screenshots are present.

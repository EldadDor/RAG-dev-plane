# PDF parser comparison corpus

**Task:** RAG-A-01
**Last reviewed:** 2026-10-10
**Status:** Intake protocol and rubric proposal; corpus/references not frozen.

Copy `corpus.example.json` to a private directory outside the repository and
replace its empty document list with permitted local PDFs. No non-archived PDFs
were found in repository discovery. Do not commit private source paths, PDFs,
extracted content, screenshots, answers or experiment results. The future
comparison command must require an explicit output directory outside the Git
checkout for private runs. The example is a template, not a runnable benchmark.

Target 12–20 documents and 30–50 manually verified questions. Include ordinary
text, two columns, tables with units/footnotes, labeled diagrams, scanned pages,
mixed scanned/text pages, Hebrew and mixed English/Hebrew. Track coverage as
multiple categories per document; use separate malformed/encrypted error fixtures.

Each manifest document requires `id` (opaque unique ID), `source_path` (private
absolute local path), `source_sha256`, `categories`, `languages`,
`inspection_pages` (one-based), `permission_basis` and `references_path`.
References are UTF-8 JSONL, one object per question: `id`, `document_id`,
`question`, `answerable`, `expected_facts`, `evidence` (page, visible quote/table
cell or figure label), `verified_by` and `verified_on`. Unanswerable cases have
empty facts/evidence and a manually checked reason. Separate page reference text
and expected reading order may accompany question evidence for extraction scoring.
Do not derive references from either parser's output or model-generated answers.

Freeze manifest/reference hashes and experiment settings before comparing:
parser/version/options, OCR engine/languages/model revisions, local artifacts,
machine/OS/CPU/RAM, serial execution, file/page/time/memory limits and one cold
plus three warm runs. Proposed limits and adapter contract are in
[the Stage A design](../../docs/rag_pdf_experiment_design.md).

| Dimension | Required manual evidence | Proposed acceptance |
| --- | --- | --- |
| Text coverage | Selected page transcript and critical facts | No loss of simple-text critical facts versus reference |
| Reading order | Verified paragraph/column sequence | Record correct/inspected transitions per category |
| OCR / RTL | Verified Hebrew/mixed-script text | Per-language character edit distance; record normalization rules; manually inspect numbers/punctuation |
| Tables | Headers, exact cells, signs, decimals, units and footnotes | No loss of critical values; report exact matches/inspected cells |
| Diagrams | Visible labels and source association | Labels assessed only where engine supports extraction; do not claim visual understanding |
| Provenance | Original page, block and asset association | Zero wrong page/asset links in inspected sample |
| Failures | Malformed/encrypted, missing engine/model, timeout | Explicit failure/partial status; no hidden fallback |
| Resources | Initialization, cold/warm timings and measured peak memory | Stay within operator-approved ceilings; disclose unavailable measurements |

Report per-document outcomes and denominators, then category summaries. Character
count is diagnostic only. A candidate must improve at least one difficult category
without unexplained regressions and pass offline correctness/isolation checks.
Retain baseline output and failed examples. This small corpus cannot establish
statistical significance. Extraction success does not imply RAG answer improvement;
paired indexed evaluation follows in Stage C after its own approval.

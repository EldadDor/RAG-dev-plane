# PDF parser comparison corpus

**Task:** RAG-A-01
**Last reviewed:** 2026-10-16
**Status:** User-approved corpus frozen; earlier runs retained. PDFium revision approved on 2026-10-13; paired corpus runs and 124-output audit complete. Separate telemetry revalidation covers exact UTF8 export and export-time clamping warnings. See [the comparison](corpus/PDFIUM_COMPARISON.md).

Copy `corpus.example.json` to a private directory outside the repository and
replace its empty document list with permitted local PDFs. The user explicitly
chose to copy, commit and push the supplied corpus/review artifacts under
`evaluation/pdf_parsers/corpus`, and approved every worksheet on 2026-10-13.
That corpus now has a validated original `corpus.frozen.json` and location-only `corpus.relocated.json` and 47 cases across 17 PDFs;
see [the release report](corpus/GOLDEN_CASES_VALIDATION.md).
Other private corpora and extraction run outputs remain outside Git. The
comparison command requires an explicit output directory outside every Git
checkout. `corpus.example.json` remains a template, not a runnable benchmark.

Target 12–20 documents and 30–50 manually verified questions. Include ordinary
text, two columns, tables with units/footnotes, labeled diagrams, scanned pages,
mixed scanned/text pages, Hebrew and mixed English/Hebrew. Track coverage as
multiple categories per document; use separate malformed/encrypted error fixtures.

Each manifest document requires `id` (opaque unique ID), `source_path` (private
absolute local path), `source_sha256`, `categories`, `languages`,
`inspection_pages` (one-based), `permission_basis`, `references_path` and
`references_sha256`. The manifest requires `status: "frozen"` to run. The template
remains deliberately unfrozen and fails validation until populated and reviewed.
References are UTF-8 JSONL, one object per question: `id`, `document_id`,
`question`, `answerable`, `expected_facts`, `evidence` (objects with `page` and
`source_evidence`: visible quote/table cell or figure label), `verified_by` and
`verified_on`. Unanswerable cases have
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

## Implemented extraction command

The command is available after G2 approval on 2026-10-10. It requires human-verified
references even for extraction-only runs. Use private absolute source/reference
paths and SHA-256 hashes. Outputs must be outside every Git checkout; on this
machine the user's home is also a checkout, so use an explicitly chosen private
directory elsewhere. The command rejects an existing output directory.

Baseline-only run in the existing environment:

```powershell
.venv\Scripts\python.exe scripts/compare_pdf_parsers.py `
  --manifest E:/Private/pdf-experiment/corpus.json --parsers pypdf `
  --output E:/Private/pdf-experiment/run-001
```

After separately authorized dependency/model preparation, compare both parsers:

```powershell
<experiment-python> scripts/compare_pdf_parsers.py `
  --manifest E:/Private/pdf-experiment/corpus.json --parsers pypdf docling `
  --artifacts-path E:/Private/pdf-experiment/docling-models `
  --max-memory-mib <approved-budget> --timeout 180 `
  --output E:/Private/pdf-experiment/run-002
```

These paths and the memory budget are examples, not provisioned resources.
`--ocr --ocr-languages en --ocr-models-path <prepared-EasyOCR-models>`
enables explicitly selected English EasyOCR; no OCR engine auto-selection occurs.
EasyOCR 1.7.2 does not support Hebrew (`he`); Hebrew OCR requires a separately
configured compatible engine, so do not use this option as a Hebrew treatment.
The approved Tesseract option is explicit:

```powershell
<experiment-python> scripts/compare_pdf_parsers.py `
  --manifest <frozen-manifest> --parsers docling --output <fresh-private-output> `
  --artifacts-path <prepared-Docling-artifacts> --ocr --ocr-engine tesseract `
  --ocr-executable <isolated-tesseract.exe> --ocr-models-path <prepared-tessdata> `
  --ocr-languages heb eng --pdf-backend pypdfium2 `
  --max-memory-mib 8192 --timeout 180 --warm-runs 3
```

The user approved the [backend revision](corpus/PDF_BACKEND_REVISION.md)
on 2026-10-13. Both new Docling treatments explicitly use `--pdf-backend pypdfium2`;
omit the OCR arguments for its paired no-OCR treatment. The original default
`docling_parse` remains selectable. Backend selection/class and pypdfium2 version
are recorded in processing identity; failures never trigger backend fallback.
Tesseract requires explicit native language files plus osd.traineddata and
configs/tsv; missing files fail before initialization. The worker alone sets
TESSDATA_PREFIX so Docling's language discovery sees that prepared directory.
Native executable/model/config hashes and normalization policy are recorded
in processing identity. No language-code translation or engine fallback occurs.
OCR is disabled by default, including for Docling. Language support and mixed RTL
accuracy remain unmeasured; missing/unsupported models fail without fallback.

Each document uses a new serial CPU worker per engine; converter initialization
is timed separately. The first parse is labeled cold (a fresh process/converter,
not a flushed OS disk cache), followed by at least three warm parses using that
converter. Byte/page limits and a killable initialization/extraction timeout apply.
Docling requires an explicit memory budget, currently enforced on Windows using
the worker's lifetime peak working set. This is not a per-parse allocation metric,
GPU memory measurement or whole-machine limit. Unsupported memory enforcement
fails rather than ignoring the budget. Baseline-only runs may omit memory limits;
unavailable measurements are null with an explicit method label.
Native Tesseract workers additionally enter a Windows job before initialization.
The job caps aggregate private commit across the worker/native children and kills
the process tree on cleanup. Job private-commit peaks are reported separately
from the existing worker working-set peaks. The same 8192 MiB limit applies to
both; native over-budget peaks fail conservatively, including rejected allocation
attempts reflected by the counter. Unknown worker exits include the exit code.

Workers disable Hugging Face online mode and Python socket connections/sends;
Docling receives local PDF bytes, local artifact paths, CPU-only options, disabled
remote services/plugins and disabled picture descriptions/classification.
These controls cover this pipeline's Python network paths, not an OS-level
sandbox for arbitrary native plugins. No services are started and no RAG stores,
configuration or provider clients are imported. Package installation and model
downloads are separate actions; this command never prepares them automatically.

`report.json` records initialization/run timing, package versions, settings,
warnings/failures and manifest hash. Each engine/run has raw JSON, normalized
JSON, assembled text and linked PNG assets where available. `source.pdf` and
`references.json` are private inspection snapshots; `inspection.md` points to
each treatment. Source-byte changes during comparison fail the run.

The current text export writes exact UTF8 bytes, preserving embedded carriage
returns. Read with `read_bytes().decode("utf-8")` for offset-sensitive checks;
universal-newline reading can change parser text. Original corpus exports used
Windows LF-to-CRLF translation; their lossless audit and exact-text companion
files are recorded in the comparison report. Original files are retained.
The original telemetry normalization policy `export_clamp_pages_without_boxes_v3` captures warnings
through conversion and export. Upstream-clamped pages produce partial results
with normalized boxes omitted; text/page IDs and raw output remain available.
Raw coordinates may already be clamped, so they do not recover original geometry.

On 2026-10-14, `picture_children_export_clamp_pages_without_boxes_v4` additionally
traverses text nested under pictures, which the default Docling iterator omitted.
It changes processing/block identity and retains the existing clamping disclosure.
47 focused tests and 31 saved-export replays passed; no model treatments were rerun.
See [the original-case scorecard and correction evidence](corpus/EXTRACTION_SCORECARD.md).

The later v5 policy `picture_parent_document_index_export_clamp_pages_without_boxes_v5`
preserves nearest-picture source-ref/block-ID links and serializes `document_index`
items through the existing table path. 52 focused tests and 31 in-memory saved-document
replays passed; original outputs remain unchanged. Replay captures raw-loading
clamping warnings and omits affected boxes. See [fidelity follow-up](corpus/NORMALIZATION_FIDELITY_REVIEW.md).

Failed or partial extraction returns exit code 1. Exit code 0 establishes extraction
completion only; manual rubric inspection and paired RAG evaluation remain pending.

## Optional dependency preparation

The separate `pyproject.toml` declares the `pdf-experiment` group. It is outside
the application's dependency configuration. `requirements-windows-py314.txt`
freezes the 113-package metadata resolution for CPython 3.14/Windows x86_64, with
an upload cutoff of 2026-10-11. The direct pins are Docling 2.137.0 with EasyOCR
and pypdf 6.12.1. On 2026-10-13 all 113 pins installed into the isolated
experiment environment, native imports passed, and local Heron/TableFormer
artifacts passed an offline smoke. See the
[runtime results](corpus/DOCLING_RUNTIME_RESULTS.md).

Reproduce the metadata-only wheel check without changing the application lock:

```powershell
uv pip compile --directory evaluation/pdf_parsers --group pdf-experiment `
  --python-version 3.14 --python-platform x86_64-pc-windows-msvc `
  --only-binary :all: --no-python-downloads --no-config `
  --exclude-newer 2026-10-11 --output-file <scratch-requirements-file>
```

Before installation, review package and model licenses and approve a private
environment/artifact directory and resource budget. Then install from the frozen
requirements into that isolated environment, prove imports, prepare approved
models and prove warmed offline parsing. Metadata resolution proves compatible
wheel candidates are published; it does not prove installation, ABI behavior,
Docling parsing, OCR or Hebrew support. The application runtime remains Python 3.14.


## Assigned-document indexed evaluation (RAG-C-03)

The G2-approved optional document scope is implemented and offline-validated.
pypdf remains the user-approved production default. This does not authorize a
live API reload, provider calls, reingestion or a new extraction run.

Prepare a new private dataset from the frozen manifest and successful saved
index reports with `scripts/prepare_pdf_benchmark.py --assigned-document`.
Omit that switch to retain workspace-wide positive-only preparation. All
questions/reference bytes stay frozen; only the previously recorded reference
defect is excluded from derived facts. Zero-chunk reports, including unchanged
skips without positive counts, do not establish availability. Multiple reports
select the intersection of their available documents, using identical profiles.

The prepared 2026-10-16 datasets contain 42+5 pypdf, 28+2 no-OCR and 29+3 OCR
positive+negative cases. [Paths and hashes](corpus/RAG_C03_PREPARATION.json)
refer to new private files; they do not replace the original Stage C datasets.
Availability reflects saved publication reports, not a fresh database check.

Before an explicitly authorized live run, verify the running API has the updated
OpenAPI `document_id` field, workspace access and the intended model/chunking
publication identity and nonzero counts. Verify no indexing is concurrent and
that saved ingestion evidence still matches current publication. Missing scoped
context can otherwise resemble successful abstention. The live adapter checks
OpenAPI capability, null scoped session IDs, response shape and every returned
citation's document ID; these do not replace publication-readiness checks.

Use `scripts/run_benchmark.py --dataset <new-cases.jsonl> --output <new-private-report.json>
--api-url <running-api> --workspace-id <treatment-workspace> --model-profile bge-m3
--chunking-profile default --top-k 5` after that authorization/preflight.
Each successful case makes two complete chat requests in fresh/stateless scope.
`--responses-output` optionally names the paired-response artifact; otherwise it
is `<output>.responses.json`. Both outputs must be new and outside Git checkouts.
The report records dataset/response hashes and zero-based response indices for
each case; the paired file retains both requests, answers, citations and order.
Responses expose shortened snippets, not complete retrieved chunks. First-probe
retrieval metrics and second-probe answer/snippet proxies remain distinct.

Negatives use `answerable: false`, empty expected facts and an explicit document
ID. Positive coverage/faithfulness metrics are null for negatives. Exact
canonical refusal after whitespace normalization scores `abstained=1`; a refusal
with added claims scores 0. A noncanonical appropriate refusal also scores 0
under this strict policy and needs manual review. Empty/malformed/failed calls
are failures, never successful refusals; unavailable documents stay in separate
preparation evidence. The report summary separates positive cases, negative
cases, failures, scored negatives and exact refusals. It does not convert
retrieved context or the API `grounded` flag into correctness acceptance.

# Stage C isolated indexed comparison

**Reviewed:** 2026-10-15
**Task:** RAG-C-01 — authorized G2 design and local ingestion.
**Status:** Authorized isolated experiment complete; production selection remains unresolved.

**Follow-up:** [RAG-C-02 saved-answer review](STAGE_C_ANSWER_REVIEW.md) examines
all 99 saved second-request answers against approved facts and source evidence.
Matched OCR fact coverage improves modestly, but incorrect claims, entity/page
attribution errors and availability loss prevent an overall acceptance claim.
Original metrics and artifacts below remain unchanged.

## Fixed scope

Frozen 17 PDFs and 47 reference cases; original questions/source/reference bytes
preserved. Derived datasets omit the previously recorded invalid descriptive
reference fact. Five assigned-document negatives are deferred because the current
chat API cannot enforce their document-only scope.

Three dedicated `rag-stage-c-*` workspaces use bge-m3:latest (1024 dimensions),
the default 800-character/120-overlap chunker, top-five retrieval, no reranking
and the configured local Dicta chat model. The application PDF default is pypdf.
Docling runs in the prepared isolated CPU environment, with PDFium and optional
prepared Hebrew/English Tesseract; no new dependency or model download.

Only complete, hash-validated and stable cold/three-warm extractions are indexed.
Budgets are 50 MiB/file, 200 pages, 180 seconds per extraction and 8192 MiB worker
memory. Partial outputs and timed-out warm passes are excluded without fallback.

## Current evidence

| Treatment | Publishable documents / 17 | Published chunks | Eligible positive cases / 42 |
| --- | --- | --- | --- |
| pypdf | 17 | 809 | 42 |
| Docling no OCR | 11 | 432 | 28 |
| Docling OCR | 12 | 327 | 29 |

Fresh no-OCR extraction: all 17 pypdf records completed; Docling had 11 completed,
four partial and two failed records. Dedicated baseline and no-OCR ingestion
completed. Fresh OCR extraction: 12 completed, one partial and four failed
records; validation and dedicated indexing completed. Database counts match all
three reports, and all 1,568 published chunks contain extraction-block and
source-page metadata. Baseline and no-OCR live
benchmarks completed without request failures and with stable retrieval order
on all 42 and 28 cases respectively. OCR completed all 29 cases without request
failures and with stable retrieval order. Total: 99 evaluated case runs.

## Paired live metrics

Baseline all 42 cases: source Recall@5 39/42 (0.9286), MRR 0.9167,
answer-overlap proxy 0.5696, faithfulness proxy 0.5117; median two-request
latency 16.39 seconds.

| Same 28 case IDs | pypdf | Docling no OCR |
| --- | --- | --- |
| Source Recall@5 | 27/28 (0.9643) | 27/28 (0.9643) |
| Source MRR | 0.9464 | 0.8958 |
| Answer-overlap proxy | 0.6362 | 0.6697 |
| Faithfulness proxy | 0.5861 | 0.5684 |
| Median two-request latency (seconds) | 16.70 | 14.62 |

The no-OCR result is mixed: equal source recall, lower MRR, higher answer-overlap
proxy and lower faithfulness proxy. Coverage is only 28/42 answerable cases due
to extraction exclusions. No significance test or production superiority claim.

| Same 29 case IDs | pypdf | Docling OCR |
| --- | --- | --- |
| Source Recall@5 | 27/29 (0.9310) | 29/29 (1.0000) |
| Source MRR | 0.9138 | 0.9770 |
| Answer-overlap proxy | 0.5951 | 0.6539 |
| Faithfulness proxy | 0.5348 | 0.5645 |
| Median two-request latency (seconds) | 17.13 | 10.07 |

OCR improves these retrieval/proxy metrics on its matched subset, with only
29/42 answerable cases available. Its subset differs from no-OCR's; their
aggregate means are not a direct paired candidate comparison. No statistical
significance or exact-fact acceptance is established. Different concurrent load
conditions preclude treating latency differences as a parser speed improvement.

[Machine summary](STAGE_C_SUMMARY.json) records matched IDs, unrounded metrics,
extraction exclusions, actual model identities and private artifact SHA-256s.

95 focused tests passed for prepared ingestion, assets, loaders, model profiles,
evaluation and extraction. Full application suite and independent human answer
adjudication were not run.

## Interpretation limits

Compare each candidate with baseline on matching case IDs and report availability
separately. Recall@5 means the expected document appeared among returned sources;
it does not establish that the exact fact or page was retrieved. Answer relevance
and faithfulness are existing token-overlap proxies, not correctness judgments.
Latency covers two sequential complete chat requests per case. Second responses
and citations are retained privately for selective inspection.

OCR extraction ran alongside indexing and baseline chat evaluation. Resource
timings/timeouts therefore reflect that load condition and are not controlled
idle-machine measurements. Native extraction itself remained serial.
OCR live benchmarking began after extraction and indexing finished, so latency
differences across treatments also include different concurrent load conditions.

Selective baseline response inspection: pdf-003-q1 gives diagram labels but
appends an insufficient-information sentence; pdf-004-q1 omits several expected
company details; pdf-005-q1 includes the three expected rules. These are assistant
observations against the approved facts, not independent human adjudication.
For pdf-003-q1, the no-OCR answer additionally mixes table-of-contents entries
with diagram labels and appends the same insufficient-information sentence.
The OCR response for that case repeats table-of-contents entries instead of the
requested diagram labels despite retrieving the expected document.

## Decision and follow-up

Keep pypdf as the production default. Stage C demonstrates a usable isolated
prepared-output ingestion path and a bounded OCR retrieval benefit, not overall
parser fidelity acceptance. Prioritize independent exact-fact/cell/citation
adjudication, a design for assigned-document negatives, and controlled equal-load
resource/latency measurements before treatment selection. Native failures,
glyph/RTL/table defects and answer repetition remain visible limitations.

Private outputs, datasets and answers are under
`E:\Workspace\AI_Stuff\Pdf_Examples\Comparison_Runs\stage-c-*2026-10-15-r1*`.
Models and private artifacts stay outside Git. The existing migration 008 and
local API startup were separately approved and completed; no new migration,
production parser promotion, push/merge or phase closure is implied.

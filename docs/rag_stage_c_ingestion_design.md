# Stage C local ingestion and indexed comparison design

**Task:** RAG-C-01
**Date:** 2026-10-15
**Status:** G1 intake/laptop readiness and this specific G2 structural design
explicitly approved by user on 2026-10-15.

## Chosen boundary

Add a local operator command, `scripts/ingest_local.py`, selecting pypdf,
Docling/PDFium without OCR, or Docling/PDFium with prepared Hebrew/English
Tesseract. Invoke the existing ingestion service with an explicitly resolved
document loader. Standard HTTP ingestion and the production pypdf default keep
their existing contract. Do not add `pdf_parser` to the HTTP request schema.

Docling remains in the already prepared isolated Python environment. Reuse the
approved serial comparison worker and its validated normalized result/assets
boundary; the main application environment does not import Docling or acquire
new dependencies. Fresh normalized artifacts must be generated with current v5
code before indexing. The 2026-10-14 in-memory replay hashes are verification
evidence, not reusable extraction files or fresh model acceptance.

New local ingestion/result-mapping modules and loader injection are the specific
G2 triggers. Directory and single-file selection use the same resolved options.
The proposed command accepts explicit source manifest, treatment, authorized
workspace, existing ready model profile and chunking profile. Reject unknown
treatments and missing/unverified extraction results before writes.

## Mapping and publication identity

Map normalized text, page markers, source SHA-256, parser/settings/versions and
block ranges into the existing internal Document representation. Map PNG assets
to DocumentAsset, preserving raw source refs, picture-parent links, captions,
offsets and byte hashes. Validate source/asset hashes, normalized offsets, pages,
parent IDs and result-directory containment before loading private bytes.

Derive chunk provenance from overlap with source block ranges. Preserve all
overlapping pages/block refs; attach picture assets through verified child/parent
relationships. Do not infer an asset relationship solely from nearest ordinal.
Retain the existing source-only anchor behavior for legacy document types.

For this explicit experiment path, derive a canonical publication hash from
source SHA-256, extracted-text/asset hashes, parser versions/settings/normalization
policy and resolved chunker configuration. Keep original source SHA-256 separately
in metadata. Reuse the existing stored hash and transactional replace_document
boundary; changed parser settings must defeat the unchanged-document skip.
Leave the ordinary legacy ingestion path unchanged until an explicit rollout.
Model-profile dimensions and the existing embedding-cache scope remain intact.

No new SQL schema objects or migration are planned. Stage assets before replacing
the document publication. Parse/validation/embedding failure preserves the last
usable publication; do not delete shared asset bytes during rollback. Reject
partial/failed extraction for publication in this first implementation; record
the document failure rather than substituting pypdf. Candidate resource and
fidelity failures remain measurable outcomes, not exceptions to acceptance.

## Isolated live experiment

Use the frozen 17-document/47-case manifest and unchanged source/reference bytes.
Provision distinct workspaces for pypdf, Docling no-OCR and Docling OCR, with
matching membership, embedding/model profile, chunking, retrieval and answer
settings. Discover the running deployment and authorized principal before
provisioning names; avoid modifying existing user workspaces or publications.
Read existing operator workspace conventions before issuing row writes.

Retain the previously approved serial CPU limits: 50 MiB/file, 200 pages,
180-second extraction timeout, 8192 MiB worker/native memory, one cold and three
warm parses. Failed/partial documents remain visible in the all-document
denominator and cannot silently enter the candidate index. Compare matched
successful document/case subsets and also report overall availability separately.
Preserve all baseline publications and previous extraction evidence.

Use existing local embeddings and ready storage tables; no automatic cloud
fallback, model downloads, migration execution or service reconfiguration.
Check endpoint health/capabilities before writes. Laptop-readiness/ingestion
authorization is recorded; separately mandated service start/stop or structural
changes must be presented if required by the discovered deployment.

Verify authentication and fixed model/chunking scope before using the existing
live benchmark runner. Add local runner support only where existing parameters
cannot express the fixed scope. Run fresh sessions and record per-question
source Recall@k/MRR, verified facts, table values, citations, abstention and
latency. Report missing treatments explicitly; no aggregate improvement claim
from extraction success alone. OCR noise, glyph, table-row and RTL defects remain
unresolved and this experiment does not select a new production default.

## Rejected alternative and rollback

Reject introducing parser selection into the HTTP API and loading Docling inside
the application process now. That would expand the public contract and native
runtime/resource exposure before an indexed benefit is established. The local
CLI and prepared-output boundary keep treatment choices explicit and reuse the
existing application publication path.

Rollback selects the existing pypdf loader. The baseline workspace is retained;
restoring a previously replaced publication requires explicit pypdf reingestion,
not merely changing a parser setting. No migration rollback is needed. Deleting
benchmark workspaces or private artifacts requires a separate cleanup decision.

## Checks before live writes

Focused fake-provider/store tests cover baseline compatibility without optional
imports; file/directory option propagation; invalid/unavailable/partial results;
hashes/path containment and asset associations; changed processing identity;
unchanged skip; failed replacement; workspace/model scope; and dry-run with no
model/provider/store writes. Dry-run reports extraction pending when model-backed
artifacts are absent. Validate actual v5 extraction artifacts separately before
real indexing, then run the isolated ingestion and paired benchmark.

Design evidence: current PDFLoader/registry choose only pypdf; ingest_path imports
those loaders directly and skips by stored content_hash; asset matching currently
uses source offsets and nearest-chunk fallback; Document metadata can carry
internal extraction identity; replace_document is the existing publication
boundary. No source implementation, ingestion, live tests or service operations
were performed during this design preparation.

## Operator command and implementation progress

G2 was approved 2026-10-15. `scripts/ingest_local.py` consumes fresh validated
private results through `PreparedPDFLoader`; it defaults to a model/provider/store
free dry run and reports extraction pending when artifacts are absent. Complete
cold/warm results must agree; partials/timeouts, altered hashes, escaped asset
paths and invalid parent links are rejected. Single-file and complete manifest
directory inputs share the same resolved loader. The existing API schema and
production PDF default are unchanged.

Example after generating the fresh approved-budget extraction run:

```powershell
.venv/Scripts/python.exe scripts/ingest_local.py --manifest <frozen-manifest> --source <manifest-PDF-root> --run-root <completed-private-run> --treatment docling-noocr --workspace-id rag-stage-c-docling-noocr-20261015 --model-profile bge-m3 --chunking-profile default --provision-workspace --apply --output <new-private-ingestion-report.json>
```

Use treatment `pypdf` for the baseline and `docling-ocr` for the prepared
Hebrew/English OCR run. Workspace creation is explicit and existing workspaces
require `--resume` with matching treatment/manifest identity and owner membership.
Do not reuse ordinary user workspaces. Source and references stay frozen; private
extraction/index/answer artifacts stay outside Git. No cloud fallback is supported.

`scripts/prepare_pdf_benchmark.py` derives positive cases from actual index
availability and records all 47 frozen case statuses, input hashes and the prior
documented reference-fact exclusion. Questions/reference bytes are unchanged.
The five assigned-document negatives remain explicitly deferred: current chat
requests/evaluator cannot enforce their document-only scope, and they are not
recast as positive facts or claimed as abstention evidence. Compare baseline and
each candidate on matched case IDs, with availability/failures reported separately.
The live runner now accepts explicit model/chunking profile options already
supported by the existing HTTP chat contract.

Operator permission for the missing migration 008 and API startup was separately
requested and approved. The existing additive migration is now applied and the
local API is healthy. The configured LAN Ollama embedding probe returned 1024
dimensions for the ready bge-m3 profile. This operational readiness does not
certify parser fidelity or promote a default.

## Delivery

Authorized Stage C implementation and live comparison completed 2026-10-15.
95 focused tests passed. All three dedicated workspaces were indexed from fresh
validated outputs and checked against stored chunk counts/provenance. The live
runner completed 42/28/29 positive case runs with fixed profiles and no request
failures. [Results, paired metrics and limitations](../evaluation/pdf_parsers/corpus/STAGE_C_RESULTS.md)
and [artifact hashes](../evaluation/pdf_parsers/corpus/STAGE_C_SUMMARY.json)
are retained evidence. Five document-scoped negatives remain deferred; exact-fact
acceptance and parser promotion remain unresolved. No push/merge or phase closure.

# RAG PDF extraction experiment — Stage A design

**Task:** RAG-A-02
**Last reviewed:** 2026-10-10
**Status:** Concrete G2 proposal; runtime implementation has not started.

## Decision requested

Approve an extraction-only adapter boundary and comparison command for Stage B.
Use internal normalized results, a pypdf baseline and a lazily imported Docling
candidate. Initially keep the experiment independent of production ingestion.
Approve an optional `pdf-experiment` dependency group only after an isolated
Windows/Python 3.14 resolution and wheel check selects compatible pins. Model
downloads and model-using runs require their separate preparation decision.

Rejected alternative: install RAG-Anything/LightRAG and redirect production
ingestion through its storage pipeline. That expands dependencies and replaces
existing workspace, vector-store and provider contracts without comparison
evidence. No upstream source code will be copied in this stage; inspect and
record immutable upstream revisions if later implementation adapts fragments.

No SQL migration or public API change is proposed. Rollback removes the optional
experiment dependency and modules; existing PDFLoader remains the ingestion
default. Production selector and processing identity belong to Stage C.

## Proposed implementation boundary

| Proposed file | Responsibility |
| --- | --- |
| `src/app/loaders/pdf_extraction.py` | Versioned result/block/options dataclasses, validation and deterministic text assembly; no optional engine imports |
| `src/app/loaders/pdf_parsers/pypdf_adapter.py` | Page-level baseline using the existing extraction algorithm |
| `src/app/loaders/pdf_parsers/docling_adapter.py` | Lazy converter construction; explicit local model artifacts; structured item mapping |
| `scripts/compare_pdf_parsers.py` | Validate frozen manifest/references, verify input hashes, run each selected engine and serialize artifacts/reports |
| `tests/test_pdf_extraction.py` | Synthetic baseline and fake-engine contract/failure/isolation checks |

Adapters expose `extract(path, options) -> ExtractionResult`. Resolve options
once per engine/run and reuse heavy converters. Read/hash the same immutable
source bytes for both treatments; fail if a file changes during the run.
Do not import API dependencies, construct stores, load `.env`, call providers,
index chunks or write private assets from this command. Reject fallback and
unknown engines. Missing package/model errors identify preparation needed.

## Normalized format v1

Result fields: format version, source SHA-256, opaque document ID, page count,
engine/package versions, effective settings, status (`completed`, `partial`,
`failed`), warnings, assembled source text, ordered blocks and extracted assets.
Failures are recorded per input/engine and produce a nonzero command exit;
partial extraction is visible and cannot silently pass a correctness gate.

Each block contains ID, ordinal, kind (`text`, `table`, `image`, `equation`),
source text, structured payload when available, one-based source page(s),
heading path, optional bounding box, optional asset anchor and half-open text
offsets `[start, end)`. Offsets index Python Unicode characters in the exact
assembled text, including page markers and separators, rather than UTF-8 bytes.
Require `assembled_text[start:end] == block.source_text` for text-bearing
blocks. Empty/image-only blocks have a zero-width anchor. Keep multi-page table
provenance intact; do not infer page membership from text matches.

Stable IDs are scoped to source revision, normalized-format version, parser
identity and deterministic item ordinal; cross-engine block IDs need not match.
Preserve missing coordinates as null. Normalize available coordinates to a
documented top-left page coordinate system, with page dimensions/units stored.
Store table cells, headers, spans and units when available; flag unsupported or
incomplete structures explicitly. No model-generated interpretation is produced
by this stage. Asset bytes remain in the private experiment output and are
referenced by relative file name, hash and block anchor in normalized JSON.

The baseline returns one text block per page and exactly reproduces existing
`[PAGE n]` markers and separators. It declares layout, table/image detection and
OCR unsupported. Empty scanned pages remain diagnostically empty. Keep the
production `DocumentLoader.load(path) -> Document` contract unchanged for Stage B.

## Compatibility findings and next proof

The repository requires Python 3.14 and reports Python 3.14.2/uv 0.12.19.
The virtualenv launcher answered `--version`, but a subsequent script execution
failed to resolve its backing interpreter inside the sandbox. Resolve executable
access before claiming local runtime validation; do not recreate the environment
or downgrade the application interpreter as an incidental repair.

Primary sources checked 2026-10-10:

- [Docling package metadata](https://pypi.org/project/docling/) declares
  Python >=3.10,<4 and lists Python 3.14 and Windows. This is eligibility evidence,
  not proof of this machine's transitive wheel or runtime compatibility.
- [Official installation guide](https://docling-project.github.io/docling/getting_started/installation/)
  describes Windows support, PyTorch dependency and separately selected OCR engines.
- [Official advanced options](https://docling-project.github.io/docling/usage/advanced_options/)
  documents local model artifact configuration. Require prepared artifacts and
  disable remote services for the experiment.

After G2, resolve dependencies for Windows x86_64/CPython 3.14 in an isolated
scratch environment without altering `uv.lock`; record all versions, native
wheels, resolver outcome and package/model licenses. Then run an import/synthetic
text-PDF smoke check. Prepare models separately and prove warmed parsing offline.
Hebrew OCR capability must be measured; package/platform metadata cannot prove it.
If any native dependency fails, present a supported-runtime local worker with a
versioned JSON boundary as a revised G2 decision instead of silently switching.

## Offline acceptance and deferred operations

Test baseline text equality, Unicode offsets, one-based pages, empty pages,
malformed/encrypted fixtures, deterministic IDs, missing optional package/models,
unknown parser, hash mismatch, partial/failed results, converter reuse and
baseline operation without Docling imports. Use fake converters to exercise
structured tables/images and source-coordinate mapping without model downloads.
Assert the comparison imports no ingestion/store/provider code and makes no
network calls. Assert output refuses overwrite of an existing run directory.

Artifacts record settings, source/reference hashes, versions, initialization,
cold parse and three warm parse timings, warnings and failures. Peak process
memory is nullable with measurement method/limitations; never report unavailable
measurements as zero. Use a serial CPU experiment initially; propose 50 MiB per
file, 200 pages and 180 seconds per extraction with a killable subprocess.
Machine-specific memory and final time ceilings need operator agreement before
real model runs. Do not label synthetic/mock results as a Docling quality result.

Real corpus/reference approval, installation/model preparation, resource budget
and live indexed workspaces remain pending. Stage A reference preparation cannot
be declared complete until permitted files and human-verified answers exist.

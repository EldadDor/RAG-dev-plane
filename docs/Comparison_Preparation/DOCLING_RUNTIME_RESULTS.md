# Docling runtime preparation and no-OCR comparison

**Task:** RAG-B-RUNTIME
**Prepared:** 2026-10-13
**Status:** Runtime/model preparation and offline smoke passed; all 17 sources attempted in the paired no-OCR comparison. Outcomes and remediation are recorded below.

The user approved isolated preparation after reviewing the download explanation.
The application environment, `.env`, Bionic/CHAT_BASE_URL and Ollama are unchanged.
This treatment uses local CPU extraction models and no provider requests.

## Installed environment

`E:/Workspace/AI_Stuff/Pdf_Examples/Parser_Experiment/venv` uses the existing
CPython 3.14.2 interpreter. All 113 frozen Windows package pins installed from
binary wheels. Docling 2.137.0, Docling Core 2.101.1, Docling IBM Models 4.0.3,
PyTorch 2.14.1+cpu, Torchvision 0.29.1+cpu and EasyOCR 1.7.2 import successfully.
EasyOCR's installed language list excludes Hebrew; no EasyOCR weights were
downloaded and no Hebrew OCR capability is claimed.

Published package licenses and wheel hashes were recorded before installation in
`Parser_Experiment/package-metadata.json`; installed versions are retained in
`installed-packages.json`. The inventory includes LGPL (`python-bidi`), MPL
(`certifi`, `tqdm`) and bundled/dependency notices (`pypdfium2`, numerical/native
wheels), in addition to MIT/BSD/Apache/PSF packages. This is local experiment use;
redistribution obligations and all bundled notices require separate review if
the runtime is ever packaged or redistributed.

Actual commands, from the repository directory:

```powershell
uv venv --python C:/Users/eadno1/AppData/Local/Programs/Python/Python314/python.exe `
  E:/Workspace/AI_Stuff/Pdf_Examples/Parser_Experiment/venv
uv pip install --python E:/Workspace/AI_Stuff/Pdf_Examples/Parser_Experiment/venv/Scripts/python.exe `
  --only-binary :all: --no-config -r evaluation/pdf_parsers/requirements-windows-py314.txt
```

## Downloaded artifacts

The default installed pipeline uses Heron and TableFormer accurate mode. Model
cards were checked before weight downloads. Only required weight/config files
and their READMEs were selected; no VLM, OCR, classifier or ONNX model was fetched.
Hugging Face repository metadata resolved mutable refs to immutable commits
before `snapshot_download(..., revision=<commit>, token=False)` fetched files.

| Model | Immutable commit | Published license | Weight SHA-256 |
| --- | --- | --- | --- |
| `docling-project/docling-layout-heron` | `8f39ad3c0b4c58e9c2d2c84a38465abf757272d8` | Apache-2.0 | `00333a43451945aaf89db8ca9c0a17e75d1537c17db60fdb91aa95f4c7929e0c` |
| `docling-project/docling-models`, TableFormer accurate, tag `v2.3.0` | `fc0f2d45e2218ea24bce5045f58a389aed16dc23` | CDLA-Permissive-2.0 | `2a7d6c924b3cd12fb99a09280ca9c33a89c5d60b93253617d2e088c1a40374d9` |

Eight files, including weights/configs/READMEs, are inventoried by size and SHA-256
in `Parser_Experiment/model-inventory.json`; repository identities are also in
`model-revisions.json`. Artifacts are under `Parser_Experiment/models/docling`.
The two weight files total 384,417,384 bytes (about 366.61 MiB).
The preserved download helper now hard-pins those exact commits for reproduction:

```powershell
E:/Workspace/AI_Stuff/Pdf_Examples/Parser_Experiment/venv/Scripts/python.exe -X utf8 `
  E:/Workspace/AI_Stuff/Pdf_Examples/Parser_Experiment/prepare_docling_models.py
```

Sources: [Heron model card](https://huggingface.co/docling-project/docling-layout-heron),
[TableFormer repository](https://huggingface.co/docling-project/docling-models/tree/v2.3.0),
[pinned Docling downloader](https://github.com/docling-project/docling/blob/v2.137.0/docling/utils/model_downloader.py).

## Offline smoke evidence

A generated deterministic one-page PDF contains two facts: color blue and number
42. Its fixture references are explicitly synthetic; they are not human corpus
evidence. The existing runner disabled network access in both workers and ran
one cold/three warm passes for each parser. All eight passes completed and
preserved both facts. Docling initialization took 16.04 seconds and its lifetime
peak working set was 1,139,527,680 bytes (about 1.06 GiB), below the 8 GiB cap.

Output: `E:/Workspace/AI_Stuff/Pdf_Examples/Comparison_Runs/docling-offline-smoke-2026-10-13`.
Smoke completion establishes runtime/artifact compatibility, not corpus quality.

## Frozen corpus comparison

```powershell
E:/Workspace/AI_Stuff/Pdf_Examples/Parser_Experiment/venv/Scripts/python.exe `
  scripts/compare_pdf_parsers.py `
  --manifest docs/Comparison_Preparation/corpus.frozen.json `
  --parsers pypdf docling `
  --artifacts-path E:/Workspace/AI_Stuff/Pdf_Examples/Parser_Experiment/models/docling `
  --max-memory-mib 8192 --timeout 180 --warm-runs 3 `
  --output E:/Workspace/AI_Stuff/Pdf_Examples/Comparison_Runs/pypdf-docling-no-ocr-2026-10-13
```

The run uses the frozen 17-document/47-case corpus, CPU-only serial workers,
50 MiB/200-page limits and the approved 180-second initialization/extraction
timeout. OCR is explicitly disabled. Results and private source/reference/asset
snapshots stay outside Git. All 17 pypdf treatments completed; Docling originally
completed 13, returned 2 partials and failed on 2. All 128 serialized passes passed
source/reference/model/text/offset/asset integrity checks; pypdf reproduced the
earlier baseline exactly. The highest measured completed-treatment Docling peak
was 2.48 GiB. See [the execution comparison](NO_OCR_COMPARISON.md).

The pdf-013 failure was reproduced: six upstream text boxes extend 6.5–17.1 PDF
points above the page frame. The adapter now retains raw coordinates/text, omits
invalid normalized boxes and marks partial output with explicit warnings. It
records normalization policy `bounded_boxes_or_partial_v1` in processing identity.
A separate one-cold/three-warm rerun produced four stable, integrity-checked
partial passes; the original failed run is unchanged. The agriculture-document
180-second timeout remains an explicit failure, with no budget increase.

Supplement: `Comparison_Runs/docling-bbox-partial-pdf-013-2026-10-13`.
Review packet: `Comparison_Runs/pypdf-docling-no-ocr-2026-10-13/golden-case-review.md`.
This packet reproduces the 47 cases and source-page parser text without scoring
them or changing approved references. Manual evidence/rubric scoring remains
distinct from successful extraction.

The user subsequently approved the [Tesseract OCR revision](HEBREW_OCR_DESIGN.md).
Native/model preparation and OCR outputs are documented in
[OCR runtime results](TESSERACT_RUNTIME_RESULTS.md); recurrent native PDF decoder
faults now require the [explicit PDF backend revision](PDF_BACKEND_REVISION.md)
before corpus OCR execution. No production ingestion/provider/configuration change.

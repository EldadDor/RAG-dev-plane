# Tesseract preparation and native OCR stability evidence

**Task:** RAG-B-OCR
**Prepared:** 2026-10-13
**Status:** Tesseract G2 approved and implemented; native/model setup and synthetic OCR verified. Corpus OCR awaits the explicit PDF backend revision because the default native decoder faulted.

## Prepared artifacts

Windows x64 Tesseract 5.5.3.20260724 was downloaded from the official
[Tesseract 5.5.3 release](https://github.com/tesseract-ocr/tesseract/releases/tag/5.5.3).
Package SHA-256 `bee9e3434bd94fd65387d9be28cd467a41f61b1275383b55b0f59a1331270ae4`
matches GitHub's release-asset digest. Windows Authenticode returned UnknownError
for certificate validity; this is recorded rather than claimed as a valid
Windows signature. The signer is Universität Mannheim. 7-Zip extracted the
verified package to a new `Parser_Experiment/tesseract` directory; the installer
was not run and machine PATH/registry/provider configuration was not changed.
The isolated executable reports version 5.5.3.20260724. Its packaged Apache-2.0
notice and all 138 native files were retained/inventoried; bundled dependency
notices remain relevant if redistributing this runtime.

Recognition models are `heb` and `eng`; `osd` is the required orientation/script
auxiliary model, not another selected recognition language. All come from
[official tessdata_fast](https://github.com/tesseract-ocr/tessdata_fast) commit
`87416418657359cb625c412a48b6e1d6d41c29bd`, under Apache-2.0.

| Artifact | SHA-256 |
| --- | --- |
| heb.traineddata | `11f9e43ab227f786352a50f75c94c2e9906f1baba86d93276da19da7ce0904db` |
| eng.traineddata | `7d4322bd2a7749724879683fc3912cb542f19906c83bcc1a52132556427170b2` |
| osd.traineddata | `9cf5d576fcc47564f11265841e5ca839001e7e6f38ff7f7aacf46d15a96b00ff` |
| configs/tsv, from verified native package | `59d079bb75d8b3d7c839a3564580cb559e362c93a9d70f234e421c0c3e767e04` |

Private inventories: `Parser_Experiment/tesseract-release-asset.json`,
`tesseract-native-inventory.json`, `tesseract-model-inventory.json`.
All native/model files, plus eight original Docling artifacts, matched their
inventories after the latest smoke. `.env`, Bionic and Ollama are unchanged.

## Implementation and checks

Existing experiment options/CLI expose `--ocr-engine tesseract`, explicit
`--ocr-executable`, `--ocr-models-path` and native codes `--ocr-languages heb eng`.
The adapter checks prepared language/auxiliary files before initialization and
records their hashes plus the executable hash in processing identity. EasyOCR
Hebrew configuration now fails explicitly. No engine auto-selection/fallback.

Docling's `--list-langs` subprocess ignores its configured tessdata path, so the
worker alone sets `TESSDATA_PREFIX` to the prepared directory. Actual OCR commands
also receive the explicit path. This does not edit `.env` or machine environment.
Orientation detection requires osd.traineddata; TSV parsing requires configs/tsv.
Their absence was discovered in the first smoke attempts and corrected explicitly.

The worker waits for Windows job registration before native initialization.
The original 8192 MiB worker lifetime peak working-set check remains, and a job
adds an 8192 MiB aggregate private-commit cap for the worker/native descendants.
These metrics are different and separately named in results. Native children are
terminated on job cleanup, including timeout/failure. Tests demonstrate native
allocation denial against a 128 MiB test cap, descendant termination and explicit
failure on an over-budget reported job peak. The peak counter observed during
the allocation-denial test included the rejected large allocation attempt; the
runner conservatively fails such an over-budget peak rather than treating it as
compliant. [Windows job memory semantics](https://learn.microsoft.com/en-us/windows/win32/api/winnt/ns-winnt-jobobject_basic_limit_information).

Focused offline command:

```powershell
.venv/Scripts/python.exe -X utf8 -m pytest -q -p no:cacheprovider `
  --basetemp .codex-test-tmp-pdf-ocr-crash tests/test_pdf_extraction.py tests/test_loaders.py
```

**43 passed**, including out-of-frame/non-finite coordinates, OCR configuration
and prepared-file checks, no hidden fallback, native-child cleanup, memory denial,
timeout handling and crash exit-code reporting. Full application suite/live
providers/stores/SQL/production ingestion were not run.

## OCR smoke and unresolved decoder fault

The generated one-page raster fixture was visually checked. It contains
`Revenue -12.50 USD` and `שלום עולם 123` with proper visual RTL placement.
It has no text layer; pypdf returns empty page text, as expected.
References are explicitly synthetic, not claimed as human corpus evidence.

`tesseract-offline-smoke-2026-10-13-r4` completed one cold/three-warm OCR passes
with identical text, logical Hebrew order and the exact signed number/unit.
Peak worker working set was 1,329,717,248 bytes; job peak private commit was
1,347,448,832 bytes, both below 8 GiB. The sparse fixture caused orientation
warnings (too few characters); recognition still used the explicit heb/eng models.
`runtime-audit.json` verifies text/offset/page/hash consistency and all native/model
inventories. Output: `E:/Workspace/AI_Stuff/Pdf_Examples/Comparison_Runs/tesseract-offline-smoke-2026-10-13-r4`.

An earlier `r3` run exited without a result during its second warm pass despite
two correct completed outputs and about 1.25 GiB job peak commit. Windows
Application Error events report access violation `0xc0000005` in
`docling_parse/pdf_parsers.cp314-win_amd64.pyd`; events also recur in the later
successful worker. These are native decoder faults, not Tesseract missing-model
errors. They are retained in `Parser_Experiment/native-pdf-decoder-events.json`.
The passing r4 output therefore does not establish decoder stability.

No corpus OCR run was started after this fault evidence. The reviewable
[PDF backend revision](PDF_BACKEND_REVISION.md) proposes the existing pinned
PDFium backend explicitly for both Docling treatments; it awaits its own G2
decision under the approved native-failure rule. No interpreter change, backend
switch or implicit retry/fallback has been made.

# Hebrew/English OCR treatment — approved G2 revision

**Task:** RAG-B-OCR
**Prepared:** 2026-10-13
**Status:** G2 explicitly approved by the user on 2026-10-13; implementation and isolated preparation verified. PDFium revision separately approved; both corpus treatments and the paired audit are complete. See [results and limits](PDFIUM_COMPARISON.md).

The frozen EasyOCR 1.7.2 package explicitly excludes Hebrew from its supported
language list. The original `he en` treatment cannot meet the experiment scope.
Docling without OCR remains a valid separate comparison treatment.

## Chosen approach

Use Docling's existing `TesseractCliOcrOptions` with explicit languages
`['heb', 'eng']`, local traineddata paths and an explicit native executable path.
Prepare the Windows x64 Tesseract 5.5.3.20260724 build documented by
[UB Mannheim](https://github.com/UB-Mannheim/tesseract/wiki) under a new dedicated
`Parser_Experiment/tesseract` directory. Review the installer signature and
bundled license notices, freeze its hash, and avoid machine PATH/provider edits.
If isolated deployment is unsupported, report that failure before changing scope.

Use `heb.traineddata` and `eng.traineddata` for recognition from the official
[tessdata_fast repository](https://github.com/tesseract-ocr/tessdata_fast), which
contains both language models under Apache-2.0. Resolve a single immutable
repository commit, review notices and record SHA-256 hashes before running.
Fast integer models suit the approved CPU/time ceiling; quality remains to be
measured against the human references. Docling also requires the same-revision
`osd.traineddata` orientation auxiliary and the verified package's `configs/tsv`;
these are explicitly inventoried in [runtime results](TESSERACT_RUNTIME_RESULTS.md).

Extend the existing internal options/CLI with an explicit OCR engine selection,
native executable and tessdata directory; keep missing/unsupported configuration
failures explicit. Update the existing adapter rather than adding production
ingestion wiring. Retain the current EasyOCR option for supported-language runs.
Do not auto-select engines or convert Hebrew language codes silently.

The native OCR process runs as a child of the Python extraction worker. Extend
Windows worker lifecycle/resource enforcement to account for the process tree
and terminate native children on timeout or budget failure. The existing worker
peak metric alone cannot prove native-child compliance with the 8192 MiB cap.
Record the measurement definition and actual engine settings in the run report.
Keep CPU-only serial execution, the 180-second deadline and offline model paths.

## Rejected alternative and rollback

Using a Bionic/Ollama vision-language model for OCR would introduce a generative
extraction treatment and provider/service calls into this isolated parser test.
RapidOCR's published model list also does not establish Hebrew support. Tesseract
has explicit Hebrew traineddata and is already supported by Docling's public API.

No SQL migration or production API/provider configuration change is required.
Rollback reverts the OCR option/runner additions and removes only the new native
experiment runtime/model directories; keep approved PDFs, frozen references and
completed no-OCR results.

## Validation before corpus execution

- Native version and `--list-langs` must confirm `heb` and `eng` from the chosen
  directory; package/runtime/model hashes and license notices must be preserved.
- Focused tests must cover explicit engine selection, language rejection,
  missing native/model paths, no fallback, process-tree cleanup and resource
  enforcement. Keep existing pypdf and no-OCR behavior working.
- A Hebrew/English raster fixture must parse with remote services disabled and
  local artifacts only. Check RTL order, punctuation and numbers explicitly.
- Then run the frozen corpus with one cold/three warm passes and inspect the
  approved evidence. Model availability and successful execution do not prove
  Hebrew OCR accuracy or RAG answer quality.

**Approval recorded:** The user approved G2 for this native OCR dependency, explicit engine/CLI
configuration and process-tree resource controls, followed by isolated setup
and the Hebrew/English OCR comparison under the existing preparation limits.

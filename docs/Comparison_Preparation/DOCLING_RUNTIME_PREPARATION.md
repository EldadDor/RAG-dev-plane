# Docling/OCR setup — concrete approval request

**Task:** RAG-B-RUNTIME
**Status:** G1 preparation approved by the user on 2026-10-13; isolated environment created, package/model preparation in progress.
**Prepared:** 2026-10-13

The human-approved references are frozen and the pypdf baseline has run. The user explicitly approved proceeding after reviewing the model-download explanation. This authorizes the isolated Docling preparation and model execution within the proposed limits. EasyOCR 1.7.2 does not support Hebrew; changing the OCR engine requires a concrete revised design rather than silently running the invalid Hebrew configuration.

## Proposed scope

- Environment: `E:/Workspace/AI_Stuff/Pdf_Examples/Parser_Experiment/venv` using the existing CPython 3.14 interpreter.
- Package source: [frozen Windows requirements](../../evaluation/pdf_parsers/requirements-windows-py314.txt), 113 pins, including Docling 2.137.0, EasyOCR 1.7.2 and pypdf 6.12.1. The application environment and lockfile are unchanged.
- Model artifacts: `E:/Workspace/AI_Stuff/Pdf_Examples/Parser_Experiment/models/docling` and `.../models/easyocr`. Resolve exact required official model revisions, review package/model licenses, download compatible permitted artifacts, and record every file hash before use. Prove Hebrew/English compatibility; unsupported language/native-wheel combinations fail explicitly.
- Results: fresh directories under `E:/Workspace/AI_Stuff/Pdf_Examples/Comparison_Runs`, outside Git.
- Execution: CPU only, serial workers, maximum **8 GiB lifetime peak working set per worker**, **180 seconds per initialization/extraction**, **50 MiB per source**, **200 pages per source**, one cold and three warm passes. This machine reports 63.78 GiB physical RAM; 8 GiB is a proposed experiment ceiling, not a measured Docling requirement.
- Treatments: pypdf and Docling with OCR disabled are approved for preparation/comparison. The originally proposed Hebrew/English EasyOCR treatment is unsupported by EasyOCR 1.7.2 and will not run. Freeze settings and artifact revisions before executing each treatment. No implicit fallback or remote inference.

## Validation and boundaries

Check the package/model license inventory and native imports, prove a synthetic offline parse, test prepared OCR language settings, then execute the real corpus using the frozen source/reference identity. Compare evidence fidelity, tables, labels, RTL, explicit failures, timing and memory. Extraction completion alone is not a quality or adoption decision.

Rejected alternative: installing into the application environment or running cloud OCR/provider services. Rollback removes only newly created experiment directories; existing source PDFs, approved references and baseline artifacts remain intact. If CPython 3.14 support fails, report the concrete failure and request a revised design instead of changing the application interpreter.

No service startup/configuration, database/store indexing, credentials, production ingestion, push or phase closure is included in this preparation approval.

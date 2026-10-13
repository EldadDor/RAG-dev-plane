# Explicit PDF backend revision after native OCR decoder faults

**Task:** RAG-B-OCR
**Prepared:** 2026-10-13
**Status:** Awaiting revised G2 decision; the Tesseract design/setup approval remains valid.

Tesseract's prepared language models recover the synthetic raster fixture exactly:
`Revenue -12.50 USD` and `שלום עולם 123`, including logical Hebrew word order.
One cold/three-warm run passed with stable text and about 1.25 GiB job peak commit.
An earlier run exited during its second warm pass. Windows Application Error
events identify `docling_parse/pdf_parsers.cp314-win_amd64.pyd` with access violation
`0xc0000005`, including repeated events in the later successful worker. The
default PDF decoder is therefore not established as stable for this OCR runtime.
Do not mistake the later successful fixture for a native stability proof.

## Chosen revision

Expose an explicit experiment PDF backend option and configure
`PdfFormatOption(backend=PyPdfiumDocumentBackend)` for both Docling treatments.
The installed/pinned `pypdfium2==5.14.0` and Docling's built-in
`docling.backend.pypdfium2_backend.PyPdfiumDocumentBackend` import successfully.
This is only import evidence, not an inference or quality result. No new Python
dependency or application interpreter change is proposed.

Keep the original decoder selectable and identified in settings; do not retry
or auto-fallback to another backend on failure. Freeze backend name, native
package version, model hashes and normalization policy into processing identity.
Retain the existing native-decoder no-OCR comparison and failed smoke artifacts.

Run PDFium no-OCR and PDFium Tesseract OCR as separate, clearly identified
treatments on the same frozen corpus. Keep both candidate treatments on the
same backend so differences are not incorrectly attributed to OCR alone.
The existing pypdf output is reusable after source/reference and text-identity
verification; it need not be installed into or routed through a new provider.

## Rejected alternatives and rollback

Changing the application's Python 3.14 interpreter would affect unrelated work.
Restarting a converter for every warm pass would hide the observed reuse failure
and invalidate the existing warm-run definition. Running through Bionic/Ollama
would add provider/generative behavior to the parser experiment. These approaches
are rejected for this revision.

No SQL migration, production API/provider configuration or indexing is needed.
Rollback reverts the explicit backend selection and preserves all experiment
results; existing application ingestion and Python runtime remain intact.

## Required validation

- Focused tests for explicit backend selection, identity, unknown-backend
  rejection and no automatic fallback; retain strict provenance/partial results.
- Offline raster and digital-text smoke tests with one cold/three-warm passes,
  original signed number/Hebrew order, native-child cleanup and resource limits.
  Preserve any native failures and their exit codes; imports alone are insufficient.
- Then PDFium no-OCR and PDFium OCR corpus treatments under the existing CPU-only,
  serial, 8192 MiB worker working-set plus job private-commit cap and 180-second
  initialization/extraction deadlines. No budget increase is included.
- Verify unchanged model/native/source/reference hashes, normalized text/offsets,
  page/asset links and cold/warm consistency. Quality/adoption remains a separate
  fact/cell/label/RTL/provenance review against the 47 approved cases.

## Why a new design decision is requested

The approved [Stage A design](../rag_pdf_experiment_design.md) states: “If any
native dependency fails, present a supported-runtime local worker with a
versioned JSON boundary as a revised G2 decision instead of silently switching.”
This revision retains the existing worker/JSON boundary and pinned Python,
explicitly changing only the PDF backend/treatments. The repository's
[G2 rule](../../.codex/AGENTS.md) also covers a public CLI shape change.

**Approval requested:** G2 for explicit PDFium backend selection and its paired
no-OCR/OCR validation and corpus runs. Tesseract installation/download approval
does not need to be repeated.

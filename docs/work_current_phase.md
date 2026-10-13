# Current Backend Work Phase

**Last reviewed:** 2026-10-14
**Phase:** RAG adoption Stages A/B — extraction experiment; source-fidelity acceptance remains unmet.
**Scope:** Offline PDF extraction only. Production ingestion and indexed comparison belong to Stage C.
**Decision:** Keep pypdf as the default; resolve fact/cell/label/RTL gaps and fixed-budget timeouts before treatment selection.
**Approvals:** G1 adoption/proceed and G2 adapter/isolated-runtime design approved 2026-10-10; all submitted worksheets and Tesseract/PDFium revisions explicitly approved 2026-10-13. References require no repeat signoff. Local RAG commits authorized; push/merge and phase closure retain separate gates.

| ID | Task | Status | Gate | Request / evidence |
| --- | --- | --- | --- | --- |
| DOC-PLAN-01 | Index documents in play and define retirement lifecycle | Completed | G1/G3 approved by direct request | User approved and requested commit on 2026-10-14. Delivered in `25c7b6d`: docs/README.md and repository reading rules. 21 index links/whitespace passed; no application tests or service checks. |
| DOC-PLAN-02 | Relocate corpus and shorten planning records | Completed | G1 approved by direct request | User approved proceeding on 2026-10-14. Delivered in `5db1a56`: 229 files relocated, original hashes verified, sources/references/frozen manifest unchanged; 225 unchanged Git blobs verified. Derived manifest passes loader: 17 PDFs/47 cases. 85 navigation links and 19 retirement candidates checked; native staged whitespace check passed after LF normalization of new JSON only. Index/protocol/board updated; docs now has 31 visible live files. No retirement/deletion or closure; no parser treatments, application tests, build or service checks. |
| RAG-A-01 | Corpus/reference protocol and rubric | Completed | G1 approved | `aa2182b`; frozen release `c9878f3`. See [runner protocol](../evaluation/pdf_parsers/README.md). No checks rerun during board condensation. |
| RAG-A-02 | Extraction adapter contracts and tooling | Completed | G2 approved | `db20498`; 37 focused tests previously passed. See [approved design](rag_pdf_experiment_design.md). No application/live checks rerun. |
| RAG-B-PREP | Inspect corpus and prepare worksheets | Completed | G1 approved | `cf3d45d`, `0c2d038`; 17 PDFs/313 pages. Sources and submissions preserved. No parser tests rerun during relocation. |
| RAG-B-REF | Validate cases and freeze references | Completed | Human approval 2026-10-13 | `dc0b7e5`, `c9878f3`; 47 cases, four optional exclusions. [Release evidence](../evaluation/pdf_parsers/corpus/GOLDEN_CASES_VALIDATION.md). No repeat signoff or scoring rerun. |
| RAG-B-BASE | Frozen pypdf baseline | Completed | G1 approved | `c9878f3`; 68 stable cold/warm passes. Scanned-text gaps retained; no quality score inferred. No baseline rerun during relocation. |
| RAG-B-RUNTIME | Isolated Docling runtime and paired no-OCR extraction | Completed | G1 approved 2026-10-13 | `66b4b55`, `9be667d`; 113 pins installed, 132 outputs validated including supplement. [Runtime report](../evaluation/pdf_parsers/corpus/DOCLING_RUNTIME_RESULTS.md). No live indexed validation. |
| RAG-B-OCR | Hebrew/English OCR and PDFium resource controls | Completed | G2 revision approved 2026-10-13 | `1a85278`, `464afe2`; 46 tests, 124 original outputs and eight fix outputs audited. [Comparison and limitations](../evaluation/pdf_parsers/corpus/PDFIUM_COMPARISON.md). No full-case aggregate/CER scoring or application suite. |
| DOC-SWEEP-01 | Archive two selected Q&A notes | Completed | G3 approved by direct request | `9e20325`; original hashes matched, live references absent. No application/build/service checks. |
| REPO-AGENT-01 | Repository routing and session preflight | Completed | G1/G2 authorized by direct request | `9e20325`; JSON/parser/path checks passed. Actual SessionStart event and application tests not run. Original design/rollback evidence retained in `25c7b6d:docs/work_current_phase.md`. |
| RAG-PHASE-SYNC | Reconcile committed phase evidence | Completed | G1 approved by direct request | `9e20325`; history reviewed through `464afe2`, approved ledger hashes corrected. No new closure or application/live checks. |

**Read for this phase:** [corpus entry point](../evaluation/pdf_parsers/corpus/README.md), [comparison](../evaluation/pdf_parsers/corpus/PDFIUM_COMPARISON.md), [approved experiment design](rag_pdf_experiment_design.md). Follow individual evidence links only for the task being worked on.

**Evidence preservation:** Source PDFs, approved worksheets/JSONL and original frozen manifest remain unchanged. Detailed pre-condensation board evidence is preserved in Git at `25c7b6d:docs/work_current_phase.md`; [relocation audit](../evaluation/pdf_parsers/corpus/relocation-validation.json) records move hashes and loader validation. Private models/native runtimes/extraction outputs remain outside Git.

**Outstanding gates/limits:** G3 push/merge and G4 closure are pending. No service operations, SQL/migrations, provider calls, production ingestion or Stage C activation. Historical retirement requires owner selection of the proposed files.

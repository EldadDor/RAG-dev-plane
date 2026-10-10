# Current Backend Work Phase

**Last reviewed:** 2026-10-10
**Status:** RAG-ADOPT-A — Stage A preparation delivered; awaiting G2 adapter design.

**Scope:** Prepare the PDF parser experiment corpus specification, extraction rubric, normalized adapter contract and Windows/Python 3.14 compatibility assessment for Stages A/B of the approved RAG-Anything plan.
**G1 approval:** User reviewed/approved the plan and instructed “commit it, and all changes and proceed” on 2026-10-10. Activate Stage A only.
**Affected layers:** Backend loader/domain design, extraction-only evaluation tooling and shared documentation. Public API and persistence changes belong to later stages.
**Rough validation plan:** Inspect existing loaders/models/ingestion boundaries; verify primary dependency guidance; validate manifest JSON and documentation whitespace. After G2, use synthetic PDFs and fake optional engines to test offsets, page numbering, failures and baseline import isolation offline.

| ID | Task | Status | Gate | Request / evidence |
| --- | --- | --- | --- | --- |
| RAG-A-01 | Prepare corpus/reference protocol and frozen extraction rubric proposal | Completed | G1 approved | Added evaluation/pdf_parsers/README.md and corpus.example.json with categories, manual reference protocol, hashes, private-output policy and acceptance rubric. JSON parsed successfully; whitespace/conflict checks passed. No permitted corpus was found; actual corpus/reference freezing is pending and Stage A is not fully complete. |
| RAG-A-02 | Prepare adapter contract and compatibility decision for extraction-only tooling | Awaiting G2 | G2 Design | Request: approve docs/rag_pdf_experiment_design.md: normalized v1 contract, pypdf/Docling adapters and extraction-only CLI; optional pdf-experiment dependency group after isolated Windows/CPython 3.14 wheel validation. Rejected full RAG-Anything/LightRAG adoption. No SQL/API changes; rollback removes isolated tooling/dependency. Official guidance declares eligibility, not local runtime proof. Prepared protocol and offline tests/limits; package installation, model preparation and real runs remain separate. No runtime code written. |

**Delivered documentation:** `d548a00` commits all previously pending files: architecture flow diagram, adoption plan, task overview and phase board. User explicitly approved local commit (G3) on 2026-10-10. DOC-03 and plan/review tasks are delivered; G4 closure of DOC-03 remains pending, so no completed-phase closure was written. Staged whitespace check caught three Markdown hard-break lines in the new plan; corrected during Stage A preparation. Application tests and Mermaid rendering were not run. No push, installation, model download, service or migration operation occurred.

**Preparation validation:** PowerShell ConvertFrom-Json parsed the manifest template; git diff --check and explicit new-file whitespace/conflict scans passed. Source and official Docling metadata/guidance inspected. Interpreter script execution is unavailable in the sandbox despite version reporting; no application tests, dependency resolution/install, model downloads, parser/model runs, live services, SQL, migrations or push ran. Files: design, evaluation protocol/template, plan whitespace, current/next boards and task overview. Stage A preparation commit follows d548a00; see Git log for its hash.

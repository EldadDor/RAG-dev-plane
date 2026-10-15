# Frozen PDF benchmark

**State:** Reproducibility inputs and retained evidence; read only for PDF experiment tasks.
**Release:** 17 PDFs / 47 approved cases. Human approval and source/reference bytes are unchanged.

Use [corpus.relocated.json](corpus.relocated.json) with the existing comparison runner
in this checkout. [corpus.frozen.json](corpus.frozen.json) is the byte-preserved
2026-10-13 snapshot and retains its historical absolute paths. It is evidence,
not the runnable manifest at this location. The derived manifest changes only
locations and adds relocation provenance; the question set needs no new approval.

| Need | Entry point |
| --- | --- |
| Isolated indexed comparison | [Stage C results](STAGE_C_RESULTS.md), [machine summary](STAGE_C_SUMMARY.json) |
| Current result and remaining fidelity work | [Normalization fidelity follow-up](NORMALIZATION_FIDELITY_REVIEW.md), [original case review](EXTRACTION_SCORECARD.md), [PDFium execution](PDFIUM_COMPARISON.md) |
| Approved reference release | [Case validation](GOLDEN_CASES_VALIDATION.md), [approval](HUMAN_APPROVAL.md) |
| Parser commands and budgets | [Runner protocol](../README.md) |
| Move verification and original/derived hashes | [Relocation audit](relocation-validation.json) |
| Completed historical cleanup | [Retirement record](RETIREMENT_PROPOSAL.md), [archive audit](retirement-validation.json) |

`PDFs/`, `golden-cases/` and `worksheets-done/` hold sources, scored references
and approved submissions. Read only the document/case needed for the task.
Earlier runtime failures, approved designs and `reference-review-2026-10-11/`
remain retained provenance. They are not routine onboarding or active plans.
Historical reports/commands may show the old `docs/Comparison_Preparation` paths.
Use the derived manifest above for current commands.

The 229 original files were hashed before and after the move. Navigation edits
affect START_HERE, two design/preparation documents and Git attributes; the audit
records each original/current hash at relocation. The later retirement audit
locates the 19 archived drafts/templates; START_HERE subsequently received navigation edits.
The original frozen manifest, all PDFs,
references, worksheets and machine evidence remain byte-identical.

On another checkout, regenerate location fields from the original snapshot rather
than editing its frozen bytes. Point source_path to this folder's PDFs, references_path
to golden-cases, and human_approval_path to HUMAN_APPROVAL.md; preserve all other
fields and source/reference hashes. Validate the derived manifest with the existing
load_manifest function before parsing. The checked-in derived file uses this machine's
absolute paths, as required by the current runner.

Do not externalize/delete source PDFs or previews during ordinary development.
Any later external storage decision needs an explicit destination, restoration
procedure, hash verification and owner approval. Extraction outputs remain outside Git.

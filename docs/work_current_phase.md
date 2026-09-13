# Current Work Phase — NP-16 Hebrew and Multilingual RAG Evaluation

**Status:** Complete — closed 2026-09-13
**Activated:** 2026-09-13
**Owner:** Project team
**Prerequisite:** NP-13 through NP-15 completed and live-validated on 2026-09-12

## Objective

Measure Hebrew extraction, retrieval, and answer quality separately against a
human-authored local golden set before changing a model, vector dimension, or
deployment provider.

## Guardrails

- The historical `nomic-embed-text` / `llama3.2:3b` baseline remains intact.
- `bge-m3` and DictaLM experiments use separate profile storage.
- Treat image text as out of scope; Hebrew text embedded in screenshots still
  requires a separately approved OCR or visual-understanding phase.

## Baseline Evidence

The committed 13-case Hebrew set and
`evaluation/results/baseline-hebrew-default.json` establish the current local
baseline:

| Measure | Result |
| --- | ---: |
| Retrieval determinism | 13/13 cases |
| Source-hint recall | 46.2% |
| Context precision | 40.0% |
| Source MRR | 40.0% |
| Answer relevance proxy | 1.2% |
| Faithfulness proxy | 1.6% |
| Median two-request case latency | 4.42 s |

The five `israel-vehicle-importers.pdf` cases retrieved their expected source;
the operational Hebrew Word cases mostly did not. This is a retrieval finding,
not evidence that a chat-model swap alone will solve the problem.

The approved `bge-m3:latest` profile was warmed into a separate
`rag.document_chunks_bge_m3` table at 1024 dimensions, leaving the default
table untouched. Its 13-case artifact, `evaluation/results/bge-m3-hebrew.json`,
measured 100.0% source precision, source-hint recall, and MRR; median paired
case latency was 7.06 s. The default profile remains the rollback target.

With that same retrieval profile, `dictalm2.0-instruct` completed all 13 cases
without a generation failure. Its artifact,
`evaluation/results/bge-m3-dictalm2-hebrew.json`, measured 47.1% answer
relevance and 56.0% faithfulness, versus 2.8% and 16.3% for `llama3.2:3b`.
The median paired-case latency increased to 14.13 s.

The existing 19-case English set was also re-run with bge-m3 and DictaLM.
`evaluation/results/bge-m3-dictalm2-english.json` recorded 100.0% source-hint
recall and MRR, 96.8% source precision, 64.3% answer relevance, 53.3%
faithfulness, no generation failures, and 14.19 s median paired-case latency.
The older English baseline uses a different chat-model configuration, so its
answer metrics are contextual rather than an embedding-only A/B comparison.

## Task Board

| ID | Task | Status |
| --- | --- | --- |
| NP16-01 | Validate the UTF-8 Hebrew golden set and run the immutable default-profile baseline. | Complete: 13 valid cases and baseline artifact recorded. |
| NP16-02 | Add rank-aware source metrics so comparison reports include MRR as well as source precision/recall. | Complete: `source_mrr` is included in every benchmark result. |
| NP16-03 | Add a Hebrew `.docx` extraction regression fixture/test. | Complete: Hebrew text and mixed punctuation are preserved by `WordLoader`. |
| NP16-04 | Document the baseline diagnosis and a reproducible local comparison command. | Complete: default baseline artifact refreshed 2026-09-13. |
| NP16-05 | Compare a multilingual embedding profile (`bge-m3`) against the baseline. | Complete: the isolated 1024-dimension profile reached 100.0% source precision, recall, and MRR. |
| NP16-06 | Compare Hebrew-capable local chat models only after the best embedding profile is known. | Complete: `dictalm2.0-instruct` with bge-m3 completed all 13 cases with no generation failures. |

## Completion Criteria

- Golden cases are valid UTF-8, duplicate-free, and cover representative Hebrew
  Word/PDF material.
- Reports record source Recall@k, MRR, determinism, latency, answer coverage,
  and the deterministic faithfulness proxy.
- The default baseline is preserved as an immutable comparison artifact.
- Any candidate model experiment is isolated from the default index and has an
  evidence-backed rollback path.

## Outcome and Handoff

NP-16 is closed. The recommended local operational pairing is bge-m3 retrieval
with DictaLM chat; preserve the original profile as a rollback/reference. NP-17
continues with application-level model-profile resolution, cache adapters, and
an Azure-ready profile configuration.

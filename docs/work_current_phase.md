# Current Work Phase — NP-16 Hebrew and Multilingual RAG Evaluation

**Status:** Active — Phase A: baseline evidence and evaluation hardening
**Activated:** 2026-09-13
**Owner:** Project team
**Prerequisite:** NP-13 through NP-15 completed and live-validated on 2026-09-12

## Objective

Measure Hebrew extraction, retrieval, and answer quality separately against a
human-authored local golden set before changing a model, vector dimension, or
deployment provider.

## Guardrails

- Keep the active `nomic-embed-text` / `llama3.2:3b` profile unchanged.
- Do not download a new model, alter `PG_VECTOR_DIM`, create a new vector
  table, or send workplace documents to Azure during Phase A.
- Keep the existing default index and chat contract intact.
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

## Task Board

| ID | Task | Status |
| --- | --- | --- |
| NP16-01 | Validate the UTF-8 Hebrew golden set and run the immutable default-profile baseline. | Complete: 13 valid cases and baseline artifact recorded. |
| NP16-02 | Add rank-aware source metrics so comparison reports include MRR as well as source precision/recall. | Complete: `source_mrr` is included in every benchmark result. |
| NP16-03 | Add a Hebrew `.docx` extraction regression fixture/test. | Complete: Hebrew text and mixed punctuation are preserved by `WordLoader`. |
| NP16-04 | Document the baseline diagnosis and a reproducible local comparison command. | Complete: default baseline artifact refreshed 2026-09-13. |
| NP16-05 | Compare a multilingual embedding profile (`bge-m3`) against the baseline. | Complete: the isolated 1024-dimension profile reached 100.0% source precision, recall, and MRR. |
| NP16-06 | Compare Hebrew-capable local chat models only after the best embedding profile is known. | Blocked pending NP16-05 evidence and approval of the chosen download. |

## Completion Criteria

- Golden cases are valid UTF-8, duplicate-free, and cover representative Hebrew
  Word/PDF material.
- Reports record source Recall@k, MRR, determinism, latency, answer coverage,
  and the deterministic faithfulness proxy.
- The default baseline is preserved as an immutable comparison artifact.
- Any candidate model experiment is isolated from the default index and has an
  evidence-backed rollback path.

## Decision Gate for Phase B

Before comparing `bge-m3`, approve NP-17's additive registry/cache migration,
profile-specific 1024-dimension storage, and the model download. That approval
will permit a non-destructive re-embedding experiment while preserving the
current 768-dimension default profile.

# Current Work Phase — NP-10 Activate Retrieval Reranking

**Status:** Active
**Activated:** 2026-09-09
**Last reviewed:** 2026-09-09
**Owner:** Project team
**Roadmap:** [`extended_plan.md`](extended_plan.md)
**Baseline:** [`../evaluation/results/baseline-default-expanded.json`](../evaluation/results/baseline-default-expanded.json)

## Objective

Improve the precision of the context sent to the answer model by reranking a
wider hybrid-retrieval candidate set, while retaining recall and the existing
local/on-premises operating path.

## Scope and Guardrails

- Turn the existing `RERANK_ENABLED` setting into an actual retrieval stage
  behind an adapter boundary.
- Fetch a wider candidate set, rerank it, and retain a configurable final
  top-k result set for chat and retrieval callers.
- Provide a local cross-encoder implementation or an explicit safe fallback
  when that optional dependency is unavailable.
- Preserve workspace and chunking-profile filters, source attribution, score
  ordering, error envelopes, and the current behavior when reranking is off.
- Do not modify document chunks, embeddings, provider selection, prompts, or
  database schema in this phase.
- Keep model downloads/initialization opt-in and never mandatory for the
  offline test suite.

## Task Board

| ID | Task | Status |
| --- | --- | --- |
| CW-01 | Map the existing retrieval/configuration boundary and document the chosen reranker interface. | Complete 2026-09-09: reranking belongs after profile/workspace-scoped hybrid fusion. |
| CW-02 | Add configuration for candidate width, final top-k, and the local reranker adapter/fallback. | Complete 2026-09-09: optional lazy `sentence-transformers` adapter uses `RERANK_*`; existing `TOP_K` remains final result count. |
| CW-03 | Implement reranking after hybrid fusion while preserving profile/workspace isolation and disabled-mode behavior. | Complete 2026-09-09: enabled mode reranks fused candidates; unavailable adapter safely preserves fused order. |
| CW-04 | Add focused unit and API tests for ordering, fallback, configuration, and isolation. | Complete 2026-09-09: ordering, wider candidates, disabled mode, and unavailable-adapter fallback are covered; `61 passed, 1 skipped`. |
| CW-05 | Run offline validation and an approved live A/B benchmark against the NP-09 19-case baseline. | Active: implementation validation is complete; live comparison is next. |
| CW-06 | Decide whether reranking should be enabled by default; record the evidence and close or revise the phase. | Queued |

## Acceptance Checks

- With `RERANK_ENABLED=false`, retrieval is behaviorally unchanged.
- With reranking enabled, candidates are retrieved wider, reranked, and
  trimmed to the final top-k without crossing workspace or profile boundaries.
- The offline suite covers deterministic ordering and a dependency/model-free
  fallback path.
- The local reranker path is configurable and does not download a model during
  ordinary imports or tests.
- On the 19-case NP-09 set, context precision improves at equal-or-better
  recall. Any answer-length change is reported, not assumed.
- The A/B artifact records both configurations and any failure stage.

## Handoff Constraint

Do not enable reranking by default until the live A/B result is reviewed. No
frontend work or destructive index/database operation is required.

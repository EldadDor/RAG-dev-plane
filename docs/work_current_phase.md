# Current Work Phase — NP-17 Embedding Model Profiles and Cache

**Status:** Complete — closed 2026-09-13
**Activated:** 2026-09-13
**Owner:** Project team
**Prerequisite:** NP-16 evaluation completed with bge-m3 retrieval and DictaLM chat.

## Objective

Make embedding-model selection a profile change rather than a re-parsing or
destructive vector-dimension migration. Keep the historical `default` profile
intact while allowing locally warmed or future Azure profiles to coexist.

## Delivered

- Migration 005 provides the `rag.model_profiles` registry and persistent
  `rag.embedding_cache`; profile storage remains provisioned through reviewed
  SQL rather than application DDL.
- Profile-aware ingestion, retrieval, and chat select model dimensions,
  prefixes, storage tables, and cache keys together. Omitted API fields still
  resolve through `MODEL_PROFILE`.
- The active local bge-m3 profile uses its isolated 1024-dimension table;
  the 768-dimension nomic default remains a rollback/reference path.
- The local operator warmer copies one authorized workspace's chunk text and
  provenance into a target profile without re-chunking. Its dry-run response
  reports chunks, cached embeddings, and estimated provider calls.
- The warmer is deliberately unavailable outside `APP_ENV=local`. A gateway
  deployment requires a separately approved operator-authorization design.

## Task Board

| ID | Task | Status |
| --- | --- | --- |
| NP17-01 | Registry/cache migration and profile-table provisioning. | Complete. |
| NP17-02 | Typed profile and cache stores. | Complete. |
| NP17-03 | Prefix-aware cached embedding client with dimension validation. | Complete. |
| NP17-04 | Profile resolution through ingestion, retrieval, and chat. | Complete and live-validated. |
| NP17-05 | Workspace-scoped warmer and dry-run API. | Complete; batched cache inspection and API/unit coverage added. |
| NP17-06 | bge-m3 live warm and multilingual benchmark validation. | Complete: 1,150 chunks warmed; Hebrew and English artifacts recorded. |

## Validation and Outcome

- Full test suite: **86 passed, 1 skipped** (2026-09-13).
- bge-m3 delivered 100% Hebrew source precision, recall, and MRR on the
  13-case golden set. DictaLM completed all Hebrew cases without generation
  failure and materially improved answer relevance/faithfulness over the
  original chat baseline.
- The recommended local pairing is bge-m3 retrieval with DictaLM chat. Keep
  `default`/nomic storage for rollback and comparison.

## Handoff

NP-17 is closed. Future work should select the next explicitly approved item
from `next_phase.md`; Azure exposure of the warmer is intentionally not part of
this phase.

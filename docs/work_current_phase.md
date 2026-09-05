# Current Work Phase — NP-08 Non-Destructive Chunking Experimentation Lab

**Status:** Active
**Activated:** 2026-09-04
**Last reviewed:** 2026-09-05
**Owner:** Project team
**Roadmap:** [`extended_plan.md`](extended_plan.md)

## Objective

Make chunking strategies safe to change, ingest, and compare side by side
without overwriting the existing pgvector index. The default profile must
continue to behave exactly as it does today unless a caller explicitly selects
another profile.

## Approved Resolution

Treat `chunking_profile` as an index-data dimension, not merely a runtime
setting. Sources and chunks belonging to an experiment are isolated from the
default profile, and a future promotion changes the workspace's selected
profile rather than replacing the default rows during experimentation.

## Scope and Guardrails

- Add `chunking_profile` to persisted source-document and chunk records with
  versioned migration `003_chunking_profiles.sql`.
- Backfill or default existing records to the profile that preserves current
  chunk-size and overlap behavior.
- Extend `POST /ingest` with optional `chunking_profile` and `dry_run` inputs.
  A dry run reports chunk statistics and must not write or replace index data.
- Register profile-defined recursive-character chunking behind the current
  chunker boundary. A semantic splitter may be added only as an optional
  comparison strategy.
- Allow retrieval and chat to select a profile, while omission selects the
  existing default behavior.
- Preserve workspace authorization, provider boundaries, conversation memory,
  and the current default ingestion/retrieval/chat contracts.
- Do not delete, rebuild, or mutate default-profile rows as part of an
  experiment. Do not deploy infrastructure, change embedding models, activate
  reranking, or apply NP-07 prompt/context changes in this phase.
- Do not run Uvicorn, models, pgvector, Langfuse, or office services without
  announcing it first.

## Task Board

| ID | Task | Status |
| --- | --- | --- |
| CW-01 | Map current source/chunk persistence, IDs, replacement lifecycle, and retrieval filters; record the migration and rollback design. | Complete 2026-09-05: profile is now part of source identity and chunk metadata; default retains legacy IDs. |
| CW-02 | Define the profile model, default-profile name, request/response schema changes, and profile-selection authorization boundaries. | Complete 2026-09-05: configured named profiles, `default` fallback, and validated optional request fields. |
| CW-03 | Implement and validate migration `003_chunking_profiles.sql`, including preservation of existing rows. | Complete 2026-09-05: applied to PostgreSQL; 55 source documents and 433 chunks preserved as `default`. |
| CW-04 | Implement profile-aware ingestion, source lifecycle, and `dry_run` statistics with no writes. | Complete 2026-09-05: dry runs skip hash checks, embeddings, replacement, and stale-row deletion. |
| CW-05 | Register recursive-character profiles and any approved optional semantic strategy behind the chunker boundary. | Complete 2026-09-05: profiles use the existing recursive-character and optional semantic adapters. |
| CW-06 | Add profile filters to retrieval and chat without changing unspecified-request behavior. | Complete 2026-09-05: semantic and lexical paths both filter by resolved profile. |
| CW-07 | Add focused unit/API tests, run the approved validation lanes, update contracts and handoff records, then prepare closure. | In progress: isolated suite passes and PostgreSQL migration/backfill validation is complete; a live experiment ingestion/query remains. |

## Acceptance Checks

- Re-ingesting the same sources under an experiment profile leaves default
  profile source and chunk rows unchanged.
- A workspace-scoped retrieval or chat request filtered to an experiment
  profile returns only that profile's chunks.
- `dry_run` returns deterministic useful statistics and makes no persistent
  changes.
- Ingestion, retrieval, and chat behavior remain unchanged when no profile is
  specified.
- The migration has a documented rollback path that does not discard indexed
  data.

## Approval Gates

- NP-08 is approved active as recorded in [`extended_plan.md`](extended_plan.md).
- Review the data model, default-profile naming, API shapes, and migration
  rollback before implementation of CW-03.
- Obtain explicit approval before adding a semantic-splitter dependency or
  making live model/database validation mandatory.
- Record externally visible API contract changes in
  [`frontend_architecture.md`](frontend_architecture.md) and the backend-to-
  frontend handoff before implementation is presented for frontend use.

## Validation Plan

- Unit-test profile selection, chunk generation, dry-run non-mutation, and
  preservation of the default profile.
- API-test request validation and profile-filtered ingestion, retrieval, and
  chat with mocked dependencies.
- Run a local PostgreSQL migration and lifecycle validation only after the
  migration review gate; preserve the existing index before that check.
- NP-09 will provide the cross-profile quality benchmark. NP-08 verifies
  isolation and reversibility rather than declaring a strategy superior.

## Handoff Constraint

No frontend work is required until the optional profile fields and their
response semantics are finalized. Existing frontend requests must continue to
work unchanged when no profile is sent.

## Completion Record

Pending. On completion, add a validated, committed NP-08 entry to
[`complete_phases.md`](complete_phases.md), update the backlog, and publish
any contract changes through the shared handoff.

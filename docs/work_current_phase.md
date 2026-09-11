# Current Work Phase — NP-13 through NP-15 Word Documents and Images

**Status:** Implementation and PostgreSQL migration complete; live Word/image browser validation pending
**Approved:** 2026-09-11
**Last reviewed:** 2026-09-11
**Owner:** Project team
**Plan:** [`document_image_support_plan.md`](document_image_support_plan.md)

## Objective

Ingest modern Microsoft Word `.docx` files as structured searchable text,
preserve embedded image bytes under the existing workspace/profile lifecycle,
and show authorized related images with grounded chat citations.

## Guardrails

- No legacy `.doc`, Office automation, OCR, visual embeddings or multimodal
  model calls.
- Original image bytes remain outside pgvector and outside prompts.
- Browsers receive only application-issued, workspace-authorized asset URLs.
- Existing text-only loaders, citations and SSE event order remain compatible.
- Migration 004 is additive and does not alter existing chunks or embeddings.

## Task Board

| ID | Task | Status |
| --- | --- | --- |
| NP13-01 | Add safe `.docx` loader and dependency. | Complete: `python-docx` plus bounded ZIP/OOXML validation. |
| NP13-02 | Preserve ordered Word structure and stable image anchors. | Complete: headings, paragraphs, lists, tables, page breaks, block offsets, captions and image relationships. |
| NP13-03 | Make source hashing image-aware. | Complete: loader-supplied package hash detects image-only changes. |
| NP14-01 | Add binary asset-store boundary and limits. | Complete: content-addressed local/in-memory adapters, safe keys and bounded extraction settings. |
| NP14-02 | Add profile-scoped metadata and chunk associations. | Complete; `004_document_assets.sql` was applied and verified on 2026-09-11. |
| NP14-03 | Integrate asset replacement, cleanup and retrieval metadata. | Complete offline for PostgreSQL and Qdrant paths. |
| NP15-01 | Add authorized asset delivery. | Complete: membership check, media allowlist, private caching, ETag and `nosniff`. |
| NP15-02 | Extend citation/SSE contract compatibly. | Complete: optional image asset metadata; old payloads map to an empty array. |
| NP15-03 | Render cited images in chat. | Complete: lazy previews in Sources and a deduplicated related-images section. |
| NP15-04 | Run offline validation. | Complete: 74 backend tests, 7 frontend tests, TypeScript and production build pass. |
| NP15-05 | Apply migration and run live `.docx` ingestion/chat/browser validation. | Blocked 2026-09-11: configured PostgreSQL `10.100.102.12:5432` timed out; no database changes were made. |

## Acceptance State

- Safe deterministic Word parsing: passed with synthetic fixtures.
- Image-only change detection: passed.
- Original byte round-trip, storage-key safety and pruning: passed.
- Chunk association, dry-run no-write behavior and limits: passed.
- Workspace authorization, safe headers, unsupported-media behavior and ETag:
  passed through in-process API tests.
- Frontend backward compatibility, asset mapping, type checking and build:
  passed.
- Real PostgreSQL migration, real Word ingestion and browser image rendering:
  pending environment availability.

## Validation Commands

```powershell
.\.venv\Scripts\python.exe -m pytest tests\ --ignore=tests\integration -q
node node_modules\vitest\vitest.mjs run
node node_modules\typescript\bin\tsc -b
node node_modules\vite\bin\vite.js build
```

## Next Operator Step

Bring the configured PostgreSQL service online, apply
`database/migrations/004_document_assets.sql`, restart the API, ingest a safe
review fixture or approved real `.docx`, and validate that a grounded answer
shows its related screenshot in the frontend. Do not close the phase until
this live path passes.

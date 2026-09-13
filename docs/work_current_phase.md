# Current Work Phase — NP-13 through NP-15 Word Documents and Images

**Status:** Complete
**Approved:** 2026-09-11
**Last reviewed:** 2026-09-12
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
| NP15-04 | Run offline validation. | Complete: 76 backend tests, 7 frontend tests, TypeScript and production build pass. |
| NP15-05 | Apply migration and run live `.docx` ingestion/chat/browser validation. | Complete 2026-09-12: PostgreSQL migration 004 verified; `general_errors_handling.docx` retrieved an asset-linked chunk, and its embedded screenshot rendered in the local browser. |

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
  passed on 2026-09-12. A targeted Hebrew query returned `10MB` and rendered
  an associated `image/png` asset in the related-source-images panel.

## Validation Commands

```powershell
.\.venv\Scripts\python.exe -m pytest tests\ --ignore=tests\integration -q
node node_modules\vitest\vitest.mjs run
node node_modules\typescript\bin\tsc -b
node node_modules\vite\bin\vite.js build
```

## Completion Record

NP-13 through NP-15 closed on 2026-09-12. The next proposed backend work is
NP-16 Hebrew and multilingual evaluation; it remains unapproved for
implementation.

# Word Documents and Embedded Images — Review Proposal

**Status:** Approved 2026-09-11; implementation and PostgreSQL migration complete, live browser validation pending
**Prepared:** 2026-09-10
**Proposed phases:** NP-13, NP-14, NP-15

## Goal

Ingest modern Microsoft Word documents (`.docx`) as structured text and make
their embedded images available from grounded chat citations. The initial
image scope is preservation and display, not OCR, caption generation, visual
embedding, or multimodal question answering.

The user-facing target is: when a retrieved Word passage has an associated
embedded screenshot, the chat UI can show that image alongside its source.

## Recommended Boundary

```text
.docx ZIP package
  ├─ paragraphs, headings, lists and tables ──> text chunks ──> embeddings
  └─ embedded image bytes + Word relationships ──> asset store
                                                   │
text chunk <──────────── stable chunk/asset link ──┘
   │
retrieval result ──> citation with related asset metadata
                         │
                         └─> authorized asset endpoint ──> chat image preview
```

- Only extracted text is embedded in the initial release.
- Image bytes are never inserted into pgvector or embedded into prompts.
- Images are returned only when associated with a retrieved/cited text chunk.
- The model does not invent image URLs. The API supplies structured asset
  references and the frontend renders them.
- A screenshot with no nearby searchable text can be preserved and displayed,
  but questions about its visual contents cannot be answered until a later OCR
  or multimodal phase is approved.

## Parser Recommendation

Use `python-docx` for supported Word semantics and targeted read-only OOXML
inspection (`zipfile` plus the existing `lxml` dependency) for relationship and
image-anchor details that the high-level library does not expose reliably.
This keeps the implementation in-process and cross-platform. Do not depend on
Microsoft Word COM automation, desktop Office, LibreOffice conversion, or a
large general document-AI framework for the first phase.

The loader should treat the `.docx` as an untrusted ZIP/XML package: apply
entry-count and expanded-size limits before parsing, reject traversal paths,
disable external entity/network resolution, and never fetch external Word
relationships.

## Scope Decisions Proposed for Approval

1. Support `.docx`, not legacy binary `.doc`. Legacy files must be converted
   with Word/LibreOffice before ingestion; server-side Office automation is out
   of scope.
2. Extract paragraphs, headings, lists, tables, hyperlinks, page-break hints,
   captions/alt text, and image anchors in document order.
3. Keep original embedded image bytes. Initially serve browser-safe PNG, JPEG,
   GIF and WebP. Preserve but do not inline unsupported formats until a preview
   conversion phase is approved.
4. Store asset metadata and chunk associations in PostgreSQL. Store binary
   bytes behind an `AssetStore` interface: local filesystem for local use and
   Azure Blob-compatible storage for the later office deployment.
5. Scope every asset by workspace, chunking profile and document. Document
   replacement and directory reconciliation must remove obsolete associations
   and unreferenced blobs.
6. Show images in the Sources area and a related-images section for the cited
   assistant response. Do not embed model-authored Markdown image links in the
   answer stream.
7. Asset content is delivered through an authenticated/authorized API route,
   never through `file://`, an absolute server path, or a publicly exposed
   storage directory.

## NP-13 — Structured Microsoft Word Ingestion

**Objective:** Make `.docx` a first-class text source while retaining Word
structure needed for later image association.

### Tasks

- Add an optional Word parsing dependency and a `WordLoader` registered for
  `.docx`.
- Add `word` to `SourceType` and directory discovery.
- Parse the OOXML package without executing macros or external relationships.
- Extract ordered paragraphs, headings, lists and tables. Preserve title,
  section/heading ancestry, table position, block ordinal and page-break hints
  where Word provides them.
- Produce stable source text offsets/block identifiers so downstream chunks
  can be related to embedded-image anchors.
- Include relevant Word package parts in the document content hash so an image
  replacement is detected even when visible text is unchanged.
- Define explicit behavior for encrypted, corrupt, macro-enabled, oversized
  and unsupported legacy documents.
- Add loader, directory-discovery, chunking, hash and malformed-file tests.

### Acceptance

- A `.docx` fixture containing headings, paragraphs, lists and a table ingests
  into searchable chunks in the correct reading order.
- Re-ingestion is deterministic and unchanged Word files are skipped.
- Changing only an embedded image invalidates the document hash.
- Existing loaders and default-profile behavior are unchanged.
- `.doc`, encrypted and corrupt files fail with a safe, specific reason.

### Explicit exclusions

- Image persistence or browser delivery.
- Word comments, tracked-change review UI, embedded OLE objects and macros.
- Pixel-based page-layout reconstruction.

## NP-14 — Embedded Image Asset Lifecycle

**Objective:** Extract and retain Word images, relate them deterministically to
text chunks, and keep their lifecycle consistent with document replacement.

### Tasks

- Extend the loader result with structured asset descriptors: original bytes,
  relationship ID, media type, original name, ordinal, dimensions when safely
  available, alt text/caption, anchor block and content hash.
- Introduce an `AssetStore` adapter with local-filesystem and test in-memory
  implementations. Reserve an Azure Blob implementation for NP-12 deployment.
- Add migration `004_document_assets.sql` for profile-scoped asset metadata and
  chunk-to-asset associations. Do not add binary columns to the vector table.
- Use deterministic asset IDs and content-addressed storage keys. Never expose
  those storage keys as user-facing URLs.
- Associate an inline/floating image with its containing block or the nearest
  meaningful text block, then map it to the chunk covering that block's source
  offsets. Preserve document and display order.
- Carry related asset IDs through `Chunk`, `IngestedChunk` and
  `RetrievedChunk` metadata for PostgreSQL and Qdrant parity.
- Make document replacement atomic from the application's perspective: do not
  publish new metadata until text chunks and assets are ready; clean obsolete
  links transactionally. Expose unreferenced-blob pruning as an explicit
  maintenance operation rather than racing concurrent ingestion workers.
- Ensure `dry_run` reports image counts/types/bytes but writes no files, rows or
  embeddings.
- Add lifecycle, profile/workspace isolation, deduplication, cleanup, dry-run,
  size-limit and malicious-package tests.

### Proposed metadata shape

```text
document_assets
  workspace_id, chunking_profile, doc_id, asset_id
  content_hash, storage_key, media_type, byte_size
  original_name, relationship_id, ordinal
  width, height, alt_text, caption, anchor_block_id

chunk_assets
  workspace_id, chunking_profile, chunk_id, asset_id, display_order
```

The exact DDL remains subject to implementation review. The primary ownership
key must include workspace and chunking profile to prevent cross-profile drift
when the same source is ingested under different profiles at different times.

### Acceptance

- Original PNG/JPEG bytes round-trip without modification.
- A text-only edit, image-only edit, removal and directory reconciliation leave
  no stale chunk/asset associations.
- Default and experiment profiles cannot see each other's asset metadata.
- Identical blobs may share storage bytes but never bypass workspace access.
- PostgreSQL and Qdrant retrieval return equivalent related-asset metadata.

### Explicit exclusions

- OCR, image descriptions, visual embeddings and multimodal model calls.
- Public URLs and direct filesystem access from the browser.
- Image editing, compression or format conversion.

## NP-15 — Authorized Image Citations and Chat Display

**Objective:** Deliver cited Word images safely and render them in chat without
changing grounded-answer semantics.

### Proposed contract

Extend each `SourceReference` with an optional `assets` array:

```json
{
  "asset_id": "stable-id",
  "media_type": "image/png",
  "width": 1280,
  "height": 720,
  "alt_text": "Deployment settings screenshot",
  "caption": null,
  "content_url": "/workspaces/local/assets/stable-id"
}
```

Add `GET /workspaces/{workspace_id}/assets/{asset_id}`. The route must:

- authenticate the principal and authorize workspace membership before lookup;
- return `404 resource_not_found` for a missing or inaccessible asset where
  disclosure would be unsafe;
- stream bytes with a server-controlled allowlisted `Content-Type`,
  `X-Content-Type-Options: nosniff`, safe content disposition and bounded cache
  policy;
- support conditional requests; byte ranges are optional unless large-image
  evidence shows they are needed;
- never accept a storage path from the caller.

The SSE event sequence remains unchanged. Asset metadata travels inside the
existing terminal `meta.sources` payload.

### Frontend tasks

- Extend the typed source contract and strict SSE validation for `assets`.
- Render related images under their citation in the Sources pane, using lazy
  thumbnails and an explicit open/full-size action.
- Provide captions/alt text when available and a neutral fallback label such
  as “Image from <document>” when unavailable.
- Preserve source title/path/snippet and grounded state; an image is supporting
  source material, not proof that the model interpreted its pixels.
- Handle loading, broken/unsupported image, authorization loss and keyboard
  interaction accessibly.
- Avoid prefetching every image in a document; fetch only images in the active
  answer's citations.

### Acceptance

- A cited screenshot from an ingested `.docx` appears in the chat Sources pane
  and opens at readable size.
- An unauthorized user cannot fetch an asset by guessing its ID.
- Switching workspace/session or starting a new answer cannot leak stale image
  references.
- Text-only citations and old SSE payloads without `assets` still render.
- Browser tests cover success, missing asset, unsupported type and authorization
  loss; live validation covers a real `.docx` with screenshots.

### Explicit exclusions

- Letting the answer model choose image placement.
- Rendering active content (SVG/HTML) inline.
- An ingestion/admin UI.

## Deferred Candidate — Visual Understanding

After NP-13 through NP-15 are measured, a separate approval can consider OCR,
locally generated descriptions, multimodal embeddings or multimodal answer
generation. That phase needs its own privacy, accuracy, latency and model
evaluation. It is not required to preserve and display screenshots linked to
retrieved Word text.

## Validation Fixtures

Create synthetic, redistributable fixtures rather than committing office
documents or screenshots containing internal data:

- text-only `.docx` with headings, list and table;
- `.docx` with one inline PNG and one floating JPEG near distinct sections;
- same visible text with one image byte changed;
- duplicate image used twice;
- unsupported image type, oversized image, external relationship, corrupt ZIP,
  encrypted document and renamed non-DOCX file;
- two workspaces and two chunking profiles containing similarly named assets.

## Data, Security and Rollback

- NP-13 requires no database migration. NP-14 introduces migration 004 and a
  configured asset-storage root/container.
- Extract ZIP entries with decompression-count and uncompressed-size limits;
  reject path traversal and external relationship fetching.
- Validate media bytes independently of OOXML filenames/extensions. Do not
  execute macros, OLE payloads or linked remote content.
- Rollback disables Word/image ingestion and asset serving, then removes asset
  rows and the explicitly configured asset container after backup/review.
  Existing text chunks and migrations remain usable.
- Production storage must use private access and application-mediated
  authorization. Signed object-store URLs, if later used, must be short-lived
  and created only after the same workspace check.

## Approval Record

The user approved NP-13 through NP-15 on 2026-09-11. The implementation uses
the proposed `.docx`-only, preservation-first, private local asset store and
authorized citation-display design. Migration 004 was applied and verified on
2026-09-11; live Word/image chat validation remains pending.

## Approval Gates

Before implementation, approve or revise:

1. `.docx` only versus a required `.doc` conversion workflow.
2. Local filesystem adapter plus future Azure Blob adapter.
3. Images in Sources/related-images UI rather than inside model-authored answer
   Markdown.
4. Preservation-only image scope, with OCR/visual understanding deferred.
5. Migration 004 and the workspace/profile/document ownership model.
6. Maximum Word package size, per-image size, image count and total extracted
   bytes (proposed defaults: 50 MiB package, 15 MiB/image, 100 images,
   100 MiB extracted image bytes/document).

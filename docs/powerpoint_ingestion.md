# PowerPoint ingestion — NP-21

Implemented 2026-10-02. `.pptx` uses the existing `/ingest` API, directory
discovery, chunking/model profiles, hashing, atomic document publication,
workspace filtering, asset authorization and citation flow.

## Extracted content

| Slide content | Handling |
| --- | --- |
| Titles, text boxes, placeholders and grouped shapes | Unicode text in slide order; recursively traverse groups in stored shape order. Preserve paragraph breaks and nesting. This is deterministic shape order, not a reconstruction of visual reading order. |
| Tables | Text rows rendered as Markdown; merged-cell continuations are blank. |
| Charts | Read title, series labels and cached category/value data, including XY/bubble coordinates and hierarchical labels. Missing points remain unavailable. Read no linked workbook or remote data source; caches may reflect the deck's last saved values. |
| Pictures, image fills and available embedded-object previews | Preserve original image bytes in the existing private asset pipeline and associate each occurrence with a chunk from its slide. Retain alt text and slide caption. |
| Speaker notes | Include the notes text frame after the slide's visible content; exclude notes-page boilerplate. |
| Hidden slides | Include content and preserve `hidden=true` in metadata. |
| SmartArt | Best-effort cached node text. Record `smartart_text_only`; diagram relationships/layout are not interpreted. Images stored only inside a SmartArt data/drawing part are not extracted. |
| OLE/embedded files, linked objects, media and unrecognized graphic frames | Keep exposed text/image previews when available and record `unsupported_objects`; opaque binaries are not opened or executed. Insert an explicit unavailable-content marker. |

Slides are not rendered. There is no OCR, visual chart interpretation, image
embedding, animation/video transcription, external fetching, or automatic
parsing of embedded spreadsheets/files. Inherited master/layout artwork is not
expanded. Legacy `.ppt` and `.pptm` are unsupported; convert them to `.pptx`.
Encrypted, malformed, corrupt, oversized and unsafe packages are rejected.

## Chunking, citations and lifecycle

- One deck is one document with a stable path-derived `doc_id` and
  `source_type=powerpoint`. The catalog returns `document_type=powerpoint`.
- Chunk each non-empty slide separately with the configured chunker. Chunks
  retain one-based slide number as citation `page`, the slide title as `section`,
  global source offsets, and hidden-slide metadata. Chunks do not cross slides.
- Original package bytes determine the content hash, so image/object-only
  edits trigger re-ingestion. Unchanged files preserve count/time; changed
  versions replace the same scoped publication atomically. A blank deck
  publishes zero chunks and removes the old scoped content/assets.
- Missing chart caches/external images and SmartArt limitations are recorded
  under `extraction_warnings` in private source metadata. Source load failures
  participate in the existing directory-rescan protection.
- Limits are shared with other loaders: registry file-size limit, bounded OOXML
  entry count/expanded size, and configured image count/byte limits.

## Usage and rollout

```json
{
  "source_path": "E:/documents/presentation.pptx",
  "workspace_id": "local",
  "dry_run": true
}
```

Send this body to `POST /ingest`; set `dry_run=false` to index normally. Existing
directory requests discover `.pptx` automatically. No new ingestion endpoint or
frontend upload workflow is introduced.

Install locked dependencies with `uv sync`. Apply migration
`database/migrations/007_powerpoint_document_type.sql` before restarting updated
PostgreSQL writers; it widens the catalog type constraint without touching
existing vectors/documents. Fresh Docker initialization includes migration 007.
The configured local stack has this migration applied and the updated API running.

Frontend should accept `powerpoint` as a canonical type, add its configured
label/color, and treat citation `page` on `.pptx` sources as a slide number.
Existing authorized image previews require no API shape change. Other clients
can retain the documented Unknown/Other fallback for unfamiliar types.

## Validation

The offline suite covers mixed slides, Unicode/Hebrew, tables, category/XY
charts, missing/external chart data, grouped shapes, notes, hidden/blank slides,
SmartArt text, embedded-object previews, image-only hash changes, external image
exclusion, unsafe packages, slide-local offsets and normal ingestion lifecycle.

The local smoke runner uses mixed-content fixtures and synthetic embeddings
against real PostgreSQL, validates catalog counts/type, slide citations and asset
references, exercises unchanged/failed/changed/blank ingestion, and always rolls
back its temporary SQL records. It makes no real model calls:

```powershell
.venv/Scripts/python.exe scripts/validate_powerpoint_ingestion.py --output docs/phase_qa/NP21-live-powerpoint-ingestion.json
```

Evidence: `phase_qa/NP21-live-powerpoint-ingestion.json`. Actual presentation
quality can be reviewed by ingesting a representative deck through the normal
workflow; synthetic checks establish pipeline correctness without interpreting
its pictures or charts visually.

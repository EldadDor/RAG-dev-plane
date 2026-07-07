---
applyTo: "src/**/*ingest*.py,src/**/*loader*.py,src/**/*parser*.py,src/**/*chunk*.py,src/**/*document*.py,tests/**/*ingest*.py,tests/**/*loader*.py,tests/**/*chunk*.py"
---

# Ingestion and chunking instructions

These instructions apply to document loading, normalization, metadata extraction, and chunking.

## Baseline assumptions
- Build the ingestion pipeline in Python.
- Use typed models for intermediate records.
- Persist provenance-rich metadata that will later be stored in vector store records (Qdrant payloads or PostgreSQL metadata JSONB).

## Required behavior
- Separate loading, parsing, normalization, and chunking into independent units.
- Preserve `doc_id`, `source_path`, `source_type`, title when available, and structural location markers such as page, heading, or section.
- Generate deterministic chunk IDs.
- Keep one default chunking strategy for v1, with configurable chunk size and overlap.
- Prefer structure-aware chunk boundaries when they can be extracted reliably.

## Reliability rules
- Validate file size and allowed file types.
- Handle malformed files gracefully and record skip reasons.
- Avoid dropping metadata during transformations.
- Make re-ingestion idempotent where possible.

## Testing
- Add tests for deterministic chunk IDs.
- Add tests for metadata propagation.
- Add tests for chunking behavior on markdown, HTML, plain text, and any supported PDF path.
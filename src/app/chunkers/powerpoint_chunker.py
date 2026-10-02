"""Keep presentation chunks within one slide and preserve source offsets."""
from dataclasses import replace

from app.chunkers.chunker_adapter import ChunkedText, TextChunker
from app.domain.models import Document


def chunk_powerpoint_document(document: Document, chunker: TextChunker) -> list[ChunkedText]:
    chunks = []
    for slide in document.metadata["slides"]:
        start, end = slide["start_index"], slide["end_index"]
        text = document.content[start:end]
        if not text.strip():
            continue
        for chunk in chunker.chunk(text):
            chunks.append(replace(
                chunk,
                start_index=start + chunk.start_index if chunk.start_index is not None else start,
                end_index=start + chunk.end_index if chunk.end_index is not None else end,
                metadata={**(chunk.metadata or {}), "page": slide["slide_number"],
                          "slide_number": slide["slide_number"], "section": slide["title"],
                          "hidden": slide["hidden"]},
            ))
    return chunks

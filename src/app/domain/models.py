from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class SourceType(str, Enum):
    markdown = "markdown"
    html = "html"
    pdf = "pdf"
    text = "text"
    unknown = "unknown"


@dataclass
class Document:
    """A raw loaded document before chunking."""

    doc_id: str
    source_path: str
    source_type: SourceType
    content: str
    title: str | None = None
    # Structural metadata preserved from the source
    metadata: dict = field(default_factory=dict)


@dataclass
class Chunk:
    """A single text chunk ready for embedding and indexing."""

    chunk_id: str
    doc_id: str
    source_path: str
    source_type: SourceType
    text: str
    chunk_index: int
    title: str | None = None
    page: int | None = None
    section: str | None = None


@dataclass
class RetrievedChunk:
    """A chunk returned from a vector search, with a similarity score."""

    chunk_id: str
    doc_id: str
    source_path: str
    text: str
    score: float
    title: str | None = None
    page: int | None = None
    section: str | None = None

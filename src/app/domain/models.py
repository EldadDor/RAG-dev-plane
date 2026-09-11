from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class SourceType(str, Enum):
    markdown = "markdown"
    html = "html"
    pdf = "pdf"
    word = "word"
    text = "text"
    code = "code"
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
    # Loaders may hash source material that is not represented in text (for
    # example embedded images in a Word package).
    content_hash: str | None = None
    assets: list["DocumentAsset"] = field(default_factory=list)


@dataclass
class DocumentAsset:
    """An embedded source asset extracted by a loader before persistence."""

    anchor_id: str
    relationship_id: str
    content: bytes = field(repr=False)
    content_hash: str = ""
    media_type: str = "application/octet-stream"
    original_name: str | None = None
    ordinal: int = 0
    block_id: str | None = None
    block_ordinal: int | None = None
    source_index: int | None = None
    section: str | None = None
    alt_text: str | None = None
    caption: str | None = None
    width: int | None = None
    height: int | None = None


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
    related_asset_ids: tuple[str, ...] = ()
    related_assets: tuple[dict, ...] = ()


@dataclass
class IngestedChunk:
    """A chunk with its embedding, ready to be upserted into the vector store."""

    doc_id: str
    chunk_id: str
    text: str
    embedding: list[float]
    source_path: str
    title: str | None = None
    page: int | None = None
    section: str | None = None
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Serialise to the dict format expected by VectorStore.upsert()."""
        return {
            "chunk_id": self.chunk_id,
            "vector": self.embedding,
            "payload": {
                "doc_id": self.doc_id,
                "chunk_id": self.chunk_id,
                "text": self.text,
                "source_path": self.source_path,
                "title": self.title,
                "page": self.page,
                "section": self.section,
                **self.metadata,
            },
        }


@dataclass
class IngestedDocumentResult:
    doc_id: str
    source_path: str
    chunks_indexed: int
    skipped: bool = False
    skip_reason: str | None = None
    assets_found: int = 0


@dataclass
class IngestionResult:
    """Summary returned after ingesting a file or directory."""

    source_path: str
    documents_processed: int
    chunks_indexed: int
    chunker_provider: str
    chunking_profile: str = "default"
    dry_run: bool = False
    documents: list[IngestedDocumentResult] = field(default_factory=list)

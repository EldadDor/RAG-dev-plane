import pytest
import tempfile
import os

from app.chunkers.text_chunker import TextChunker
from app.domain.models import Document, SourceType
from app.chunkers.ids import make_doc_id


def _make_doc(content: str, source_type: SourceType = SourceType.text) -> Document:
    return Document(
        doc_id=make_doc_id("test/sample.txt"),
        source_path="test/sample.txt",
        source_type=source_type,
        content=content,
        title="Sample",
    )


def test_chunker_produces_chunks():
    chunker = TextChunker(chunk_size=200, chunk_overlap=20)
    doc = _make_doc("word " * 200)
    chunks = chunker.chunk(doc)
    assert len(chunks) > 1


def test_chunker_preserves_doc_id():
    chunker = TextChunker(chunk_size=200, chunk_overlap=20)
    doc = _make_doc("word " * 200)
    chunks = chunker.chunk(doc)
    for chunk in chunks:
        assert chunk.doc_id == doc.doc_id


def test_chunker_preserves_source_path():
    chunker = TextChunker(chunk_size=200, chunk_overlap=20)
    doc = _make_doc("word " * 200)
    chunks = chunker.chunk(doc)
    for chunk in chunks:
        assert chunk.source_path == doc.source_path


def test_chunker_chunk_ids_are_unique():
    chunker = TextChunker(chunk_size=200, chunk_overlap=20)
    doc = _make_doc("word " * 200)
    chunks = chunker.chunk(doc)
    ids = [c.chunk_id for c in chunks]
    assert len(ids) == len(set(ids))


def test_markdown_chunker_extracts_sections():
    content = "# Title\n\nIntro text.\n\n## Section A\n\nContent A.\n\n## Section B\n\nContent B.\n"
    chunker = TextChunker(chunk_size=500, chunk_overlap=50)
    doc = _make_doc(content, source_type=SourceType.markdown)
    chunks = chunker.chunk(doc)
    sections = {c.section for c in chunks if c.section}
    assert len(sections) >= 1


def test_chunker_metadata_propagation():
    chunker = TextChunker(chunk_size=200, chunk_overlap=20)
    doc = Document(
        doc_id=make_doc_id("test/file.txt"),
        source_path="test/file.txt",
        source_type=SourceType.text,
        content="word " * 200,
        title="My Doc",
        metadata={"page": 3},
    )
    chunks = chunker.chunk(doc)
    for chunk in chunks:
        assert chunk.title == "My Doc"
        assert chunk.page == 3

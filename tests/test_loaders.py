import pytest
import tempfile
from pathlib import Path

from app.loaders.markdown_loader import MarkdownLoader
from app.loaders.text_loader import TextLoader
from app.loaders.html_loader import HTMLLoader
from app.loaders.registry import load_document, UnsupportedFileTypeError, FileTooLargeError
from app.domain.models import SourceType


def test_text_loader_preserves_content(tmp_path):
    f = tmp_path / "sample.txt"
    f.write_text("Hello world", encoding="utf-8")
    doc = TextLoader().load(str(f))
    assert doc.content == "Hello world"
    assert doc.source_type == SourceType.text
    assert doc.source_path == str(f)


def test_markdown_loader_extracts_title(tmp_path):
    f = tmp_path / "readme.md"
    f.write_text("# My Title\n\nSome content.", encoding="utf-8")
    doc = MarkdownLoader().load(str(f))
    assert doc.title == "My Title"
    assert doc.source_type == SourceType.markdown


def test_html_loader_extracts_title(tmp_path):
    f = tmp_path / "page.html"
    f.write_text("<html><head><title>Page Title</title></head><body><p>Text</p></body></html>", encoding="utf-8")
    doc = HTMLLoader().load(str(f))
    assert doc.title == "Page Title"
    assert doc.source_type == SourceType.html
    assert "Text" in doc.content


def test_doc_id_is_deterministic(tmp_path):
    f = tmp_path / "sample.txt"
    f.write_text("content", encoding="utf-8")
    doc1 = TextLoader().load(str(f))
    doc2 = TextLoader().load(str(f))
    assert doc1.doc_id == doc2.doc_id


def test_unsupported_extension_raises(tmp_path):
    f = tmp_path / "archive.zip"
    f.write_bytes(b"fake zip content")
    with pytest.raises(UnsupportedFileTypeError):
        load_document(str(f))


def test_file_not_found_raises():
    with pytest.raises(FileNotFoundError):
        load_document("/nonexistent/path/file.txt")


def test_file_too_large_raises(tmp_path):
    f = tmp_path / "big.txt"
    f.write_bytes(b"x" * 100)
    with pytest.raises(FileTooLargeError):
        load_document(str(f), max_bytes=50)

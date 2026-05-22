from __future__ import annotations

from pathlib import Path

from app.domain.models import Document, SourceType
from app.loaders.html_loader import HTMLLoader
from app.loaders.markdown_loader import MarkdownLoader
from app.loaders.pdf_loader import PDFLoader
from app.loaders.text_loader import TextLoader

_LOADER_MAP = {
    ".md": MarkdownLoader,
    ".mdx": MarkdownLoader,
    ".html": HTMLLoader,
    ".htm": HTMLLoader,
    ".pdf": PDFLoader,
    ".txt": TextLoader,
}

SUPPORTED_EXTENSIONS = set(_LOADER_MAP.keys())


class UnsupportedFileTypeError(ValueError):
    pass


class FileTooLargeError(ValueError):
    pass


def load_document(source_path: str, max_bytes: int = 50 * 1024 * 1024) -> Document:
    """
    Load a document from disk using the appropriate loader for its extension.

    Raises:
        UnsupportedFileTypeError: if the extension is not supported.
        FileTooLargeError: if the file exceeds max_bytes.
        FileNotFoundError: if the path does not exist.
    """
    path = Path(source_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {source_path}")

    size = path.stat().st_size
    if size > max_bytes:
        raise FileTooLargeError(f"File too large ({size} bytes): {source_path}")

    ext = path.suffix.lower()
    loader_cls = _LOADER_MAP.get(ext)
    if loader_cls is None:
        raise UnsupportedFileTypeError(f"Unsupported file type '{ext}': {source_path}")

    return loader_cls().load(source_path)


def load_directory(
    directory: str,
    recursive: bool = False,
    max_bytes: int = 50 * 1024 * 1024,
) -> tuple[list[Document], list[dict]]:
    """
    Load all supported documents from a directory.

    Returns:
        (documents, skipped) where skipped is a list of dicts with path and reason.
    """
    base = Path(directory)
    pattern = "**/*" if recursive else "*"
    documents: list[Document] = []
    skipped: list[dict] = []

    for path in sorted(base.glob(pattern)):
        if not path.is_file():
            continue
        if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            continue
        try:
            doc = load_document(str(path), max_bytes=max_bytes)
            documents.append(doc)
        except (UnsupportedFileTypeError, FileTooLargeError, Exception) as exc:
            skipped.append({"path": str(path), "reason": str(exc)})

    return documents, skipped

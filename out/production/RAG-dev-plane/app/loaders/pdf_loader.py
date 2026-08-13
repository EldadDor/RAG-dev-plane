from __future__ import annotations

from pathlib import Path

from pypdf import PdfReader

from app.chunkers.ids import make_doc_id
from app.domain.models import Document, SourceType


class PDFLoader:
    """
    Loads PDF files page-by-page.

    Each page's text is concatenated with page-break markers so the
    chunker can later identify page boundaries.
    """

    def load(self, source_path: str) -> Document:
        path = Path(source_path)
        reader = PdfReader(str(path))

        parts: list[str] = []
        for page_num, page in enumerate(reader.pages, start=1):
            text = page.extract_text() or ""
            parts.append(f"[PAGE {page_num}]\n{text}")

        content = "\n\n".join(parts)

        title: str | None = None
        if reader.metadata:
            title = reader.metadata.get("/Title") or None

        return Document(
            doc_id=make_doc_id(source_path),
            source_path=source_path,
            source_type=SourceType.pdf,
            content=content,
            title=title or path.stem,
            metadata={"total_pages": len(reader.pages)},
        )

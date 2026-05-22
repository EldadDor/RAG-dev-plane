from __future__ import annotations

from pathlib import Path

from app.chunkers.ids import make_doc_id
from app.domain.models import Document, SourceType


class TextLoader:
    """Loads plain text (.txt) files."""

    def load(self, source_path: str) -> Document:
        path = Path(source_path)
        content = path.read_text(encoding="utf-8", errors="replace")
        return Document(
            doc_id=make_doc_id(source_path),
            source_path=source_path,
            source_type=SourceType.text,
            content=content,
            title=path.stem,
        )

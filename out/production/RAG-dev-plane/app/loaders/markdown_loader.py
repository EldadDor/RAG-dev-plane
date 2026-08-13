from __future__ import annotations

from pathlib import Path

from app.chunkers.ids import make_doc_id
from app.domain.models import Document, SourceType


class MarkdownLoader:
    """Loads Markdown (.md, .mdx) files."""

    def load(self, source_path: str) -> Document:
        path = Path(source_path)
        content = path.read_text(encoding="utf-8", errors="replace")
        # Extract first H1 as title if present
        title: str | None = None
        for line in content.splitlines():
            stripped = line.strip()
            if stripped.startswith("# "):
                title = stripped[2:].strip()
                break
        return Document(
            doc_id=make_doc_id(source_path),
            source_path=source_path,
            source_type=SourceType.markdown,
            content=content,
            title=title or path.stem,
        )

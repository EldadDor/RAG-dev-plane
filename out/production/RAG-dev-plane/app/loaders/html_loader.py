from __future__ import annotations

from pathlib import Path

from bs4 import BeautifulSoup

from app.chunkers.ids import make_doc_id
from app.domain.models import Document, SourceType


class HTMLLoader:
    """Loads HTML files, extracting visible text while preserving title metadata."""

    def load(self, source_path: str) -> Document:
        path = Path(source_path)
        raw_html = path.read_text(encoding="utf-8", errors="replace")
        soup = BeautifulSoup(raw_html, "lxml")

        # Remove script and style blocks
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()

        title: str | None = None
        title_tag = soup.find("title")
        if title_tag:
            title = title_tag.get_text(strip=True) or None
        if not title:
            h1 = soup.find("h1")
            if h1:
                title = h1.get_text(strip=True) or None

        content = soup.get_text(separator="\n", strip=True)

        return Document(
            doc_id=make_doc_id(source_path),
            source_path=source_path,
            source_type=SourceType.html,
            content=content,
            title=title or path.stem,
        )

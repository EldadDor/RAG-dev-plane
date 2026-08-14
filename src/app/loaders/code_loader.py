from __future__ import annotations

from pathlib import Path

from app.chunkers.ids import make_doc_id
from app.domain.models import Document, SourceType


_LANGUAGES = {
    ".py": "python", ".js": "javascript", ".jsx": "javascript", ".ts": "typescript",
    ".tsx": "typescript", ".java": "java", ".cs": "csharp", ".go": "go", ".rs": "rust",
    ".sql": "sql", ".json": "json", ".yaml": "yaml", ".yml": "yaml", ".toml": "toml",
}


class CodeLoader:
    """Loads source/configuration files while preserving language provenance."""

    def load(self, source_path: str) -> Document:
        path = Path(source_path)
        language = _LANGUAGES.get(path.suffix.lower(), "unknown")
        return Document(
            doc_id=make_doc_id(source_path),
            source_path=source_path,
            source_type=SourceType.code,
            content=path.read_text(encoding="utf-8", errors="replace"),
            title=path.name,
            metadata={"language": language},
        )

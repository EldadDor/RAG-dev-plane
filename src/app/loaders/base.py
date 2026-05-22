from __future__ import annotations

from typing import Protocol

from app.domain.models import Document


class DocumentLoader(Protocol):
    """Protocol for loading a file into a Document."""

    def load(self, source_path: str) -> Document: ...

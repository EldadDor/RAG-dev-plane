from __future__ import annotations

import hashlib


def make_chunk_id(doc_id: str, chunk_index: int) -> str:
    """Generate a deterministic, collision-resistant chunk ID."""
    raw = f"{doc_id}::{chunk_index}"
    return hashlib.sha256(raw.encode()).hexdigest()


def make_doc_id(source_path: str) -> str:
    """Generate a deterministic document ID from its source path."""
    return hashlib.sha256(source_path.encode()).hexdigest()

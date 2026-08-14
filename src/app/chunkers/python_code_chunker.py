"""AST-aware chunking for Python source files."""

from __future__ import annotations

import ast

from app.chunkers.chunker_adapter import ChunkedText
from app.domain.models import Document


def chunk_python_document(document: Document) -> list[ChunkedText]:
    """Return module, class, and function chunks with symbol and line metadata."""
    try:
        tree = ast.parse(document.content)
    except SyntaxError:
        return [ChunkedText(text=document.content, metadata={"language": "python", "parse_error": True})]

    lines = document.content.splitlines(keepends=True)
    chunks: list[ChunkedText] = []
    symbol_nodes = [node for node in tree.body if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))]

    first_symbol_line = min((node.lineno for node in symbol_nodes), default=len(lines) + 1)
    preamble = "".join(lines[: first_symbol_line - 1]).strip()
    if preamble:
        chunks.append(
            ChunkedText(
                text=preamble,
                metadata={"language": "python", "symbol": "<module>", "symbol_type": "module", "line_start": 1, "line_end": first_symbol_line - 1},
            )
        )

    for node in symbol_nodes:
        end_line = getattr(node, "end_lineno", node.lineno)
        symbol_type = "class" if isinstance(node, ast.ClassDef) else "async_function" if isinstance(node, ast.AsyncFunctionDef) else "function"
        source = "".join(lines[node.lineno - 1 : end_line]).strip()
        if source:
            chunks.append(
                ChunkedText(
                    text=source,
                    metadata={"language": "python", "symbol": node.name, "symbol_type": symbol_type, "line_start": node.lineno, "line_end": end_line},
                )
            )

    return chunks or [ChunkedText(text=document.content, metadata={"language": "python", "symbol": "<module>", "symbol_type": "module", "line_start": 1, "line_end": len(lines)})]

"""Tree-sitter declaration-aware chunking for Kotlin source files."""
from __future__ import annotations

from tree_sitter import Language, Parser
import tree_sitter_kotlin

from app.chunkers.chunker_adapter import ChunkedText
from app.domain.models import Document

_LANGUAGE = Language(tree_sitter_kotlin.language())
_TYPES = {"class_declaration": "class", "object_declaration": "object", "interface_declaration": "interface", "enum_class_body": "enum"}
_MEMBERS = {"function_declaration": "function", "property_declaration": "property"}


def chunk_kotlin_document(document: Document) -> list[ChunkedText] | None:
    parser = Parser(_LANGUAGE)
    source = document.content.encode("utf-8")
    tree = parser.parse(source)
    if tree.root_node.has_error:
        return None
    chunks: list[ChunkedText] = []
    for node in tree.root_node.named_children:
        _collect(node, source, [], chunks)
    return chunks or [_chunk(document.content, "<module>", "module", None, 1, document.content.count("\n") + 1)]


def _collect(node, source: bytes, parents: list[str], chunks: list[ChunkedText]) -> None:
    if node.type not in _TYPES and node.type not in _MEMBERS:
        for child in node.named_children:
            _collect(child, source, parents, chunks)
        return
    name_node = node.child_by_field_name("name")
    name = name_node.text.decode("utf-8") if name_node is not None else "<anonymous>"
    symbol = ".".join([*parents, name])
    kind = _TYPES.get(node.type) or _MEMBERS[node.type]
    text = source[node.start_byte:node.end_byte].decode("utf-8", errors="replace").strip()
    if text:
        chunks.append(_chunk(text, symbol, kind, ".".join(parents) or None, node.start_point.row + 1, node.end_point.row + 1))
    for child in node.named_children:
        _collect(child, source, [*parents, name] if node.type in _TYPES else parents, chunks)


def _chunk(text, symbol, symbol_type, enclosing_symbol, line_start, line_end):
    metadata = {"language": "kotlin", "symbol": symbol, "symbol_type": symbol_type, "line_start": line_start, "line_end": line_end}
    if enclosing_symbol:
        metadata["enclosing_symbol"] = enclosing_symbol
    return ChunkedText(text=text, metadata=metadata)

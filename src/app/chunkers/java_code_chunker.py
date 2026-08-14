"""Tree-sitter based, declaration-aware chunking for Java source files."""

from __future__ import annotations

from tree_sitter import Language, Node, Parser
import tree_sitter_java

from app.chunkers.chunker_adapter import ChunkedText
from app.domain.models import Document

_JAVA_LANGUAGE = Language(tree_sitter_java.language())
_TYPE_NODES = {
    "class_declaration": "class",
    "interface_declaration": "interface",
    "enum_declaration": "enum",
    "record_declaration": "record",
    "annotation_type_declaration": "annotation",
}
_MEMBER_NODES = {
    "method_declaration": "method",
    "constructor_declaration": "constructor",
    "compact_constructor_declaration": "constructor",
    "field_declaration": "field",
}


def chunk_java_document(document: Document) -> list[ChunkedText] | None:
    """Split valid Java into preamble, type header, and member declaration chunks.

    Returns ``None`` when Tree-sitter reports syntax errors so ingestion can use
    the generic text chunker instead of indexing unreliable symbol boundaries.
    """
    parser = Parser(_JAVA_LANGUAGE)
    source = document.content.encode("utf-8")
    tree = parser.parse(source)
    if tree.root_node.has_error:
        return None

    declarations = [node for node in tree.root_node.named_children if node.type in _TYPE_NODES]
    first_declaration = min((node.start_byte for node in declarations), default=len(source))
    chunks: list[ChunkedText] = []
    preamble = source[:first_declaration].decode("utf-8", errors="replace").strip()
    if preamble:
        chunks.append(_chunk(preamble, "<module>", "module", None, 1, preamble.count("\n") + 1))

    for declaration in declarations:
        _collect_declaration_chunks(declaration, source, [], chunks)
    return chunks or [_chunk(document.content, "<module>", "module", None, 1, document.content.count("\n") + 1)]


def _collect_declaration_chunks(node: Node, source: bytes, ancestors: list[str], chunks: list[ChunkedText]) -> None:
    name = _node_name(node) or "<anonymous>"
    symbol_type = _TYPE_NODES[node.type]
    symbol = ".".join([*ancestors, name])
    body = node.child_by_field_name("body")
    header_end = body.start_byte if body is not None else node.end_byte
    header = source[node.start_byte:header_end].decode("utf-8", errors="replace").strip()
    if header:
        chunks.append(_chunk(header, symbol, symbol_type, _enclosing_symbol(ancestors), node.start_point.row + 1, (body.start_point.row + 1) if body is not None else node.end_point.row + 1))

    if body is None:
        return
    for child in body.named_children:
        if child.type in _TYPE_NODES:
            _collect_declaration_chunks(child, source, [*ancestors, name], chunks)
        elif child.type in _MEMBER_NODES:
            member_name = _node_name(child) or "<constructor>"
            member_symbol = ".".join([*ancestors, name, member_name])
            text = source[child.start_byte:child.end_byte].decode("utf-8", errors="replace").strip()
            if text:
                chunks.append(_chunk(text, member_symbol, _MEMBER_NODES[child.type], symbol, child.start_point.row + 1, child.end_point.row + 1))


def _node_name(node: Node) -> str | None:
    name = node.child_by_field_name("name")
    if name is None and node.type == "field_declaration":
        declarator = next((child for child in node.named_children if child.type == "variable_declarator"), None)
        name = declarator.child_by_field_name("name") if declarator is not None else None
    return name.text.decode("utf-8", errors="replace") if name is not None else None


def _enclosing_symbol(ancestors: list[str]) -> str | None:
    return ".".join(ancestors) if ancestors else None


def _chunk(text: str, symbol: str, symbol_type: str, enclosing_symbol: str | None, line_start: int, line_end: int) -> ChunkedText:
    metadata = {
        "language": "java",
        "symbol": symbol,
        "symbol_type": symbol_type,
        "line_start": line_start,
        "line_end": line_end,
    }
    if enclosing_symbol:
        metadata["enclosing_symbol"] = enclosing_symbol
    return ChunkedText(text=text, metadata=metadata)

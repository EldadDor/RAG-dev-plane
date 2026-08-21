import pytest

pytest.importorskip("tree_sitter_kotlin")

from app.chunkers.kotlin_code_chunker import chunk_kotlin_document
from app.domain.models import Document, SourceType


def test_kotlin_chunker_preserves_type_and_function_symbols():
    document = Document(
        doc_id="doc",
        source_path="Example.kt",
        source_type=SourceType.code,
        content="""package example

class Example {
    fun greet(name: String): String {
        return name
    }
}
""",
        metadata={"language": "kotlin"},
    )
    chunks = chunk_kotlin_document(document)
    assert chunks is not None
    function = next(chunk for chunk in chunks if chunk.metadata["symbol"] == "Example.greet")
    assert function.metadata["symbol_type"] == "function"
    assert function.metadata["enclosing_symbol"] == "Example"
    assert function.metadata["line_start"] == 4
    assert function.metadata["line_end"] == 6


def test_kotlin_chunker_returns_none_for_invalid_source():
    document = Document("doc", "Broken.kt", SourceType.code, "class Broken {", metadata={"language": "kotlin"})
    assert chunk_kotlin_document(document) is None

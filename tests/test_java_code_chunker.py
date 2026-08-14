import pytest

pytest.importorskip("tree_sitter_java")

from app.chunkers.java_code_chunker import chunk_java_document
from app.domain.models import Document, SourceType


def test_java_chunker_preserves_type_and_method_symbols():
    document = Document(
        doc_id="doc",
        source_path="Example.java",
        source_type=SourceType.code,
        content="""package example;

public class Example {
    private final String name;

    public String getName() {
        return name;
    }
}
""",
        metadata={"language": "java"},
    )

    chunks = chunk_java_document(document)

    assert chunks is not None
    method = next(chunk for chunk in chunks if chunk.metadata and chunk.metadata["symbol"] == "Example.getName")
    assert method.metadata["symbol_type"] == "method"
    assert method.metadata["enclosing_symbol"] == "Example"
    assert method.metadata["line_start"] == 6
    assert method.metadata["line_end"] == 8


def test_java_chunker_falls_back_for_invalid_source():
    document = Document("doc", "Broken.java", SourceType.code, "class Broken {", metadata={"language": "java"})
    assert chunk_java_document(document) is None

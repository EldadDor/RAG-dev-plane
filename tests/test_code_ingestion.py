from app.chunkers.python_code_chunker import chunk_python_document
from app.domain.models import Document, SourceType
from app.loaders.code_loader import CodeLoader


def test_python_loader_preserves_language_metadata(tmp_path):
    source = tmp_path / "example.py"
    source.write_text("def hello():\n    return 'world'\n", encoding="utf-8")

    document = CodeLoader().load(str(source))

    assert document.source_type == SourceType.code
    assert document.metadata["language"] == "python"


def test_kotlin_loader_preserves_language_metadata(tmp_path):
    source = tmp_path / "Example.kt"
    source.write_text("class Example", encoding="utf-8")

    document = CodeLoader().load(str(source))

    assert document.source_type == SourceType.code
    assert document.metadata["language"] == "kotlin"


def test_python_chunker_preserves_symbol_and_line_range():
    document = Document(
        doc_id="doc", source_path="example.py", source_type=SourceType.code,
        content="import os\n\ndef hello(name):\n    return f'Hi {name}'\n",
        metadata={"language": "python"},
    )

    chunks = chunk_python_document(document)

    function_chunk = next(chunk for chunk in chunks if chunk.metadata and chunk.metadata["symbol"] == "hello")
    assert function_chunk.metadata == {
        "language": "python", "symbol": "hello", "symbol_type": "function", "line_start": 3, "line_end": 4,
    }

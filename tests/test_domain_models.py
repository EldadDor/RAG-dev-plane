from app.domain.models import IngestedChunk


def test_ingested_chunk_uses_top_level_chunk_id_for_vector_store_contract():
    chunk = IngestedChunk(
        doc_id="document-1",
        chunk_id="chunk-1",
        text="Example content",
        embedding=[0.1, 0.2],
        source_path="docs/example.md",
    )

    payload = chunk.to_dict()

    assert payload["chunk_id"] == "chunk-1"
    assert "id" not in payload
    assert payload["payload"]["chunk_id"] == "chunk-1"

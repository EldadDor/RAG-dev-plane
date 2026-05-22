import pytest

from app.chunkers.ids import make_chunk_id, make_doc_id


def test_make_doc_id_is_deterministic():
    assert make_doc_id("docs/readme.md") == make_doc_id("docs/readme.md")


def test_make_doc_id_differs_for_different_paths():
    assert make_doc_id("docs/a.md") != make_doc_id("docs/b.md")


def test_make_chunk_id_is_deterministic():
    doc_id = make_doc_id("docs/readme.md")
    assert make_chunk_id(doc_id, 0) == make_chunk_id(doc_id, 0)


def test_make_chunk_id_differs_for_different_indexes():
    doc_id = make_doc_id("docs/readme.md")
    assert make_chunk_id(doc_id, 0) != make_chunk_id(doc_id, 1)


def test_make_chunk_id_differs_for_different_docs():
    id_a = make_doc_id("docs/a.md")
    id_b = make_doc_id("docs/b.md")
    assert make_chunk_id(id_a, 0) != make_chunk_id(id_b, 0)

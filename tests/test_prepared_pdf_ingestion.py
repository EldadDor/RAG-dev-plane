from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.config import Settings
from app.loaders.pdf_extraction import ExtractionBlock, ExtractionOptions, ExtractionResult, assemble
from app.loaders.prepared_pdf_loader import (
    ExtractionPending, PreparedPDFLoader, V5_POLICY, pdf_asset_chunk_indexes, pdf_chunk_provenance,
)
from app.loaders.registry import load_directory
from app.services.asset_store import InMemoryAssetStore
from app.services.ingestion_service import IngestionService


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf8")


@pytest.fixture
def prepared(tmp_path):
    source = tmp_path / "PDFs/source.pdf"
    source.parent.mkdir()
    source.write_bytes(b"%PDF-1.7\nsynthetic source bytes")
    sha = hashlib.sha256(source.read_bytes()).hexdigest()
    references = tmp_path / "references.jsonl"
    references.write_text('{"verified_by":"operator"}\n', encoding="utf8")
    manifest = tmp_path / "manifest.json"
    write_json(manifest, {"schema_version": 1, "status": "frozen", "documents": [
        {"id": "pdf-001", "source_path": str(source), "source_sha256": sha,
         "references_path": str(references), "references_sha256": hashlib.sha256(references.read_bytes()).hexdigest()}]})
    options = asdict(ExtractionOptions(pdf_backend="pypdfium2"))
    blocks = [ExtractionBlock("a" * 64, 0, "image", "", [1], payload={"source_ref": "#/pictures/0", "caption": "Figure"}),
              ExtractionBlock("b" * 64, 1, "text", "A diagram label with useful source facts.", [1],
                              payload={"source_ref": "#/texts/0", "picture_parent_ref": "#/pictures/0",
                                       "picture_parent_block_id": "a" * 64}),
              ExtractionBlock("c" * 64, 2, "text", "Independent page two evidence.", [2], payload={"source_ref": "#/texts/1"})]
    result = ExtractionResult(sha, 2, "docling", {"docling": "frozen-test"},
                              {"options": options, "normalization_policy": V5_POLICY}, blocks)
    result.assembled_text = assemble(blocks)
    normalized = result.normalized("pdf-001")
    png = b"\x89PNG\r\n\x1a\nsynthetic image"
    digest = hashlib.sha256(png).hexdigest()
    normalized["blocks"][0]["asset_anchor"] = "a" * 64 + ":" + digest
    normalized["assets"] = [{"anchor": normalized["blocks"][0]["asset_anchor"], "block_id": "a" * 64,
                             "sha256": digest, "media_type": "image/png", "file": f"assets/{digest}.png"}]
    root = tmp_path / "private-run"
    write_json(root / "report.json", {"format_version": 1, "status": "completed", "warm_runs": 3,
        "timeout_seconds": 180, "memory_limit_mib": 8192, "settings": options,
        "manifest_sha256": hashlib.sha256(manifest.read_bytes()).hexdigest(), "documents": [
            {"engine": "docling", "document_id": "pdf-001", "status": "completed", "runs": [
                {"run": r, "status": "completed"} for r in ("cold", "warm-1", "warm-2", "warm-3")]}]})
    for run in ("cold", "warm-1", "warm-2", "warm-3"):
        folder = root / "pdf-001/docling" / run
        write_json(folder / "normalized.json", normalized)
        asset = folder / normalized["assets"][0]["file"]
        asset.parent.mkdir()
        asset.write_bytes(png)
    return SimpleNamespace(source=source, manifest=manifest, root=root, normalized=normalized)


def loader(fixture, root=True):
    return PreparedPDFLoader(fixture.manifest, fixture.root if root else None, "docling-noocr")


def mutate_artifacts(fixture, change):
    value = deepcopy(fixture.normalized)
    change(value)
    for run in ("cold", "warm-1", "warm-2", "warm-3"):
        write_json(fixture.root / "pdf-001/docling" / run / "normalized.json", value)


def settings(**extra):
    return Settings(_env_file=None, CHAT_BASE_URL="http://localhost:8080/v1", VECTOR_STORE="qdrant", **extra)


def test_prepared_mapping_and_exact_picture_links(prepared):
    document = loader(prepared).load(str(prepared.source))
    assert document.metadata["source_sha256"] == prepared.normalized["source_sha256"]
    assert document.assets[0].block_id == "a" * 64
    blocks = document.metadata["_pdf_blocks"]
    child, unrelated = blocks[1], blocks[2]
    chunks = [(4, SimpleNamespace(start_index=child["start"], end_index=child["end"])),
              (9, SimpleNamespace(start_index=unrelated["start"], end_index=unrelated["end"]))]
    assert pdf_asset_chunk_indexes(document, document.assets[0], chunks) == [4]
    provenance = pdf_chunk_provenance(document, child["start"], unrelated["end"])
    assert provenance["source_pages"] == [1, 2] and provenance["page"] == 1
    assert len(provenance["extraction_blocks"]) == 2


def test_missing_artifacts_report_pending_without_models(prepared):
    with pytest.raises(ExtractionPending):
        loader(prepared, root=False).load(str(prepared.source))


@pytest.mark.parametrize("defect", ["offset", "parent", "cycle", "asset_path", "source", "partial", "policy", "nonfinite"])
def test_rejects_corrupt_prepared_artifacts(prepared, defect):
    def change(d):
        if defect == "offset": d["blocks"][1]["end"] += 1
        elif defect == "parent": d["blocks"][1]["payload"]["picture_parent_block_id"] = "f" * 64
        elif defect == "cycle":
            d["blocks"][0]["payload"].update(picture_parent_block_id="a" * 64, picture_parent_ref="#/pictures/0")
        elif defect == "asset_path": d["assets"][0]["file"] = "../../../../outside.png"
        elif defect == "source": d["source_sha256"] = "f" * 64
        elif defect == "partial": d["status"] = "partial"
        elif defect == "policy": d["settings"]["normalization_policy"] = "old"
        elif defect == "nonfinite":
            d["blocks"][1]["boxes"] = [{"page": 1, "left": 0, "right": 1, "top": 0, "bottom": 1,
                                       "page_width": float("inf"), "page_height": 10}]
    mutate_artifacts(prepared, change)
    with pytest.raises((ValueError, FileNotFoundError)):
        loader(prepared).load(str(prepared.source))


@pytest.mark.parametrize("target", ["source", "asset", "warm", "report"])
def test_rejects_hash_stability_and_report_changes(prepared, target):
    if target == "source": prepared.source.write_bytes(b"changed PDF")
    elif target == "asset":
        (prepared.root / "pdf-001/docling/cold" / prepared.normalized["assets"][0]["file"]).write_bytes(b"wrong")
    elif target == "warm":
        value = deepcopy(prepared.normalized); value["assembled_text"] += "different"
        write_json(prepared.root / "pdf-001/docling/warm-2/normalized.json", value)
    elif target == "report":
        path = prepared.root / "report.json"; report = json.loads(path.read_text())
        report["manifest_sha256"] = "f" * 64; write_json(path, report)
    with pytest.raises(ValueError): loader(prepared).load(str(prepared.source))


def test_loader_injection_handles_directory_and_protected_failure(prepared):
    selected = loader(prepared)
    docs, skipped = load_directory(str(prepared.source.parent), document_loader=selected.load)
    assert len(docs) == 1 and not skipped
    mutate_artifacts(prepared, lambda d: d.update(status="partial"))
    docs, skipped = load_directory(str(prepared.source.parent), document_loader=selected.load)
    assert not docs and skipped[0]["path"] == str(prepared.source)


@pytest.mark.asyncio
async def test_dry_run_does_not_embed_or_write(prepared):
    embeddings, vector = AsyncMock(), AsyncMock()
    assets = InMemoryAssetStore()
    result = await IngestionService(settings(), embeddings, vector, assets,
                                    document_loader=loader(prepared).load).ingest_path(str(prepared.source), dry_run=True)
    assert result.chunks_indexed > 0
    embeddings.create_embedding.assert_not_awaited()
    vector.replace_document.assert_not_awaited()
    vector.get_document_hash.assert_not_awaited()
    assert not assets.items


@pytest.mark.asyncio
async def test_processing_identity_skip_scope_and_chunk_provenance(prepared):
    embeddings, vector = AsyncMock(), AsyncMock()
    embeddings.create_embedding.return_value = [0.1]
    vector.get_document_hash.return_value = None
    selected = loader(prepared)
    service = IngestionService(settings(), embeddings, vector, document_loader=selected.load)
    await service.ingest_path(str(prepared.source), workspace_id="benchmark", model_profile="frozen")
    document, chunks, assets = vector.replace_document.await_args.args
    assert document["workspace_id"] == "benchmark"
    assert "_pdf_blocks" not in document["metadata"]
    assert chunks[0]["payload"]["source_pages"] == [1, 2]
    assert chunks[0]["payload"]["related_asset_ids"] == [assets[0]["asset_id"]]
    assert "_pdf_blocks" not in chunks[0]["payload"]
    vector.get_document_hash.return_value = document["content_hash"]
    vector.replace_document.reset_mock(); embeddings.reset_mock()
    result = await service.ingest_path(str(prepared.source), workspace_id="benchmark", model_profile="frozen")
    assert result.documents[0].skip_reason == "unchanged"
    vector.replace_document.assert_not_awaited(); embeddings.create_embedding.assert_not_awaited()
    altered = IngestionService(settings(CHUNK_SIZE=100, CHUNK_OVERLAP=10), embeddings, vector,
                               document_loader=selected.load)
    await altered.ingest_path(str(prepared.source), workspace_id="benchmark")
    assert vector.replace_document.await_args.args[0]["content_hash"] != document["content_hash"]


@pytest.mark.asyncio
async def test_embedding_failure_preserves_previous_publication(prepared):
    embeddings, vector = AsyncMock(), AsyncMock()
    vector.get_document_hash.return_value = "previous publication"
    embeddings.create_embedding.side_effect = RuntimeError("model unavailable")
    service = IngestionService(settings(), embeddings, vector, document_loader=loader(prepared).load)
    with pytest.raises(RuntimeError, match="model unavailable"):
        await service.ingest_path(str(prepared.source))
    vector.replace_document.assert_not_awaited()


@pytest.mark.asyncio
async def test_cli_missing_extraction_dry_run_never_initializes_storage(prepared, monkeypatch):
    import importlib.util
    spec = importlib.util.spec_from_file_location("stage_c_cli", Path(__file__).parents[1] / "scripts/ingest_local.py")
    cli = importlib.util.module_from_spec(spec); spec.loader.exec_module(cli)
    args = SimpleNamespace(manifest=prepared.manifest, run_root=None, treatment="docling-noocr",
                           workspace_id="rag-stage-c-unit", source=prepared.source.parent,
                           chunking_profile="default", model_profile=None, apply=False)
    report = await cli.ingest(args, settings=settings())
    assert report["status"] == "dry_run" and report["documents_publishable"] == 0
    assert report["failures"][0]["extraction_pending"]


def test_pypdf_empty_page_keeps_page_provenance_without_optional_runtime(prepared):
    source_sha = prepared.normalized["source_sha256"]
    blocks = [ExtractionBlock("d" * 64, 0, "text", "", [1])]
    result = ExtractionResult(source_sha, 1, "pypdf", {"pypdf": "test"},
                              {"options": prepared.normalized["settings"]["options"]}, blocks)
    result.assembled_text = assemble(blocks, baseline=True)
    normalized = result.normalized("pdf-001")
    report_path = prepared.root / "report.json"
    report = json.loads(report_path.read_text())
    report["documents"][0]["engine"] = "pypdf"
    write_json(report_path, report)
    for run in ("cold", "warm-1", "warm-2", "warm-3"):
        write_json(prepared.root / "pdf-001/pypdf" / run / "normalized.json", normalized)
    document = PreparedPDFLoader(prepared.manifest, prepared.root, "pypdf").load(str(prepared.source))
    provenance = pdf_chunk_provenance(document, 0, len(document.content.strip()))
    assert provenance["source_pages"] == [1]
    assert provenance["extraction_blocks"][0]["payload"]["source_ref"] == "#/pages/1"


@pytest.mark.parametrize("limits", [{"max_asset_bytes": 1}, {"max_total_asset_bytes": 1}])
def test_image_budget_rejected_before_ingestion(prepared, limits):
    with pytest.raises(ValueError):
        PreparedPDFLoader(prepared.manifest, prepared.root, "docling-noocr", **limits).load(str(prepared.source))


@pytest.mark.parametrize("assigned_document", [False, True])
def test_benchmark_derivative_preserves_questions_and_defers_negatives(prepared, monkeypatch, assigned_document):
    scripts = Path(__file__).parents[1] / "scripts"
    monkeypatch.syspath_prepend(str(scripts))
    from prepare_pdf_benchmark import prepare
    manifest = json.loads(prepared.manifest.read_text())
    entry = manifest["documents"][0]
    references = [{"id": "unit-positive", "document_id": entry["id"], "question": "Exact frozen question?",
                   "answerable": True, "expected_facts": ["A source fact"],
                   "evidence": [{"page": 1, "source_evidence": "A source fact"}],
                   "verified_by": "human", "verified_on": "2026-10-15"},
                  {"id": "unit-negative", "document_id": entry["id"], "question": "Assigned-document negative?",
                   "answerable": False, "expected_facts": [], "evidence": [], "reason": "Not in assigned source", "negative_scope": "assigned_document",
                   "verified_by": "human", "verified_on": "2026-10-15"}]
    ref_path = Path(entry["references_path"])
    ref_path.write_text("".join(json.dumps(r) + "\n" for r in references), encoding="utf8")
    entry.update(references_sha256=hashlib.sha256(ref_path.read_bytes()).hexdigest(), categories=["text"],
                 languages=["en"], inspection_pages=[1], permission_basis="synthetic permitted fixture")
    write_json(prepared.manifest, manifest)
    from app.chunkers.ids import make_doc_id
    indexed = prepared.root.parent / "index-report.json"
    write_json(indexed, {"status": "indexed", "manifest_sha256": hashlib.sha256(prepared.manifest.read_bytes()).hexdigest(),
                         "chunking_profile": "default", "model_profile": "fixed",
                         "ingestion": {"documents": [{"doc_id": make_doc_id(str(prepared.source.resolve())), "chunks_indexed": 1}]}})
    dataset, coverage = prepare(prepared.manifest, [indexed], prepared.root.parent / "derived-cases", assigned_document=assigned_document)
    rows = [json.loads(line) for line in dataset.read_text().splitlines()]
    assert rows[0]["question"] == "Exact frozen question?"
    assert coverage["cases_total"] == 2
    assert coverage["cases_eligible"] == (2 if assigned_document else 1)
    assert coverage["cases"][1]["status"] == ("eligible" if assigned_document else "deferred_assigned_document_negative_scope")
    if assigned_document:
        from app.evaluation.dataset import load_golden_cases
        loaded = load_golden_cases(dataset)
        assert loaded[1].answerable is False and loaded[1].expected_facts == ()
        assert all(c.document_id == make_doc_id(str(prepared.source.resolve())) for c in loaded)
        assert coverage["negative_cases_eligible"] == 1
        assert loaded[1].negative_scope == "assigned_document"
        assert rows[1]["question"] == references[1]["question"]
    assert ref_path.read_text().splitlines()[1] == json.dumps(references[1])
    with pytest.raises(ValueError, match="already exists"):
        prepare(prepared.manifest, [indexed], prepared.root.parent / "derived-cases", assigned_document=assigned_document)
    zero_report = json.loads(indexed.read_text())
    zero_report["ingestion"]["documents"][0].update(chunks_indexed=0, skip_reason="unchanged")
    write_json(indexed, zero_report)
    with pytest.raises(ValueError, match="No eligible indexed cases"):
        prepare(prepared.manifest, [indexed], prepared.root.parent / "zero-count-cases", assigned_document=assigned_document)


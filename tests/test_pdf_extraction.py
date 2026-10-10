from __future__ import annotations

from dataclasses import replace
import hashlib
from io import BytesIO
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time
from types import ModuleType
from types import SimpleNamespace

import pytest
from pypdf import PdfWriter
from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject

from app.loaders.pdf_extraction import (
    ExtractedAsset, ExtractionBlock, ExtractionError, ExtractionOptions,
    ExtractionResult, SourceBox, assemble, create_parser,
)
from app.loaders.pdf_loader import PDFLoader
from app.loaders.pdf_parsers.docling_adapter import DoclingAdapter

ROOT = Path(__file__).resolve().parents[1]


def pdf(path: Path, text: str = "Revenue 12.50 USD", *, encrypted=False) -> Path:
    writer = PdfWriter()
    page = writer.add_blank_page(width=300, height=400)
    font = DictionaryObject({NameObject("/Type"): NameObject("/Font"),
                             NameObject("/Subtype"): NameObject("/Type1"),
                             NameObject("/BaseFont"): NameObject("/Helvetica")})
    page[NameObject("/Resources")] = DictionaryObject({
        NameObject("/Font"): DictionaryObject({NameObject("/F1"): writer._add_object(font)}),
    })
    stream = DecodedStreamObject()
    stream.set_data(f"BT /F1 12 Tf 10 100 Td ({text}) Tj ET".encode("ascii"))
    page[NameObject("/Contents")] = writer._add_object(stream)
    writer.add_blank_page(width=300, height=400)
    if encrypted:
        writer.encrypt("secret")
    with path.open("wb") as output:
        writer.write(output)
    return path


def manifest(tmp_path: Path) -> Path:
    source = pdf(tmp_path / "source.pdf")
    references = tmp_path / "references.jsonl"
    references.write_text(json.dumps({
        "id": "revenue", "document_id": "doc-001", "question": "What is the revenue?",
        "answerable": True, "expected_facts": ["12.50 USD"],
        "evidence": [{"page": 1, "source_evidence": "Revenue 12.50 USD"}],
        "verified_by": "synthetic-fixture-author", "verified_on": "2026-10-10",
    }) + "\n", encoding="utf-8")
    path = tmp_path / "corpus.json"
    path.write_text(json.dumps({"schema_version": 1, "status": "frozen", "documents": [{
        "id": "doc-001", "source_path": str(source.resolve()),
        "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "categories": ["ordinary_text"], "languages": ["en"], "inspection_pages": [1],
        "permission_basis": "synthetic fixture", "references_path": str(references.resolve()),
        "references_sha256": hashlib.sha256(references.read_bytes()).hexdigest(),
    }]}), encoding="utf-8")
    return path


@pytest.fixture
def private_tmp_path():
    # The CLI deliberately refuses outputs under a checkout, including pytest's basetemp.
    candidates = [Path(tempfile.gettempdir()), ROOT.parent]
    directory = next(path for path in candidates if not any(
        (parent / ".git").exists() for parent in (path, *path.parents)))
    with tempfile.TemporaryDirectory(prefix="rag-pdf-offline-", dir=directory) as folder:
        yield Path(folder)


@pytest.fixture
def cli_module():
    import importlib.util
    spec = importlib.util.spec_from_file_location("pdf_comparison_test", ROOT / "scripts/compare_pdf_parsers.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_baseline_preserves_production_text_and_empty_pages(tmp_path):
    source = pdf(tmp_path / "source.pdf")
    options = ExtractionOptions()
    adapter = create_parser("pypdf", options)
    result = adapter.extract(source, options)
    assert result.assembled_text == PDFLoader().load(str(source)).content
    assert result.source_sha256 == hashlib.sha256(source.read_bytes()).hexdigest()
    assert [b.pages for b in result.blocks] == [[1], [2]]
    assert result.blocks[1].start == result.blocks[1].end
    assert "Page 2 has no extracted text" in result.warnings
    assert "ocr" in result.unsupported
    assert result.normalized("fixture")["document_id"] == "fixture"
    assert [b.block_id for b in adapter.extract(source, options).blocks] == [b.block_id for b in result.blocks]


@pytest.mark.parametrize("mode", ["encrypted", "malformed", "page_limit", "file_limit"])
def test_baseline_rejects_errors_and_limits(tmp_path, mode):
    source = pdf(tmp_path / "source.pdf", encrypted=mode == "encrypted")
    if mode == "malformed":
        source.write_bytes(b"not a PDF")
    options = ExtractionOptions(max_pages=1 if mode == "page_limit" else 200,
                                max_bytes=10 if mode == "file_limit" else 50 * 1024 * 1024)
    with pytest.raises(Exception):
        create_parser("pypdf", options).extract(source, options)


def test_unicode_offsets_and_multilocation_blocks():
    blocks = [ExtractionBlock("a", 0, "text", "שלום USD", [1]),
              ExtractionBlock("b", 1, "table", "x | 12.50", [1, 2]),
              ExtractionBlock("c", 2, "image", "", [2])]
    result = ExtractionResult("f" * 64, 2, "fake", {}, {}, blocks,
                              assembled_text=assemble(blocks))
    result.validate()
    for block in blocks:
        assert result.assembled_text[block.start:block.end] == block.source_text
    assert blocks[0].end - blocks[0].start == len("שלום USD")
    assert blocks[1].pages == [1, 2]
    blocks[0].end += 1
    with pytest.raises(ExtractionError, match="text does not match"):
        result.validate()


@pytest.mark.parametrize("mutation", ["page", "duplicate_id", "asset", "box"])
def test_result_rejects_bad_provenance_and_assets(mutation):
    blocks = [ExtractionBlock("a", 0, "text", "a", [1]),
              ExtractionBlock("b", 1, "image", "", [1])]
    result = ExtractionResult("f" * 64, 1, "fake", {}, {}, blocks,
                              assembled_text=assemble(blocks))
    if mutation == "page":
        blocks[0].pages = [0]
    elif mutation == "duplicate_id":
        blocks[1].block_id = "a"
    elif mutation == "asset":
        result.assets = [ExtractedAsset("anchor", "missing", b"png")]
    else:
        blocks[0].boxes = [SourceBox(1, 0, 0, 1000, 10, 300, 400)]
    with pytest.raises(ExtractionError):
        result.validate()


def fake_conversion(*, status="success", missing_image=False, missing_page=False):
    class Box:
        def to_top_left_origin(self, *, page_height):
            assert page_height == 400
            return SimpleNamespace(l=10, t=20, r=100, b=80)

    def item(label, text, page=1):
        return SimpleNamespace(label=label, text=text, self_ref=f"#/{label}",
                               prov=[] if missing_page else [SimpleNamespace(page_no=page, bbox=Box())])

    heading = item("section_header", "דוח")
    table = item("table", "")
    table.prov += [] if missing_page else [SimpleNamespace(page_no=2, bbox=Box())]
    table.data = SimpleNamespace(model_dump=lambda **kwargs: {"num_rows": 1, "table_cells": [
        {"text": "-12.50 USD", "row_span": 1, "col_span": 2, "column_header": False}]})
    table.export_to_markdown = lambda **kwargs: "| Value |\n| -12.50 USD |"
    table.caption_text = lambda **kwargs: "Table 1"
    picture = item("picture", "", 2)
    picture.caption_text = lambda **kwargs: "Figure 1"

    class Image:
        def save(self, stream, *, format):
            assert format == "PNG"
            stream.write(b"synthetic-png")

    picture.get_image = lambda doc: None if missing_image else Image()
    doc = SimpleNamespace(
        pages={n: SimpleNamespace(size=SimpleNamespace(width=300, height=400)) for n in (1, 2)},
        iterate_items=lambda: iter([(heading, 0), (table, 1), (picture, 1)]),
        export_to_dict=lambda: {"synthetic": True},
    )
    return SimpleNamespace(status=status, document=doc, errors=[])


def test_docling_mapping_preserves_tables_locations_and_assets_and_reuses_converter(tmp_path):
    source = pdf(tmp_path / "source.pdf")
    calls = []

    def convert(stream, **kwargs):
        calls.append(stream.read())
        assert kwargs == {"raises_on_error": False, "max_num_pages": 200, "max_file_size": 50 * 1024 * 1024}
        return fake_conversion()

    options = ExtractionOptions()
    adapter = DoclingAdapter(options, converter=SimpleNamespace(convert=convert), versions={"docling": "fake"})
    result = adapter.extract(source, options)
    assert result.status == "completed"
    assert result.blocks[1].pages == [1, 2]
    assert result.blocks[1].payload["table"]["table_cells"][0]["text"] == "-12.50 USD"
    assert result.blocks[1].heading_path == ["דוח"]
    assert result.blocks[1].boxes[0].top == 20
    assert result.assets[0].block_id == result.blocks[2].block_id
    normalized = result.normalized("fixture")
    assert normalized["assets"][0]["file"].startswith("assets/")
    assert result.raw == {"synthetic": True}
    again = adapter.extract(source, options)
    assert len(calls) == 2
    assert normalized == again.normalized("fixture")
    with pytest.raises(ExtractionError, match="fixed"):
        adapter.extract(source, replace(options, max_pages=100))


@pytest.mark.parametrize("case", ["partial_success", "failure", "missing_image", "missing_page"])
def test_docling_failure_and_partial_are_visible(tmp_path, case):
    source = pdf(tmp_path / "source.pdf")
    converted = fake_conversion(status=case if case in {"partial_success", "failure"} else "success",
                                missing_image=case == "missing_image", missing_page=case == "missing_page")
    options = ExtractionOptions()
    adapter = DoclingAdapter(options, converter=SimpleNamespace(convert=lambda *args, **kwargs: converted),
                             versions={"docling": "fake"})
    result = adapter.extract(source, options)
    assert result.status == ("failed" if case == "failure" else "partial")
    if case != "partial_success":
        assert result.warnings


def test_missing_optional_engine_and_unknown_name(monkeypatch):
    import builtins
    original = builtins.__import__

    def no_docling(name, *args, **kwargs):
        if name.startswith("docling."):
            raise ImportError("deliberately unavailable")
        return original(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", no_docling)
    with pytest.raises(ExtractionError, match="Docling is unavailable"):
        create_parser("docling", ExtractionOptions())
    with pytest.raises(ExtractionError, match="Unknown parser"):
        create_parser("automatic-fallback", ExtractionOptions())


def test_docling_factory_requires_local_models_and_disables_remote_features(tmp_path, monkeypatch):
    from app.loaders.pdf_parsers.docling_adapter import _converter
    captured = {}

    class Options(SimpleNamespace):
        def model_dump(self, **kwargs):
            return {"offline": True}

    class Converter:
        def __init__(self, **kwargs):
            captured.update(kwargs)

        def initialize_pipeline(self, input_format):
            captured["initialized"] = input_format

    modules = {
        "docling.datamodel.accelerator_options": {
            "AcceleratorDevice": SimpleNamespace(CPU="cpu"), "AcceleratorOptions": Options},
        "docling.datamodel.base_models": {"InputFormat": SimpleNamespace(PDF="pdf")},
        "docling.datamodel.pipeline_options": {"EasyOcrOptions": Options, "PdfPipelineOptions": Options},
        "docling.document_converter": {"DocumentConverter": Converter, "PdfFormatOption": Options},
    }
    for name, attributes in modules.items():
        module = ModuleType(name)
        module.__dict__.update(attributes)
        monkeypatch.setitem(sys.modules, name, module)
    with pytest.raises(ExtractionError, match="existing local"):
        _converter(ExtractionOptions())
    artifacts = tmp_path / "artifacts"
    artifacts.mkdir()
    with pytest.raises(ExtractionError, match="prepared EasyOCR models"):
        _converter(ExtractionOptions(artifacts_path=str(artifacts), ocr=True))
    ocr_models = tmp_path / "ocr"
    ocr_models.mkdir()
    _, settings = _converter(ExtractionOptions(artifacts_path=str(artifacts), ocr=True,
                                               ocr_languages=("he", "en"), ocr_models_path=str(ocr_models)))
    pipeline = captured["format_options"]["pdf"].pipeline_options
    assert captured["allowed_formats"] == ["pdf"]
    assert captured["initialized"] == "pdf"
    assert pipeline.enable_remote_services is False
    assert pipeline.allow_external_plugins is False
    assert pipeline.do_picture_description is False
    assert pipeline.do_picture_classification is False
    assert pipeline.do_table_structure is True
    assert pipeline.accelerator_options.device == "cpu"
    assert pipeline.ocr_options.download_enabled is False
    assert pipeline.ocr_options.lang == ["he", "en"]
    assert settings == {"offline": True}


@pytest.mark.parametrize("field", ["status", "source_sha256", "references_sha256", "id", "inspection_pages"])
def test_manifest_rejects_unfrozen_or_untrusted_inputs(tmp_path, cli_module, field):
    path = manifest(tmp_path)
    value = json.loads(path.read_text())
    if field == "status":
        value[field] = "template_not_frozen"
    else:
        value["documents"][0][field] = {"source_sha256": "0" * 64, "references_sha256": "0" * 64,
                                         "id": "../escape", "inspection_pages": [0]}[field]
    path.write_text(json.dumps(value))
    with pytest.raises(ExtractionError):
        cli_module.load_manifest(path, ExtractionOptions())


def test_manifest_requires_manually_verified_references(tmp_path, cli_module):
    path = manifest(tmp_path)
    value = json.loads(path.read_text())
    entry = value["documents"][0]
    refs = Path(entry["references_path"])
    reference = json.loads(refs.read_text())
    del reference["verified_by"]
    refs.write_text(json.dumps(reference))
    entry["references_sha256"] = hashlib.sha256(refs.read_bytes()).hexdigest()
    path.write_text(json.dumps(value))
    with pytest.raises(ExtractionError, match="human verification"):
        cli_module.load_manifest(path, ExtractionOptions())


def test_output_refuses_checkout_or_overwrite(private_tmp_path, cli_module):
    tmp_path = private_tmp_path
    with pytest.raises(ExtractionError, match="already exists"):
        cli_module.validate_output(tmp_path)
    with pytest.raises(ExtractionError, match="outside the repository"):
        cli_module.validate_output(ROOT / "private-parser-results")
    checkout = tmp_path / "other-checkout"
    checkout.mkdir()
    (checkout / ".git").write_text("gitdir: elsewhere")
    with pytest.raises(ExtractionError, match="Git checkout"):
        cli_module.validate_output(checkout / "results")


def test_worker_blocks_network_in_isolated_interpreter():
    command = """
import importlib.util, pathlib, socket, sys
path = pathlib.Path(sys.argv[1])
spec = importlib.util.spec_from_file_location('comparison', path)
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
m._offline_worker()
try:
    socket.create_connection(('localhost', 1))
except m.ExtractionError:
    pass
else:
    raise AssertionError('network not blocked')
for prefix in ('docling', 'app.services', 'app.clients', 'app.vectorstores', 'app.config'):
    assert not any(k == prefix or k.startswith(prefix + '.') for k in sys.modules), prefix
"""
    result = subprocess.run([sys.executable, "-c", command, str(ROOT / "scripts/compare_pdf_parsers.py")],
                            capture_output=True, text=True, timeout=20)
    assert result.returncode == 0, result.stderr


def test_cli_real_baseline_cold_and_three_warm_runs(private_tmp_path):
    tmp_path = private_tmp_path
    path = manifest(tmp_path)
    output = tmp_path / "run"
    result = subprocess.run([
        sys.executable, str(ROOT / "scripts/compare_pdf_parsers.py"),
        "--manifest", str(path), "--parsers", "pypdf", "--output", str(output),
    ], capture_output=True, text=True, timeout=60)
    assert result.returncode == 0, result.stderr
    report = json.loads((output / "report.json").read_text())
    assert report["status"] == "completed"
    assert report["quality_status"] == "manual_inspection_pending"
    record = report["documents"][0]
    assert record["initialization_seconds"] >= 0
    assert [run["run"] for run in record["runs"]] == ["cold", "warm-1", "warm-2", "warm-3"]
    cold = json.loads((output / "doc-001/pypdf/cold/normalized.json").read_text())
    for index in range(1, 4):
        assert json.loads((output / f"doc-001/pypdf/warm-{index}/normalized.json").read_text()) == cold
    assert (output / "inspection.md").exists()
    assert (output / "doc-001/references.json").exists()
    assert (output / "doc-001/source.pdf").read_bytes() == (tmp_path / "source.pdf").read_bytes()
    overwrite = subprocess.run([
        sys.executable, str(ROOT / "scripts/compare_pdf_parsers.py"),
        "--manifest", str(path), "--parsers", "pypdf", "--output", str(output),
    ], capture_output=True, text=True, timeout=20)
    assert overwrite.returncode == 1
    assert "refusing to overwrite" in overwrite.stderr


def test_cli_failed_engine_is_recorded_and_nonzero(private_tmp_path):
    tmp_path = private_tmp_path
    path = manifest(tmp_path)
    output = tmp_path / "run"
    result = subprocess.run([
        sys.executable, str(ROOT / "scripts/compare_pdf_parsers.py"),
        "--manifest", str(path), "--parsers", "pypdf", "--output", str(output), "--max-pages", "1",
    ], capture_output=True, text=True, timeout=40)
    assert result.returncode == 1
    report = json.loads((output / "report.json").read_text())
    assert report["status"] == "failed"
    assert "page limit" in report["documents"][0]["runs"][0]["error"]


def test_wait_enforces_timeout_and_memory(cli_module):
    process = SimpleNamespace(pid=123, is_alive=lambda: True)
    connection = SimpleNamespace(poll=lambda timeout: False)
    with pytest.raises(ExtractionError, match="timeout"):
        cli_module.wait_result(connection, process, 0.001, None)
    original = cli_module.process_peak_memory
    cli_module.process_peak_memory = lambda pid: (1024, "fake")
    try:
        with pytest.raises(ExtractionError, match="memory budget"):
            cli_module.wait_result(connection, process, 1, 100)
    finally:
        cli_module.process_peak_memory = original


def test_timeout_terminates_a_real_worker(cli_module):
    import multiprocessing
    context = multiprocessing.get_context("spawn")
    parent, child = context.Pipe()
    process = context.Process(target=time.sleep, args=(30,))
    process.start()
    try:
        with pytest.raises(ExtractionError, match="timeout"):
            cli_module.wait_result(parent, process, 0.1, None)
    finally:
        cli_module._stop(process, parent)
        child.close()
    assert not process.is_alive()

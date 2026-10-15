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
    ExtractionResult, SourceBox, assemble, block_id, create_parser,
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
        iterate_items=lambda *, traverse_pictures=False: iter([(heading, 0), (table, 1), (picture, 1)]),
        export_to_dict=lambda: {"synthetic": True},
    )
    return SimpleNamespace(status=status, document=doc, errors=[])


@pytest.mark.parametrize("table_label", ["table", "document_index"])
def test_docling_mapping_preserves_tables_locations_and_assets_and_reuses_converter(tmp_path, table_label):
    source = pdf(tmp_path / "source.pdf")
    calls = []

    def convert(stream, **kwargs):
        calls.append(stream.read())
        assert kwargs == {"raises_on_error": False, "max_num_pages": 200, "max_file_size": 50 * 1024 * 1024}
        converted = fake_conversion()
        table = list(converted.document.iterate_items())[1][0]
        table.label = table_label
        return converted

    options = ExtractionOptions()
    adapter = DoclingAdapter(options, converter=SimpleNamespace(convert=convert), versions={"docling": "fake"})
    result = adapter.extract(source, options)
    assert result.status == "completed"
    assert result.blocks[1].pages == [1, 2]
    assert result.blocks[1].kind == "table" and result.blocks[1].payload["label"] == table_label
    assert result.blocks[1].source_text == "| Value |\n| -12.50 USD |"
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
    pdfium_options = replace(options, pdf_backend="pypdfium2")
    pdfium = DoclingAdapter(pdfium_options, converter=adapter.converter, versions=adapter.versions)
    pdfium_result = pdfium.extract(source, pdfium_options)
    assert pdfium.identity != adapter.identity
    assert {b.block_id for b in result.blocks}.isdisjoint(b.block_id for b in pdfium_result.blocks)
    assert pdfium_result.assembled_text == result.assembled_text
    with pytest.raises(ExtractionError, match="fixed"):
        adapter.extract(source, replace(options, max_pages=100))


def test_docling_picture_children_retain_searchable_facts_with_provenance(tmp_path):
    source = pdf(tmp_path / "source.pdf")
    converted = fake_conversion()
    parents = list(converted.document.iterate_items())
    child = SimpleNamespace(
        label="text", text="1 קובייה עבור הגרסה למתחילים", self_ref="#/texts/child",
        prov=parents[-1][0].prov,
        parent=SimpleNamespace(cref=parents[-1][0].self_ref,
                               resolve=lambda **kwargs: parents[-1][0]),
    )
    visits = []

    def iterate_items(*, traverse_pictures=False):
        visits.append(traverse_pictures)
        yield from parents
        if traverse_pictures:
            yield child, 2

    converted.document.iterate_items = iterate_items
    options = ExtractionOptions()
    adapter = DoclingAdapter(options, converter=SimpleNamespace(convert=lambda *a, **k: converted),
                             versions={"docling": "fake"})
    result = adapter.extract(source, options)
    assert visits == [True]
    children = [b for b in result.blocks if b.payload["source_ref"] == child.self_ref]
    assert len(children) == 1
    assert children[0].pages == [2] and children[0].boxes[0].page == 2
    assert children[0].payload["picture_parent_ref"] == parents[-1][0].self_ref
    assert children[0].payload["picture_parent_block_id"] == result.assets[0].block_id
    assert "picture_parent_ref" not in result.blocks[0].payload
    assert result.assembled_text[children[0].start:children[0].end] == child.text
    assert result.assets[0].block_id == result.blocks[2].block_id
    legacy_identity = adapter.identity.replace(
        "picture_parent_document_index_export_clamp_pages_without_boxes_v5",
        "picture_children_export_clamp_pages_without_boxes_v4"
    )
    assert all(b.block_id != block_id(result.source_sha256, legacy_identity, b.ordinal)
               for b in result.blocks)
    result.validate()


def test_docling_picture_association_uses_nearest_picture_through_groups(tmp_path):
    converted = fake_conversion()
    items = list(converted.document.iterate_items())
    outer = items[-1][0]
    inner = SimpleNamespace(**vars(outer))
    inner.self_ref = "#/pictures/inner"
    inner.parent = SimpleNamespace(cref=outer.self_ref, resolve=lambda **kwargs: outer)
    group = SimpleNamespace(self_ref="#/groups/inner", label="list",
                            parent=SimpleNamespace(cref=inner.self_ref, resolve=lambda **kwargs: inner))
    child = SimpleNamespace(label="text", text="Graph label", self_ref="#/texts/inner",
                            prov=inner.prov,
                            parent=SimpleNamespace(cref=group.self_ref, resolve=lambda **kwargs: group))
    converted.document.iterate_items = lambda **kwargs: iter(items + [(inner, 2), (child, 4)])
    options = ExtractionOptions()
    adapter = DoclingAdapter(options, converter=SimpleNamespace(convert=lambda *a, **k: converted),
                             versions={"docling": "fake"})
    result = adapter.extract(pdf(tmp_path / "source.pdf"), options)
    assert result.blocks[-1].payload["picture_parent_ref"] == inner.self_ref
    assert result.blocks[-1].payload["picture_parent_block_id"] == result.blocks[-2].block_id
    assert result.blocks[-2].payload["picture_parent_block_id"] == result.blocks[-3].block_id


@pytest.mark.parametrize("defect", ["cycle", "unresolved", "omitted_picture"])
def test_docling_rejects_invalid_picture_parent_associations(tmp_path, defect):
    converted = fake_conversion()
    items = list(converted.document.iterate_items())
    picture = items[-1][0]
    child = SimpleNamespace(label="text", text="Label", self_ref="#/texts/child", prov=picture.prov)
    target = child if defect == "cycle" else None if defect == "unresolved" else picture
    child.parent = SimpleNamespace(cref=child.self_ref if defect == "cycle" else picture.self_ref,
                                   resolve=lambda **kwargs: target)
    visits = items[:-1] if defect == "omitted_picture" else items
    converted.document.iterate_items = lambda **kwargs: iter(visits + [(child, 2)])
    options = ExtractionOptions()
    adapter = DoclingAdapter(options, converter=SimpleNamespace(convert=lambda *a, **k: converted),
                             versions={"docling": "fake"})
    with pytest.raises(ExtractionError, match="parent"):
        adapter.extract(pdf(tmp_path / "source.pdf"), options)


@pytest.mark.parametrize("stage", ["conversion", "export"])
def test_docling_upstream_clamping_keeps_page_text_but_omits_affected_page_boxes(tmp_path, stage):
    import warnings
    source = pdf(tmp_path / "source.pdf")
    def warn():
        warnings.warn("Provenance bbox coordinate l on page 2 is outside page bounds; clamping to 0.0",
                      UserWarning)
    converted = fake_conversion()
    if stage == "export":
        def export():
            warn()
            return {"synthetic": True}
        converted.document.export_to_dict = export
    def convert(*args, **kwargs):
        if stage == "conversion":
            warn()
        return converted
    options = ExtractionOptions()
    adapter = DoclingAdapter(options, converter=SimpleNamespace(convert=convert), versions={"docling": "fake"})
    result = adapter.extract(source, options)
    assert result.status == "partial"
    assert result.blocks[1].pages == [1, 2]
    assert result.blocks[1].source_text
    assert any(box.page == 1 for block in result.blocks for box in block.boxes)
    assert not any(box.page == 2 for block in result.blocks for box in block.boxes)
    assert any("clamping to" in warning for warning in result.warnings)
    assert any("already clamped" in warning for warning in result.warnings)
    assert result.raw == {"synthetic": True}


@pytest.mark.parametrize("top", [-17.1024227575474, float("nan")])
def test_docling_invalid_upstream_box_retains_text_as_explicit_partial(tmp_path, top):
    source = pdf(tmp_path / "source.pdf")
    converted = fake_conversion()
    items = list(converted.document.iterate_items())
    heading = items[0][0]
    heading.prov[0].bbox = SimpleNamespace(
        to_top_left_origin=lambda **kwargs: SimpleNamespace(l=10, t=top, r=100, b=80)
    )
    upstream_raw = {"synthetic": True, "original_top": str(top)}
    converted.document.export_to_dict = lambda: upstream_raw
    options = ExtractionOptions()
    adapter = DoclingAdapter(options, converter=SimpleNamespace(convert=lambda *args, **kwargs: converted),
                             versions={"docling": "fake"})
    result = adapter.extract(source, options)
    assert result.status == "partial"
    assert result.blocks[0].source_text == "דוח"
    assert result.blocks[0].pages == [1]
    assert result.blocks[0].boxes == []
    assert result.blocks[1].boxes  # Valid provenance for other blocks is retained.
    assert any("invalid box on page 1" in warning for warning in result.warnings)
    assert result.raw is upstream_raw
    assert result.settings["normalization_policy"] == "picture_parent_document_index_export_clamp_pages_without_boxes_v5"
    result.normalized("fixture")  # Partial output still meets strict normalized-box validation.


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
        "docling.backend.docling_parse_backend": {
            "ThreadedDoclingParseDocumentBackend": type("ThreadedDoclingParseDocumentBackend", (), {})},
        "docling.backend.pypdfium2_backend": {
            "PyPdfiumDocumentBackend": type("PyPdfiumDocumentBackend", (), {})},
        "docling.datamodel.accelerator_options": {
            "AcceleratorDevice": SimpleNamespace(CPU="cpu"), "AcceleratorOptions": Options},
        "docling.datamodel.base_models": {"InputFormat": SimpleNamespace(PDF="pdf")},
        "docling.datamodel.pipeline_options": {"EasyOcrOptions": Options, "PdfPipelineOptions": Options,
                                              "TesseractCliOcrOptions": Options},
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
    with pytest.raises(ExtractionError, match="prepared local models"):
        _converter(ExtractionOptions(artifacts_path=str(artifacts), ocr=True))
    ocr_models = tmp_path / "ocr"
    ocr_models.mkdir()
    _, settings = _converter(ExtractionOptions(artifacts_path=str(artifacts), ocr=True,
                                               ocr_languages=("en",), ocr_models_path=str(ocr_models)))
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
    assert pipeline.ocr_options.lang == ["en"]
    assert settings == {"offline": True, "pdf_backend": {
        "selection": "docling_parse", "class": "ThreadedDoclingParseDocumentBackend"}}
    _, pdfium_settings = _converter(ExtractionOptions(artifacts_path=str(artifacts), pdf_backend="pypdfium2"))
    assert captured["format_options"]["pdf"].backend.__name__ == "PyPdfiumDocumentBackend"
    assert pdfium_settings["pdf_backend"] == {"selection": "pypdfium2", "class": "PyPdfiumDocumentBackend"}
    with pytest.raises(ExtractionError, match="supported PDF backend"):
        ExtractionOptions(pdf_backend="automatic-fallback")
    def fail_initialization(self, input_format):
        raise RuntimeError("selected backend failed")
    with monkeypatch.context() as scoped:
        scoped.setattr(Converter, "initialize_pipeline", fail_initialization)
        with pytest.raises(ExtractionError, match="selected backend failed"):
            _converter(ExtractionOptions(artifacts_path=str(artifacts), pdf_backend="pypdfium2"))
        assert captured["format_options"]["pdf"].backend.__name__ == "PyPdfiumDocumentBackend"
    with pytest.raises(ExtractionError, match="does not support Hebrew"):
        _converter(ExtractionOptions(artifacts_path=str(artifacts), ocr=True,
                                     ocr_languages=("he", "en"), ocr_models_path=str(ocr_models)))
    native_options = ExtractionOptions(artifacts_path=str(artifacts), ocr=True,
                                       ocr_engine="tesseract", ocr_languages=("heb", "eng"),
                                       ocr_models_path=str(ocr_models))
    with pytest.raises(ExtractionError, match="ocr-executable"):
        _converter(native_options)
    native = tmp_path / "tesseract.exe"
    native.write_bytes(b"fake-native-executable")
    native_options = replace(native_options, ocr_executable=str(native))
    with pytest.raises(ExtractionError, match="Missing prepared Tesseract"):
        _converter(native_options)
    for language in ("heb", "eng"):
        (ocr_models / f"{language}.traineddata").write_bytes(language.encode())
    with pytest.raises(ExtractionError, match="auxiliary artifact"):
        _converter(native_options)
    (ocr_models / "osd.traineddata").write_bytes(b"fake-orientation-model")
    (ocr_models / "configs").mkdir()
    (ocr_models / "configs/tsv").write_bytes(b"tessedit_create_tsv 1")
    _, native_settings = _converter(native_options)
    pipeline = captured["format_options"]["pdf"].pipeline_options
    assert pipeline.ocr_options.lang == ["heb", "eng"]
    assert pipeline.ocr_options.tesseract_cmd == str(native)
    assert pipeline.ocr_options.path == str(ocr_models)
    assert native_settings["native_ocr_sha256"]["executable"] == hashlib.sha256(native.read_bytes()).hexdigest()
    with pytest.raises(ExtractionError, match="Missing prepared Tesseract"):
        _converter(replace(native_options, ocr_languages=("../eng",)))


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


def test_worker_exports_exact_utf8_text_with_embedded_carriage_returns(tmp_path, monkeypatch, cli_module):
    block = ExtractionBlock(block_id="synthetic", ordinal=0, kind="text",
                            source_text="A\rB\r\nC\nשלום -12.50", pages=[1])
    result = ExtractionResult(source_sha256=hashlib.sha256(b"synthetic").hexdigest(),
                              page_count=1, engine="docling", versions={}, settings={},
                              blocks=[block], assembled_text=assemble([block]), raw={})
    output = tmp_path / "cold"
    requests = iter([(tmp_path / "unused.pdf", output, "synthetic", result.source_sha256), None])
    sent = []
    connection = SimpleNamespace(recv=lambda: next(requests), send=sent.append, close=lambda: None)
    monkeypatch.setattr(cli_module, "_offline_worker", lambda: None)
    monkeypatch.setattr(cli_module, "create_parser", lambda *args: SimpleNamespace(extract=lambda *args: result))
    monkeypatch.setattr(cli_module, "process_peak_memory", lambda pid: (1, "synthetic"))
    cli_module._worker(connection, "docling", ExtractionOptions())
    assert sent[-1]["status"] == "completed"
    assert (output / "text.txt").read_bytes() == result.assembled_text.encode("utf-8")
    normalized = json.loads((output / "normalized.json").read_text(encoding="utf-8"))
    text = (output / "text.txt").read_bytes().decode("utf-8")
    assert text[block.start:block.end] == normalized["blocks"][0]["source_text"]


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


def test_wait_rejects_over_budget_native_job_peak(cli_module):
    process = SimpleNamespace(pid=123, is_alive=lambda: True)
    connection = SimpleNamespace(poll=lambda timeout: False)
    job = SimpleNamespace(peak_commit=lambda: 1024)
    with pytest.raises(ExtractionError, match="process-tree peak commit"):
        cli_module.wait_result(connection, process, 1, 100, job)


def test_wait_records_native_crash_exit_code(cli_module):
    def closed_pipe():
        raise EOFError
    process = SimpleNamespace(join=lambda **kwargs: None, exitcode=-1073741819)
    connection = SimpleNamespace(poll=lambda timeout: True, recv=closed_pipe)
    with pytest.raises(ExtractionError, match="exit code -1073741819"):
        cli_module.wait_result(connection, process, 1, None)


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


@pytest.mark.skipif(sys.platform != "win32", reason="Windows native process-tree control")
@pytest.mark.parametrize("mode", ["cleanup", "memory_limit"])
def test_native_job_controls_descendants(private_tmp_path, cli_module, mode):
    gate = private_tmp_path / "start"
    output = private_tmp_path / "child-result"
    child_code = "import time; time.sleep(30)" if mode == "cleanup" else (
        "try:\n b=bytearray(256*1024*1024)\n print('allocated')\n"
        "except MemoryError:\n print('limited')\n"
    )
    script = """
import pathlib, subprocess, sys, time
gate, output = map(pathlib.Path, sys.argv[1:3])
while not gate.exists(): time.sleep(0.01)
if sys.argv[3] == 'cleanup':
    child = subprocess.Popen([sys.executable, '-c', sys.argv[4]])
    output.write_text(str(child.pid))
else:
    child = subprocess.run([sys.executable, '-c', sys.argv[4]], capture_output=True, text=True)
    output.write_text(child.stdout.strip() or child.stderr)
time.sleep(30)
"""
    process = subprocess.Popen([sys.executable, "-c", script, str(gate), str(output), mode, child_code])
    job = None
    child_handle = None
    try:
        job = cli_module.WindowsWorkerJob(process.pid, 128 * 1024 * 1024)
        gate.write_text("ready")
        deadline = time.monotonic() + 10
        while not output.exists() and time.monotonic() < deadline:
            time.sleep(0.01)
        assert output.exists(), "Native child did not report"
        assert job.peak_commit() > 0
        if mode == "memory_limit":
            assert output.read_text() == "limited", "Native child bypassed the job memory ceiling"
        else:
            import ctypes
            from ctypes import wintypes
            kernel = ctypes.WinDLL("kernel32", use_last_error=True)
            kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
            kernel.OpenProcess.restype = wintypes.HANDLE
            kernel.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
            kernel.CloseHandle.argtypes = [wintypes.HANDLE]
            child_handle = kernel.OpenProcess(0x00100000, False, int(output.read_text()))
            assert child_handle
        job.close()
        process.wait(timeout=5)
        if child_handle:
            assert kernel.WaitForSingleObject(child_handle, 5000) == 0, "Native child survived worker cleanup"
    finally:
        if job:
            job.close()
        if process.poll() is None:
            process.kill()
            process.wait(timeout=5)
        if child_handle:
            kernel.CloseHandle(child_handle)

"""Map Docling output into the experiment contract without production wiring."""

from __future__ import annotations

from dataclasses import asdict
import hashlib
from importlib.metadata import PackageNotFoundError, version
from io import BytesIO
import json
import math
import re
import warnings as python_warnings
from pathlib import Path

from app.loaders.pdf_extraction import (
    ExtractedAsset, ExtractionBlock, ExtractionError, ExtractionOptions,
    ExtractionResult, SourceBox, assemble, block_id, read_source,
)


def _converter(options: ExtractionOptions):
    try:
        from docling.datamodel.accelerator_options import AcceleratorDevice, AcceleratorOptions
        from docling.datamodel.base_models import InputFormat
        from docling.datamodel.pipeline_options import EasyOcrOptions, PdfPipelineOptions
        from docling.document_converter import DocumentConverter, PdfFormatOption
        if options.pdf_backend == "pypdfium2":
            from docling.backend.pypdfium2_backend import PyPdfiumDocumentBackend as backend
        else:
            from docling.backend.docling_parse_backend import ThreadedDoclingParseDocumentBackend as backend
    except ImportError as exc:
        raise ExtractionError("Docling is unavailable; prepare the optional pdf-experiment environment") from exc
    if not options.artifacts_path or not Path(options.artifacts_path).is_dir():
        raise ExtractionError("Docling requires an existing local --artifacts-path; downloads are disabled")
    if options.ocr and (not options.ocr_models_path or not Path(options.ocr_models_path).is_dir()):
        raise ExtractionError("OCR requires prepared local models via --ocr-models-path")
    pipeline = PdfPipelineOptions(
        artifacts_path=Path(options.artifacts_path), do_ocr=options.ocr,
        enable_remote_services=False, allow_external_plugins=False,
        do_picture_description=False, do_picture_classification=False,
        generate_picture_images=True, generate_page_images=True,
        do_table_structure=True,
        accelerator_options=AcceleratorOptions(device=AcceleratorDevice.CPU, num_threads=1),
    )
    if options.ocr:
        if options.ocr_engine == "easyocr":
            if any(lang in {"he", "heb", "iw"} for lang in options.ocr_languages):
                raise ExtractionError("EasyOCR 1.7.2 does not support Hebrew; select tesseract with heb eng")
            pipeline.ocr_options = EasyOcrOptions(
                lang=list(options.ocr_languages), use_gpu=False, download_enabled=False,
                model_storage_directory=options.ocr_models_path,
            )
        else:
            from docling.datamodel.pipeline_options import TesseractCliOcrOptions
            if not options.ocr_executable or not Path(options.ocr_executable).is_file():
                raise ExtractionError("Tesseract requires an explicit existing --ocr-executable")
            for language in options.ocr_languages:
                if not re.fullmatch(r"[A-Za-z0-9_]+", language) or not (
                    Path(options.ocr_models_path) / f"{language}.traineddata"
                ).is_file():
                    raise ExtractionError(f"Missing prepared Tesseract language model: {language}")
            for auxiliary in ("osd.traineddata", "configs/tsv"):
                if not (Path(options.ocr_models_path) / auxiliary).is_file():
                    raise ExtractionError(f"Missing prepared Tesseract auxiliary artifact: {auxiliary}")
            pipeline.ocr_options = TesseractCliOcrOptions(
                lang=list(options.ocr_languages), tesseract_cmd=options.ocr_executable,
                path=options.ocr_models_path,
            )
    converter = DocumentConverter(
        allowed_formats=[InputFormat.PDF],
        format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline, backend=backend)},
    )
    try:
        converter.initialize_pipeline(InputFormat.PDF)
    except Exception as exc:
        raise ExtractionError(f"Docling initialization failed; verify prepared local models: {exc}") from exc
    settings = pipeline.model_dump(mode="json")
    settings["pdf_backend"] = {"selection": options.pdf_backend, "class": backend.__name__}
    if options.ocr and options.ocr_engine == "tesseract":
        paths = {"executable": Path(options.ocr_executable)}
        paths.update({lang: Path(options.ocr_models_path) / f"{lang}.traineddata"
                      for lang in options.ocr_languages})
        paths.update({name: Path(options.ocr_models_path) / name for name in ("osd.traineddata", "configs/tsv")})
        settings["native_ocr_sha256"] = {
            name: hashlib.sha256(path.read_bytes()).hexdigest() for name, path in paths.items()
        }
    return converter, settings


def _versions() -> dict[str, str]:
    names = ("docling", "docling-slim", "docling-core", "docling-parse", "pypdfium2", "docling-ibm-models", "torch", "easyocr")
    result = {}
    for name in names:
        try:
            result[name] = version(name)
        except PackageNotFoundError:
            pass
    return result


class DoclingAdapter:
    def __init__(self, options: ExtractionOptions, *, converter=None, versions=None):
        self.options = options
        if converter is None:
            self.converter, pipeline_settings = _converter(options)
        else:
            self.converter, pipeline_settings = converter, {"test_converter": True}
        self.versions = versions if versions is not None else _versions()
        self.settings = {"options": asdict(options), "effective_pipeline": pipeline_settings,
                         "normalization_policy": "picture_parent_document_index_export_clamp_pages_without_boxes_v5"}
        self.identity = json.dumps({"versions": self.versions, "settings": self.settings}, sort_keys=True)

    def extract(self, path: Path, options: ExtractionOptions) -> ExtractionResult:
        # Exporters can validate/clamp document copies after conversion returns.
        with python_warnings.catch_warnings(record=True) as upstream_warnings:
            python_warnings.simplefilter("always")
            result = self._extract(path, options)
        result.warnings.extend(f"Docling upstream warning: {warning.message}" for warning in upstream_warnings)
        clamped_pages = set()
        for warning in upstream_warnings:
            match = re.search(r"(?:Provenance|Table cell) bbox coordinate .* on page (\d+).*clamping to",
                              str(warning.message))
            if match:
                clamped_pages.add(int(match.group(1)))
        if clamped_pages:
            result.status = "partial" if result.status == "completed" else result.status
            for block in result.blocks:
                block.boxes = [box for box in block.boxes if box.page not in clamped_pages]
            result.warnings.extend(
                f"Page {page}: upstream coordinates already clamped; normalized boxes omitted; "
                "text/page identity retained and raw output contains the upstream clamped coordinates"
                for page in sorted(clamped_pages)
            )
        result.validate()
        return result

    def _extract(self, path: Path, options: ExtractionOptions) -> ExtractionResult:
        if options != self.options:
            raise ExtractionError("Parser options must remain fixed within a run")
        content, sha256 = read_source(path, options)
        # Docling accepts a stream; URL/path loading is deliberately avoided.
        if type(self.converter).__module__.startswith("docling."):
            from docling.datamodel.base_models import DocumentStream
            source = DocumentStream(name="source.pdf", stream=BytesIO(content))
        else:
            source = BytesIO(content)  # fake converters used by offline contract tests
        converted = self.converter.convert(
            source, raises_on_error=False, max_num_pages=options.max_pages, max_file_size=options.max_bytes,
        )
        status = getattr(converted.status, "value", converted.status)
        normalized_status = {"success": "completed", "partial_success": "partial"}.get(status, "failed")
        document = converted.document
        pages = document.pages
        page_count = max(pages, default=0)
        if page_count > options.max_pages:
            raise ExtractionError(f"PDF exceeds {options.max_pages} page limit")
        warnings = [str(error) for error in converted.errors]
        blocks: list[ExtractionBlock] = []
        assets: list[ExtractedAsset] = []
        headings: list[tuple[int, str]] = []
        # Diagram labels and even list/table content can be nested under pictures.
        # Docling's default iterator visits captions but skips those other children.
        for item, depth in document.iterate_items(traverse_pictures=True):
            label = getattr(item.label, "value", item.label)
            kind = {"table": "table", "document_index": "table", "picture": "image",
                    "formula": "equation"}.get(label, "text")
            if label in {"section_header", "title"}:
                heading_level = getattr(item, "level", depth)
                headings = [(level, text) for level, text in headings if level < heading_level]
                headings.append((heading_level, getattr(item, "text", "")))
            ordinal = len(blocks)
            block = ExtractionBlock(
                block_id=block_id(sha256, self.identity, ordinal), ordinal=ordinal,
                kind=kind, source_text=getattr(item, "text", "") or "",
                pages=sorted({prov.page_no for prov in item.prov}),
                heading_path=[text for _, text in headings],
                payload={"source_ref": item.self_ref, "label": label},
            )
            ancestor = item
            seen = {item.self_ref}
            while parent := getattr(ancestor, "parent", None):
                if parent.cref in seen:
                    raise ExtractionError(f"Cyclic Docling parent reference: {parent.cref}")
                seen.add(parent.cref)
                try:
                    ancestor = parent.resolve(doc=document)
                except (AttributeError, IndexError, KeyError, ValueError) as exc:
                    raise ExtractionError(f"Unresolved Docling parent reference: {parent.cref}") from exc
                if ancestor is None:
                    raise ExtractionError(f"Unresolved Docling parent reference: {parent.cref}")
                ancestor_label = getattr(ancestor, "label", None)
                if getattr(ancestor_label, "value", ancestor_label) == "picture":
                    block.payload["picture_parent_ref"] = ancestor.self_ref
                    break
            if not block.pages:
                warnings.append(f"Block {ordinal} has no page provenance")
                normalized_status = "partial" if normalized_status == "completed" else normalized_status
            for prov in item.prov:
                page = pages.get(prov.page_no)
                if page is None or page.size is None:
                    warnings.append(f"Block {ordinal}: missing page dimensions")
                    normalized_status = "partial" if normalized_status == "completed" else normalized_status
                    continue
                box = prov.bbox.to_top_left_origin(page_height=page.size.height)
                coordinates = (box.l, box.t, box.r, box.b, page.size.width, page.size.height)
                if not all(math.isfinite(value) for value in coordinates) or not (
                    0 <= box.l <= box.r <= page.size.width
                    and 0 <= box.t <= box.b <= page.size.height
                ):
                    warnings.append(
                        f"Block {ordinal}: invalid box on page {prov.page_no}; "
                        "omitted from normalized boxes; upstream coordinates retained in raw output"
                    )
                    normalized_status = "partial" if normalized_status == "completed" else normalized_status
                    continue
                block.boxes.append(SourceBox(
                    page=prov.page_no, left=box.l, top=box.t, right=box.r, bottom=box.b,
                    page_width=page.size.width, page_height=page.size.height,
                ))
            if kind == "table":
                block.payload["table"] = item.data.model_dump(mode="json")
                if not block.payload["table"].get("table_cells"):
                    warnings.append(f"Block {ordinal}: table cells unavailable")
                    normalized_status = "partial" if normalized_status == "completed" else normalized_status
                # Preserve cell text/spans in raw payload; deterministic markdown is searchable text.
                block.source_text = item.export_to_markdown(doc=document)
            if kind in {"image", "table"}:
                block.payload["caption"] = item.caption_text(doc=document)
            if kind == "image":
                image = item.get_image(document)
                if image is None:
                    warnings.append(f"Block {ordinal}: picture bytes unavailable")
                    normalized_status = "partial" if normalized_status == "completed" else normalized_status
                else:
                    stream = BytesIO()
                    image.save(stream, format="PNG")
                    data = stream.getvalue()
                    block.asset_anchor = f"{block.block_id}:{hashlib.sha256(data).hexdigest()}"
                    assets.append(ExtractedAsset(block.asset_anchor, block.block_id, data))
            blocks.append(block)
        by_ref = {block.payload["source_ref"]: block for block in blocks}
        for block in blocks:
            if parent_ref := block.payload.get("picture_parent_ref"):
                parent_block = by_ref.get(parent_ref)
                if parent_block is None or parent_block.kind != "image":
                    raise ExtractionError(f"Picture parent missing from normalized blocks: {parent_ref}")
                block.payload["picture_parent_block_id"] = parent_block.block_id
        result = ExtractionResult(
            source_sha256=sha256, page_count=page_count, engine="docling",
            versions=self.versions, settings=self.settings, blocks=blocks,
            status=normalized_status, warnings=warnings, assets=assets,
            unsupported=[] if options.ocr else ["ocr_disabled"],
            assembled_text=assemble(blocks), raw=document.export_to_dict(),
        )
        if normalized_status == "failed" and not warnings:
            result.warnings.append(f"Docling conversion status: {status}")
        result.validate()
        return result

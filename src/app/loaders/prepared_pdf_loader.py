"""Validate prepared, private extraction artifacts without importing PDF models."""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import re

from app.chunkers.ids import make_doc_id
from app.domain.models import Document, DocumentAsset, SourceType
from app.loaders.pdf_extraction import ExtractionBlock, ExtractionOptions, ExtractionResult, SourceBox, read_source

V5_POLICY = "picture_parent_document_index_export_clamp_pages_without_boxes_v5"
TREATMENTS = {"pypdf": "pypdf", "docling-noocr": "docling", "docling-ocr": "docling"}


def canonical_hash(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                     separators=(",", ":"), allow_nan=False).encode("utf8")).hexdigest()


def _read_json(path: Path, limit: int = 64 * 1024 * 1024):
    with path.open("rb") as stream:
        content = stream.read(limit + 1)
    if len(content) > limit:
        raise ValueError("Extraction artifact exceeds byte limit")
    value = json.loads(content)
    if not isinstance(value, dict):
        raise ValueError("Extraction artifact must be an object")
    return value


class ExtractionPending(ValueError):
    """Explicit dry-run outcome; no parser or model is invoked to resolve it."""


class PreparedPDFLoader:
    def __init__(self, manifest_path: Path, run_root: Path | None, treatment: str,
                 *, max_asset_bytes: int = 15 * 1024 * 1024,
                 max_assets: int = 100, max_total_asset_bytes: int = 100 * 1024 * 1024) -> None:
        if treatment not in TREATMENTS:
            raise ValueError("Unknown PDF treatment")
        self.treatment = treatment
        self.engine = TREATMENTS[treatment]
        self.max_asset_bytes = max_asset_bytes
        self.max_assets = max_assets
        self.max_total_asset_bytes = max_total_asset_bytes
        self.errors: list[dict] = []
        self.manifest_path = manifest_path.resolve()
        manifest_bytes = self.manifest_path.read_bytes()
        self.manifest_hash = hashlib.sha256(manifest_bytes).hexdigest()
        self.manifest = json.loads(manifest_bytes)
        if not isinstance(self.manifest, dict):
            raise ValueError("Manifest must be an object")
        if self.manifest.get("schema_version") != 1 or self.manifest.get("status") != "frozen":
            raise ValueError("Frozen extraction manifest required")
        entries = self.manifest.get("documents", [])
        if not entries:
            raise ValueError("Manifest requires documents")
        self.entries = {}
        ids = set()
        for entry in entries:
            doc_id = entry["id"]
            path = Path(entry["source_path"])
            reference_path = Path(entry["references_path"])
            if (not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}", doc_id) or doc_id in ids
                    or not path.is_absolute() or str(path).startswith(("\\\\", "//"))
                    or not reference_path.is_absolute() or str(reference_path).startswith(("\\\\", "//"))):
                raise ValueError("Invalid manifest document identity/path")
            key = path.resolve()
            if key in self.entries:
                raise ValueError("Duplicate manifest source path")
            ids.add(doc_id)
            self.entries[key] = entry
        self.root = run_root.resolve() if run_root is not None else None
        self.records = {}
        if self.root is not None:
            if any((p / ".git").exists() for p in (self.root, *self.root.parents)):
                raise ValueError("Prepared private results must be outside Git checkouts")
            report = _read_json(self.root / "report.json")
            if (report.get("format_version") != 1 or report.get("status") not in {"completed", "failed"}
                    or report.get("error") or report.get("manifest_sha256") != self.manifest_hash
                    or report.get("warm_runs", 0) < 3):
                raise ValueError("Finished matching extraction report required")
            for record in report["documents"]:
                if record["engine"] == self.engine:
                    if record["document_id"] in self.records:
                        raise ValueError("Duplicate extraction report document")
                    self.records[record["document_id"]] = record
            if set(self.records) != ids:
                raise ValueError("Extraction report does not cover the frozen manifest")
            self.run_settings = report["settings"]
            if (report.get("timeout_seconds", 0) > 180 or self.run_settings.get("max_bytes", 0) > 50 * 1024 * 1024
                    or self.run_settings.get("max_pages", 0) > 200
                    or (self.engine == "docling" and not 0 < report.get("memory_limit_mib", 0) <= 8192)):
                raise ValueError("Extraction exceeds approved resource budgets")

    def load(self, source_path: str) -> Document:
        try:
            return self._load(source_path)
        except (OSError, ValueError, KeyError, TypeError) as exc:
            self.errors.append({"path": source_path, "reason": str(exc),
                                "extraction_pending": isinstance(exc, ExtractionPending)})
            raise

    def _load(self, source_path: str) -> Document:
        source = Path(source_path).resolve()
        entry = self.entries.get(source)
        if entry is None:
            raise ValueError("Source is outside the permitted frozen manifest")
        _, sha = read_source(source, ExtractionOptions())
        if sha != entry["source_sha256"]:
            raise ValueError("Source hash changed after freeze")
        references = Path(entry["references_path"])
        with references.open("rb") as stream:
            reference_bytes = stream.read(10 * 1024 * 1024 + 1)
        if len(reference_bytes) > 10 * 1024 * 1024 or hashlib.sha256(reference_bytes).hexdigest() != entry["references_sha256"]:
            raise ValueError("Reference hash changed after freeze")
        if self.root is None:
            raise ExtractionPending("Extraction pending: supply a completed prepared run; dry-run invokes no models")
        record = self.records[entry["id"]]
        if record["status"] != "completed" or len(record.get("runs", [])) < 4:
            raise ValueError(f"Extraction not publishable: {record['status']}")
        if any(r.get("status") != "completed" for r in record["runs"]):
            raise ValueError("Extraction cold/warm acceptance failed")
        folder = (self.root / entry["id"] / self.engine / "cold").resolve()
        if not folder.is_relative_to(self.root):
            raise ValueError("Extraction directory escapes private run")
        normalized_path = (folder / "normalized.json").resolve()
        if not normalized_path.is_relative_to(folder):
            raise ValueError("Normalized artifact escapes extraction directory")
        normalized = _read_json(normalized_path)
        if (normalized.get("format_version") != 1 or normalized.get("document_id") != entry["id"]
                or normalized.get("source_sha256") != sha or normalized.get("engine") != self.engine
                or normalized.get("status") != "completed"):
            raise ValueError("Normalized extraction identity/status mismatch")
        if type(normalized["page_count"]) is not int or not 0 < normalized["page_count"] <= 200:
            raise ValueError("Invalid extraction page count")
        run_names = [r["run"] for r in record["runs"]]
        if (len(set(run_names)) != len(run_names) or not {"cold", "warm-1", "warm-2", "warm-3"} <= set(run_names)
                or any(not re.fullmatch(r"cold|warm-[1-9][0-9]*", name) for name in run_names)):
            raise ValueError("Missing/invalid cold and warm run identities")
        for name in run_names:
            if name == "cold":
                continue
            warm_path = (folder.parent / name / "normalized.json").resolve()
            if not warm_path.is_relative_to(folder.parent):
                raise ValueError("Warm artifact escapes extraction directory")
            warm = _read_json(warm_path)
            if any(warm.get(key) != normalized.get(key) for key in (
                    "status", "document_id", "source_sha256", "engine", "page_count", "versions", "settings",
                    "assembled_text", "blocks", "assets")):
                raise ValueError("Cold/warm extraction content or identity is unstable")
        settings = normalized["settings"]
        if settings["options"] != self.run_settings:
            raise ValueError("Normalized settings differ from extraction report")
        if self.engine == "docling":
            options = settings["options"]
            if (settings.get("normalization_policy") != V5_POLICY or options.get("pdf_backend") != "pypdfium2"
                    or options.get("ocr") is not (self.treatment == "docling-ocr")):
                raise ValueError("Docling normalization/treatment mismatch")
            if options.get("ocr") and (options.get("ocr_engine") != "tesseract"
                                       or options.get("ocr_languages") != ["heb", "eng"]):
                raise ValueError("Prepared Hebrew/English Tesseract treatment required")
        blocks = []
        for b in normalized["blocks"]:
            if (any(type(b[k]) is not int for k in ("ordinal", "start", "end")) or not b["pages"]
                    or not re.fullmatch(r"[0-9a-f]{64}", b["block_id"])):
                raise ValueError("Invalid block offsets/page provenance")
            boxes = [SourceBox(**box) for box in b["boxes"]]
            if any(not all(math.isfinite(v) for v in (box.left, box.top, box.right, box.bottom,
                                                      box.page_width, box.page_height)) for box in boxes):
                raise ValueError("Nonfinite source geometry")
            if self.engine == "pypdf":
                b = {**b, "payload": {**b["payload"], "source_ref": f"#/pages/{b['pages'][0]}"}}
            blocks.append(ExtractionBlock(**{**b, "boxes": boxes}))
        result = ExtractionResult(source_sha256=sha, page_count=normalized["page_count"],
                                  engine=self.engine, versions=normalized["versions"], settings=settings,
                                  blocks=blocks, assembled_text=normalized["assembled_text"])
        # Validate offsets and geometry; assets are validated separately before bytes are read.
        anchors = [b.asset_anchor for b in blocks]
        for block in blocks:
            block.asset_anchor = None
        result.validate()
        for block, anchor in zip(blocks, anchors):
            block.asset_anchor = anchor
        normalized["blocks"] = [{**b, "payload": block.payload} for b, block in zip(normalized["blocks"], blocks)]
        by_id = {b.block_id: b for b in blocks}
        refs = [b.payload.get("source_ref") for b in blocks]
        if len(set(refs)) != len(refs) or any(not isinstance(ref, str) for ref in refs):
            raise ValueError("Missing/duplicate extraction source reference")
        for block in blocks:
            seen = {block.block_id}
            node = block
            if bool(node.payload.get("picture_parent_ref")) != bool(node.payload.get("picture_parent_block_id")):
                raise ValueError("Incomplete picture parent association")
            while parent_id := node.payload.get("picture_parent_block_id"):
                parent = by_id.get(parent_id)
                if (parent is None or parent_id in seen or parent.kind != "image"
                        or parent.payload["source_ref"] != node.payload.get("picture_parent_ref")
                        or not set(node.pages) <= set(parent.pages)):
                    raise ValueError("Invalid picture parent association")
                seen.add(parent_id)
                node = parent
        assets = []
        asset_anchors = set()
        total_asset_bytes = 0
        if len(normalized["assets"]) > self.max_assets:
            raise ValueError("Extraction exceeds image count limit")
        for asset in normalized["assets"]:
            digest = asset["sha256"]
            block = by_id.get(asset["block_id"])
            if (not re.fullmatch(r"[0-9a-f]{64}", digest) or asset["media_type"] != "image/png"
                    or block is None or block.kind != "image" or block.asset_anchor != asset["anchor"]
                    or asset["anchor"] in asset_anchors):
                raise ValueError("Invalid asset metadata/linkage")
            filename = (folder / asset["file"]).resolve()
            if not filename.is_relative_to(folder):
                raise ValueError("Asset path escapes extraction directory")
            with filename.open("rb") as stream:
                content = stream.read(self.max_asset_bytes + 1)
            if (len(content) > self.max_asset_bytes or hashlib.sha256(content).hexdigest() != digest
                    or not content.startswith(b"\x89PNG\r\n\x1a\n")):
                raise ValueError("Asset byte size/hash/media mismatch")
            total_asset_bytes += len(content)
            if total_asset_bytes > self.max_total_asset_bytes:
                raise ValueError("Extraction exceeds total image byte limit")
            asset_anchors.add(asset["anchor"])
            assets.append(DocumentAsset(anchor_id=asset["anchor"], relationship_id=block.payload["source_ref"],
                                        content=content, content_hash=digest, media_type="image/png",
                                        original_name=digest + ".png", ordinal=len(assets),
                                        block_id=block.block_id, block_ordinal=block.ordinal,
                                        source_index=block.start, caption=block.payload.get("caption")))
        if {a for a in anchors if a} != asset_anchors:
            raise ValueError("Block references a missing asset")
        identity = canonical_hash({"source_sha256": sha, "format_version": 1,
                                   "versions": result.versions, "settings": settings,
                                   "text_sha256": hashlib.sha256(result.assembled_text.encode("utf8")).hexdigest(),
                                   "blocks": normalized["blocks"], "assets": normalized["assets"]})
        return Document(doc_id=make_doc_id(str(source)), source_path=str(source), source_type=SourceType.pdf,
                        content=result.assembled_text, title=source.stem, assets=assets,
                        metadata={"source_sha256": sha, "total_pages": result.page_count,
                                  "pdf_treatment": self.treatment, "extraction_fingerprint": identity,
                                  "extraction_status": "completed", "_pdf_blocks": normalized["blocks"]})


def _intersects(document: Document, block: dict, start: int, end: int) -> bool:
    if (block["start"] < end and start < block["end"]
            or block["start"] == block["end"] and start <= block["start"] < end):
        return True
    # Empty scanned pages still have an explicit assembler-generated page marker.
    marker = f"[PAGE {block['pages'][0]}]\n"
    marker_start = block["start"] - len(marker)
    return (marker_start >= 0 and document.content[marker_start:block["start"]] == marker
            and marker_start < end and start < block["start"])


def pdf_chunk_provenance(document: Document, start: int | None, end: int | None) -> dict:
    blocks = document.metadata.get("_pdf_blocks")
    if blocks is None:
        return {}
    if start is None or end is None:
        raise ValueError("PDF experiment chunker must preserve source offsets")
    selected = [b for b in blocks if _intersects(document, b, start, end)]
    pages = sorted({p for b in selected for p in b["pages"]})
    return {"page": pages[0] if pages else None, "source_pages": pages,
            "extraction_blocks": [{k: b[k] for k in ("block_id", "kind", "start", "end", "pages", "boxes", "payload")}
                                  for b in selected]}


def pdf_asset_chunk_indexes(document: Document, asset: DocumentAsset, chunks: list[tuple[int, object]]) -> list[int]:
    blocks = document.metadata["_pdf_blocks"]
    by_id = {b["block_id"]: b for b in blocks}
    ranges = []
    for block in blocks:
        node = block
        while node is not None:
            if node["block_id"] == asset.block_id:
                ranges.append((block["start"], block["end"]))
                break
            node = by_id.get(node["payload"].get("picture_parent_block_id"))
    return [index for index, chunk in chunks
            if chunk.start_index is not None and chunk.end_index is not None
            and any((start < chunk.end_index and chunk.start_index < end) if start != end
                    else chunk.start_index <= start < chunk.end_index for start, end in ranges)]

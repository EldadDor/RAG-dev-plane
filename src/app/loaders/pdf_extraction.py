"""Internal, provider-free contract for extraction experiments (not ingestion)."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import hashlib
from pathlib import Path
from typing import Literal

FORMAT_VERSION = 1


class ExtractionError(ValueError):
    """An explicit extraction/preparation failure; never triggers fallback."""


@dataclass(frozen=True)
class ExtractionOptions:
    max_bytes: int = 50 * 1024 * 1024
    max_pages: int = 200
    artifacts_path: str | None = None
    ocr: bool = False
    ocr_languages: tuple[str, ...] = ("en",)
    ocr_models_path: str | None = None
    ocr_engine: Literal["easyocr", "tesseract"] = "easyocr"
    ocr_executable: str | None = None
    pdf_backend: Literal["docling_parse", "pypdfium2"] = "docling_parse"

    def __post_init__(self) -> None:
        if self.max_bytes <= 0 or self.max_pages <= 0:
            raise ExtractionError("File/page limits must be positive")
        if not self.ocr_languages or any(not value.strip() for value in self.ocr_languages):
            raise ExtractionError("Specify nonempty OCR language codes")
        if self.ocr_engine not in {"easyocr", "tesseract"}:
            raise ExtractionError("Specify an explicit supported OCR engine")
        if self.pdf_backend not in {"docling_parse", "pypdfium2"}:
            raise ExtractionError("Specify an explicit supported PDF backend")


@dataclass
class SourceBox:
    page: int
    left: float
    top: float
    right: float
    bottom: float
    page_width: float
    page_height: float
    units: str = "pdf_points"
    origin: str = "top_left"


@dataclass
class ExtractionBlock:
    block_id: str
    ordinal: int
    kind: Literal["text", "table", "image", "equation"]
    source_text: str
    pages: list[int]
    heading_path: list[str] = field(default_factory=list)
    boxes: list[SourceBox] = field(default_factory=list)
    payload: dict = field(default_factory=dict)
    asset_anchor: str | None = None
    start: int = 0
    end: int = 0


@dataclass
class ExtractedAsset:
    anchor: str
    block_id: str
    content: bytes = field(repr=False)
    media_type: str = "image/png"

    @property
    def sha256(self) -> str:
        return hashlib.sha256(self.content).hexdigest()


@dataclass
class ExtractionResult:
    source_sha256: str
    page_count: int
    engine: str
    versions: dict[str, str]
    settings: dict
    blocks: list[ExtractionBlock]
    status: Literal["completed", "partial", "failed"] = "completed"
    warnings: list[str] = field(default_factory=list)
    unsupported: list[str] = field(default_factory=list)
    assembled_text: str = ""
    assets: list[ExtractedAsset] = field(default_factory=list, repr=False)
    raw: dict = field(default_factory=dict, repr=False)
    format_version: int = FORMAT_VERSION

    def validate(self) -> None:
        if self.status not in {"completed", "partial", "failed"}:
            raise ExtractionError("Invalid extraction status")
        if self.page_count < 0 or self.format_version != FORMAT_VERSION:
            raise ExtractionError("Invalid extraction format/page count")
        ids: set[str] = set()
        previous_end = 0
        for ordinal, block in enumerate(self.blocks):
            if block.ordinal != ordinal or block.block_id in ids:
                raise ExtractionError("Duplicate block ID or nonsequential ordinal")
            ids.add(block.block_id)
            if block.kind not in {"text", "table", "image", "equation"}:
                raise ExtractionError("Invalid block kind")
            if any(type(page) is not int or not 1 <= page <= self.page_count for page in block.pages):
                raise ExtractionError("Invalid one-based page provenance")
            if not previous_end <= block.start <= block.end <= len(self.assembled_text):
                raise ExtractionError("Invalid/overlapping Unicode offsets")
            if self.assembled_text[block.start:block.end] != block.source_text:
                raise ExtractionError("Block text does not match assembled text offsets")
            previous_end = block.end
            for box in block.boxes:
                if box.page not in block.pages or not (
                    0 <= box.left <= box.right <= box.page_width
                    and 0 <= box.top <= box.bottom <= box.page_height
                ):
                    raise ExtractionError("Invalid normalized bounding box")
        anchors: set[str] = set()
        for asset in self.assets:
            if asset.block_id not in ids or asset.anchor in anchors:
                raise ExtractionError("Invalid/duplicate asset linkage")
            anchors.add(asset.anchor)
            block = next(item for item in self.blocks if item.block_id == asset.block_id)
            if block.asset_anchor != asset.anchor:
                raise ExtractionError("Asset anchor differs from source block")
        if any(block.asset_anchor and block.asset_anchor not in anchors for block in self.blocks):
            raise ExtractionError("Block references a missing asset")

    def normalized(self, document_id: str) -> dict:
        self.validate()
        return {
            "format_version": self.format_version,
            "document_id": document_id,
            "source_sha256": self.source_sha256,
            "page_count": self.page_count,
            "engine": self.engine,
            "versions": self.versions,
            "settings": self.settings,
            "status": self.status,
            "warnings": self.warnings,
            "unsupported": self.unsupported,
            "assembled_text": self.assembled_text,
            "blocks": [asdict(block) for block in self.blocks],
            "assets": [
                {"anchor": asset.anchor, "block_id": asset.block_id,
                 "sha256": asset.sha256, "media_type": asset.media_type,
                 "file": f"assets/{asset.sha256}.png"}
                for asset in self.assets
            ],
        }


def read_source(path: Path, options: ExtractionOptions) -> tuple[bytes, str]:
    if not path.is_file() or path.suffix.lower() != ".pdf":
        raise ExtractionError("Source must be a local PDF file")
    with path.open("rb") as stream:
        content = stream.read(options.max_bytes + 1)
    if len(content) > options.max_bytes:
        raise ExtractionError(f"Source exceeds {options.max_bytes} byte limit")
    return content, hashlib.sha256(content).hexdigest()


def block_id(sha256: str, engine_identity: str, ordinal: int) -> str:
    value = f"{FORMAT_VERSION}:{sha256}:{engine_identity}:{ordinal}"
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def assemble(blocks: list[ExtractionBlock], *, baseline: bool = False) -> str:
    """Assign Unicode offsets while retaining parser order and page markers."""
    parts: list[str] = []
    offset = 0
    previous_page: int | None = None
    for ordinal, block in enumerate(blocks):
        page = block.pages[0] if block.pages else None
        separator = "\n\n" if ordinal else ""
        marker = f"[PAGE {page}]\n" if page is not None and (baseline or page != previous_page) else ""
        prefix = separator + marker
        parts.extend((prefix, block.source_text))
        offset += len(prefix)
        block.start = offset
        offset += len(block.source_text)
        block.end = offset
        previous_page = page
    return "".join(parts)


def create_parser(engine: str, options: ExtractionOptions):
    if engine == "pypdf":
        from app.loaders.pdf_parsers.pypdf_adapter import PypdfAdapter
        return PypdfAdapter(options)
    if engine == "docling":
        from app.loaders.pdf_parsers.docling_adapter import DoclingAdapter
        return DoclingAdapter(options)
    raise ExtractionError(f"Unknown parser '{engine}'; expected pypdf or docling")

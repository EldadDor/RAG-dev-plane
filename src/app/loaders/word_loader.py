from __future__ import annotations

from dataclasses import dataclass
import hashlib
from pathlib import Path, PurePosixPath
import zipfile

from docx import Document as OpenWordDocument
from docx.document import Document as OpenWordDocumentType
from docx.opc.constants import RELATIONSHIP_TYPE
from docx.table import Table
from docx.text.paragraph import Paragraph

from app.chunkers.ids import make_doc_id
from app.domain.models import Document, DocumentAsset, SourceType


_WORD_DOCUMENT_PART = "word/document.xml"
_CONTENT_TYPES_PART = "[Content_Types].xml"
_MAX_PACKAGE_ENTRIES = 10_000
_MAX_EXPANDED_BYTES = 250 * 1024 * 1024
_PAGE_BREAK_XPATH = ".//w:br[@w:type='page'] | .//w:lastRenderedPageBreak"
_DRAWING_IMAGE_TAG = "{http://schemas.openxmlformats.org/drawingml/2006/main}blip"
_VML_IMAGE_TAG = "{urn:schemas-microsoft-com:vml}imagedata"
_RELATIONSHIP_EMBED_ATTR = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed"
_RELATIONSHIP_ID_ATTR = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"
_WORD_DRAWING_TAG = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}drawing"
_DRAWING_PROPERTIES_TAG = "{http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing}docPr"
_VML_SHAPE_TAG = "{urn:schemas-microsoft-com:vml}shape"


class WordDocumentError(ValueError):
    """The input is not a safe, readable modern Word document."""


@dataclass(frozen=True)
class _RenderedBlock:
    kind: str
    text: str
    element: object
    section: str | None = None


def _validate_package(path: Path) -> None:
    try:
        with zipfile.ZipFile(path) as package:
            entries = package.infolist()
            if len(entries) > _MAX_PACKAGE_ENTRIES:
                raise WordDocumentError(
                    f"Word package has too many entries ({len(entries)} > {_MAX_PACKAGE_ENTRIES})"
                )
            expanded_bytes = sum(entry.file_size for entry in entries)
            if expanded_bytes > _MAX_EXPANDED_BYTES:
                raise WordDocumentError(
                    f"Word package expands beyond the {_MAX_EXPANDED_BYTES}-byte safety limit"
                )
            names = {entry.filename for entry in entries}
            for name in names:
                parts = PurePosixPath(name).parts
                if PurePosixPath(name).is_absolute() or ".." in parts:
                    raise WordDocumentError("Word package contains an unsafe entry path")
            if _CONTENT_TYPES_PART not in names or _WORD_DOCUMENT_PART not in names:
                raise WordDocumentError("File is not a valid .docx package")
            corrupt_entry = package.testzip()
            if corrupt_entry is not None:
                raise WordDocumentError(f"Word package contains a corrupt entry: {corrupt_entry}")
    except zipfile.BadZipFile as exc:
        raise WordDocumentError(
            "File is not a readable .docx package; encrypted, corrupt, and legacy .doc files are unsupported"
        ) from exc


def _heading_level(paragraph: Paragraph) -> int | None:
    style_name = paragraph.style.name if paragraph.style is not None else ""
    if not style_name.lower().startswith("heading "):
        return None
    try:
        level = int(style_name.rsplit(" ", 1)[1])
    except (ValueError, IndexError):
        return None
    return min(max(level, 1), 6)


def _render_paragraph(paragraph: Paragraph, current_section: str | None) -> _RenderedBlock | None:
    text = paragraph.text.strip()
    page_breaks = len(paragraph._element.xpath(_PAGE_BREAK_XPATH))
    heading_level = _heading_level(paragraph)
    style_name = paragraph.style.name if paragraph.style is not None else ""

    if heading_level and text:
        rendered = f"{'#' * heading_level} {text}"
        return _RenderedBlock("heading", rendered, paragraph._element, text)
    if style_name.lower().startswith("list bullet") and text:
        text = f"- {text}"
    elif style_name.lower().startswith("list number") and text:
        text = f"1. {text}"
    if page_breaks:
        text = f"{text}\n[PAGE BREAK]" if text else "[PAGE BREAK]"
    if not text and not _image_relationship_refs(paragraph._element):
        return None
    kind = "caption" if style_name.lower() == "caption" else "paragraph"
    return _RenderedBlock(kind, text, paragraph._element, current_section)


def _render_table(table: Table, current_section: str | None) -> _RenderedBlock | None:
    rows = [[cell.text.strip().replace("\n", " ") for cell in row.cells] for row in table.rows]
    if not rows:
        return None
    width = max(len(row) for row in rows)
    normalized = [row + [""] * (width - len(row)) for row in rows]
    header = normalized[0]
    rendered_rows = [
        "| " + " | ".join(cell.replace("|", "\\|") for cell in row) + " |"
        for row in normalized
    ]
    rendered_rows.insert(1, "| " + " | ".join("---" for _ in header) + " |")
    return _RenderedBlock("table", "\n".join(rendered_rows), table._element, current_section)


def _iter_blocks(document: OpenWordDocumentType) -> list[_RenderedBlock]:
    blocks: list[_RenderedBlock] = []
    current_section: str | None = None
    for item in document.iter_inner_content():
        if isinstance(item, Paragraph):
            rendered = _render_paragraph(item, current_section)
            if rendered is not None:
                blocks.append(rendered)
                if rendered.kind == "heading":
                    current_section = rendered.section
        elif isinstance(item, Table):
            rendered = _render_table(item, current_section)
            if rendered is not None:
                blocks.append(rendered)
    return blocks


def _relationship_metadata(document: OpenWordDocumentType, relationship_id: str) -> dict:
    relationship = document.part.rels.get(relationship_id)
    if relationship is None:
        return {"relationship_id": relationship_id, "available": False}
    if relationship.is_external:
        return {
            "relationship_id": relationship_id,
            "available": False,
            "external": True,
        }
    if relationship.reltype != RELATIONSHIP_TYPE.IMAGE:
        return {"relationship_id": relationship_id, "available": False}
    part = relationship.target_part
    blob = part.blob
    return {
        "relationship_id": relationship_id,
        "available": True,
        "external": False,
        "part_name": str(part.partname),
        "original_name": PurePosixPath(str(part.partname)).name,
        "media_type": part.content_type,
        "byte_size": len(blob),
        "content_hash": hashlib.sha256(blob).hexdigest(),
    }


def _nearest_ancestor(element: object, tag: str) -> object | None:
    current = element.getparent()
    while current is not None:
        if current.tag == tag:
            return current
        current = current.getparent()
    return None


def _image_relationship_refs(element: object) -> list[dict]:
    refs: list[dict] = []
    for descendant in element.iter():
        relationship_id: str | None = None
        alt_text: str | None = None
        display_name: str | None = None
        if descendant.tag == _DRAWING_IMAGE_TAG:
            relationship_id = descendant.get(_RELATIONSHIP_EMBED_ATTR)
            drawing = _nearest_ancestor(descendant, _WORD_DRAWING_TAG)
            if drawing is not None:
                properties = next(
                    (item for item in drawing.iter() if item.tag == _DRAWING_PROPERTIES_TAG),
                    None,
                )
                if properties is not None:
                    alt_text = properties.get("descr") or properties.get("title")
                    display_name = properties.get("name")
        elif descendant.tag == _VML_IMAGE_TAG:
            relationship_id = descendant.get(_RELATIONSHIP_ID_ATTR)
            shape = _nearest_ancestor(descendant, _VML_SHAPE_TAG)
            if shape is not None:
                alt_text = shape.get("alt") or shape.get("title")
                display_name = shape.get("id")
        if relationship_id:
            refs.append(
                {
                    "relationship_id": relationship_id,
                    "alt_text": alt_text,
                    "display_name": display_name,
                }
            )
    return refs


def _image_anchors(document: OpenWordDocumentType, blocks: list[_RenderedBlock]) -> list[dict]:
    anchors: list[dict] = []
    for block_ordinal, block in enumerate(blocks):
        refs = _image_relationship_refs(block.element)
        for ref in refs:
            caption = block.text.strip() or None
            if caption is None and block_ordinal + 1 < len(blocks) and blocks[block_ordinal + 1].kind == "caption":
                caption = blocks[block_ordinal + 1].text.strip() or None
            anchors.append(
                {
                    "anchor_id": f"image-{len(anchors):04d}",
                    "block_id": f"block-{block_ordinal:04d}",
                    "block_ordinal": block_ordinal,
                    "section": block.section,
                    "alt_text": ref["alt_text"],
                    "display_name": ref["display_name"],
                    "caption": caption,
                    **_relationship_metadata(document, ref["relationship_id"]),
                }
            )
    return anchors


class WordLoader:
    """Load safe `.docx` text and retain structural/image-anchor metadata."""

    def load(self, source_path: str) -> Document:
        path = Path(source_path)
        _validate_package(path)
        try:
            word_document = OpenWordDocument(str(path))
        except Exception as exc:
            raise WordDocumentError(f"Unable to parse Word document: {exc}") from exc

        blocks = _iter_blocks(word_document)
        content_parts: list[str] = []
        block_metadata: list[dict] = []
        offset = 0
        for ordinal, block in enumerate(blocks):
            if content_parts:
                offset += 2
            start = offset
            content_parts.append(block.text)
            offset += len(block.text)
            block_metadata.append(
                {
                    "block_id": f"block-{ordinal:04d}",
                    "ordinal": ordinal,
                    "kind": block.kind,
                    "start_index": start,
                    "end_index": offset,
                    "section": block.section,
                }
            )

        title = (word_document.core_properties.title or "").strip() or path.stem
        package_hash = hashlib.sha256(path.read_bytes()).hexdigest()
        anchors = _image_anchors(word_document, blocks)
        block_offsets = {block["block_id"]: block["start_index"] for block in block_metadata}
        assets: list[DocumentAsset] = []
        for ordinal, anchor in enumerate(anchors):
            if not anchor.get("available"):
                continue
            relationship = word_document.part.rels[anchor["relationship_id"]]
            blob = relationship.target_part.blob
            assets.append(
                DocumentAsset(
                    anchor_id=anchor["anchor_id"],
                    relationship_id=anchor["relationship_id"],
                    content=blob,
                    content_hash=anchor["content_hash"],
                    media_type=anchor["media_type"],
                    original_name=anchor["original_name"],
                    ordinal=ordinal,
                    block_id=anchor["block_id"],
                    block_ordinal=anchor["block_ordinal"],
                    source_index=block_offsets.get(anchor["block_id"]),
                    section=anchor["section"],
                    alt_text=anchor["alt_text"],
                    caption=anchor["caption"],
                )
            )
        return Document(
            doc_id=make_doc_id(source_path),
            source_path=source_path,
            source_type=SourceType.word,
            content="\n\n".join(content_parts),
            title=title,
            metadata={
                "blocks": block_metadata,
                "image_anchors": anchors,
                "image_count": sum(1 for anchor in anchors if anchor.get("available")),
                "page_break_count": sum(block.text.count("[PAGE BREAK]") for block in blocks),
            },
            content_hash=package_hash,
            assets=assets,
        )

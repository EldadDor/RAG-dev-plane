from __future__ import annotations

from dataclasses import asdict
from io import BytesIO
from pathlib import Path

import pypdf

from app.loaders.pdf_extraction import (
    ExtractionBlock, ExtractionError, ExtractionOptions, ExtractionResult,
    assemble, block_id, read_source,
)


class PypdfAdapter:
    def __init__(self, options: ExtractionOptions):
        self.options = options

    def extract(self, path: Path, options: ExtractionOptions) -> ExtractionResult:
        if options != self.options:
            raise ExtractionError("Parser options must remain fixed within a run")
        content, sha256 = read_source(path, options)
        reader = pypdf.PdfReader(BytesIO(content))
        if reader.is_encrypted:
            raise ExtractionError("Encrypted PDF is not supported by this experiment")
        if len(reader.pages) > options.max_pages:
            raise ExtractionError(f"PDF exceeds {options.max_pages} page limit")
        blocks = [
            ExtractionBlock(
                block_id=block_id(sha256, f"pypdf:{pypdf.__version__}", index),
                ordinal=index, kind="text", source_text=page.extract_text() or "",
                pages=[index + 1],
            )
            for index, page in enumerate(reader.pages)
        ]
        result = ExtractionResult(
            source_sha256=sha256, page_count=len(reader.pages), engine="pypdf",
            versions={"pypdf": pypdf.__version__},
            settings={"options": asdict(options), "effective": {"ocr": False, "extraction_mode": "plain"}},
            blocks=blocks,
            warnings=[f"Page {block.pages[0]} has no extracted text" for block in blocks if not block.source_text],
            unsupported=["ocr", "layout", "table_detection", "image_detection"],
            assembled_text=assemble(blocks, baseline=True),
            raw={"pages": [{"page": b.pages[0], "text": b.source_text} for b in blocks]},
        )
        result.validate()
        return result

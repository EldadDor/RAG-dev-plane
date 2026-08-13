from __future__ import annotations

from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter

from app.chunkers.ids import make_chunk_id
from app.domain.models import Chunk, Document, SourceType


_MARKDOWN_HEADERS = [
    ("#", "h1"),
    ("##", "h2"),
    ("###", "h3"),
]


class TextChunker:
    """
    Splits documents into overlapping text chunks.

    Strategy:
    - Markdown documents: header-aware split first, then recursive character split per section.
    - All other types: recursive character split directly.
    """

    def __init__(self, chunk_size: int = 800, chunk_overlap: int = 120) -> None:
        self._chunk_size = chunk_size
        self._chunk_overlap = chunk_overlap
        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""],
        )
        self._md_header_splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=_MARKDOWN_HEADERS,
            strip_headers=False,
        )

    def chunk(self, document: Document) -> list[Chunk]:
        if document.source_type == SourceType.markdown:
            return self._chunk_markdown(document)
        return self._chunk_generic(document)

    def _chunk_markdown(self, document: Document) -> list[Chunk]:
        """Split on headers first, then recursively split each section."""
        header_docs = self._md_header_splitter.split_text(document.content)
        chunks: list[Chunk] = []
        for header_doc in header_docs:
            section = (
                header_doc.metadata.get("h3")
                or header_doc.metadata.get("h2")
                or header_doc.metadata.get("h1")
            )
            sub_texts = self._splitter.split_text(header_doc.page_content)
            for text in sub_texts:
                idx = len(chunks)
                chunks.append(
                    Chunk(
                        chunk_id=make_chunk_id(document.doc_id, idx),
                        doc_id=document.doc_id,
                        source_path=document.source_path,
                        source_type=document.source_type,
                        text=text,
                        chunk_index=idx,
                        title=document.title,
                        page=document.metadata.get("page"),
                        section=section,
                    )
                )
        if not chunks:
            # Fallback: document had no headers
            return self._chunk_generic(document)
        return chunks

    def _chunk_generic(self, document: Document) -> list[Chunk]:
        texts = self._splitter.split_text(document.content)
        return [
            Chunk(
                chunk_id=make_chunk_id(document.doc_id, idx),
                doc_id=document.doc_id,
                source_path=document.source_path,
                source_type=document.source_type,
                text=text,
                chunk_index=idx,
                title=document.title,
                page=document.metadata.get("page"),
                section=document.metadata.get("section"),
            )
            for idx, text in enumerate(texts)
        ]

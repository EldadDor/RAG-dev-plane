from __future__ import annotations

import logging

from app.api.schemas import IngestResponse, IngestResult
from app.chunkers.text_chunker import TextChunker
from app.clients.embedding_client import EmbeddingClient
from app.clients.qdrant_client import QdrantVectorStore
from app.config import Settings
from app.loaders.registry import UnsupportedFileTypeError, load_directory, load_document
from app.domain.models import Chunk

logger = logging.getLogger(__name__)


class IngestionService:
    def __init__(
        self,
        settings: Settings,
        embedding_client: EmbeddingClient,
        vector_store: QdrantVectorStore,
    ) -> None:
        self._settings = settings
        self._embedding_client = embedding_client
        self._vector_store = vector_store
        self._chunker = TextChunker(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
        )

    async def ingest_file(self, source_path: str) -> IngestResult:
        """Load, chunk, embed and index a single file."""
        try:
            document = load_document(source_path)
        except (FileNotFoundError, UnsupportedFileTypeError, Exception) as exc:
            logger.warning("Skipping %s: %s", source_path, exc)
            return IngestResult(
                doc_id="",
                source_path=source_path,
                chunks_indexed=0,
                skipped=True,
                skip_reason=str(exc),
            )

        chunks = self._chunker.chunk(document)
        if not chunks:
            return IngestResult(
                doc_id=document.doc_id,
                source_path=source_path,
                chunks_indexed=0,
                skipped=True,
                skip_reason="No chunks produced",
            )

        indexed = await self._embed_and_upsert(chunks)
        return IngestResult(
            doc_id=document.doc_id,
            source_path=source_path,
            chunks_indexed=indexed,
        )

    async def ingest_directory(self, directory: str, recursive: bool = False) -> IngestResponse:
        """Load, chunk, embed and index all supported files in a directory."""
        documents, skipped_files = load_directory(directory, recursive=recursive)
        results: list[IngestResult] = []
        total_indexed = 0

        for skip in skipped_files:
            results.append(
                IngestResult(
                    doc_id="",
                    source_path=skip["path"],
                    chunks_indexed=0,
                    skipped=True,
                    skip_reason=skip["reason"],
                )
            )

        for document in documents:
            chunks = self._chunker.chunk(document)
            if not chunks:
                results.append(
                    IngestResult(
                        doc_id=document.doc_id,
                        source_path=document.source_path,
                        chunks_indexed=0,
                        skipped=True,
                        skip_reason="No chunks produced",
                    )
                )
                continue
            indexed = await self._embed_and_upsert(chunks)
            total_indexed += indexed
            results.append(
                IngestResult(
                    doc_id=document.doc_id,
                    source_path=document.source_path,
                    chunks_indexed=indexed,
                )
            )

        return IngestResponse(indexed=total_indexed, documents=results)

    async def _embed_and_upsert(self, chunks: list[Chunk]) -> int:
        """Embed each chunk and upsert the batch into Qdrant. Returns chunk count."""
        batch: list[dict] = []
        for chunk in chunks:
            try:
                vector = await self._embedding_client.create_embedding(
                    self._settings.embedding_model, chunk.text
                )
            except Exception as exc:
                logger.error("Embedding failed for chunk %s: %s", chunk.chunk_id, exc)
                continue

            # Ensure collection exists with the correct vector size on first write
            await self._vector_store.ensure_collection(vector_size=len(vector))

            batch.append(
                {
                    "chunk_id": chunk.chunk_id,
                    "vector": vector,
                    "payload": {
                        "doc_id": chunk.doc_id,
                        "source_path": chunk.source_path,
                        "source_type": chunk.source_type.value,
                        "text": chunk.text,
                        "chunk_index": chunk.chunk_index,
                        "title": chunk.title,
                        "page": chunk.page,
                        "section": chunk.section,
                    },
                }
            )

        if batch:
            await self._vector_store.upsert(batch)
        return len(batch)

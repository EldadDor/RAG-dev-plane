from __future__ import annotations

import logging

from app.api.schemas import IngestResponse, IngestResult
from app.chunkers.text_chunker import TextChunker
from app.clients.embedding_client import EmbeddingClient
from app.clients.vector_store import VectorStore
from app.config import Settings
from app.loaders.registry import UnsupportedFileTypeError, load_directory, load_document
from app.domain.models import Chunk

logger = logging.getLogger(__name__)


class IngestionService:
    def __init__(
            self,
            settings: Settings,
            embedding_client: EmbeddingClient,
            vector_store: VectorStore,
    ) -> None:
        self._settings = settings
        self._embedding_client = embedding_client
        self._vector_store = vector_store
        self._chunker = TextChunker(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
        )
        logger.debug("IngestionService initialized with chunk_size=%d chunk_overlap=%d", settings.chunk_size, settings.chunk_overlap)

    async def ingest_file(self, source_path: str) -> IngestResult:
        """Load, chunk, embed and index a single file."""
        logger.debug("Starting ingest_file: %s", source_path)
        try:
            document = load_document(source_path)
            logger.info("  📖 Loaded document: %s (doc_id=%s)", source_path, document.doc_id)
        except (FileNotFoundError, UnsupportedFileTypeError, Exception) as exc:
            logger.warning("  ⚠️  Skipping %s: %s", source_path, exc)
            return IngestResult(
                doc_id="",
                source_path=source_path,
                chunks_indexed=0,
                skipped=True,
                skip_reason=str(exc),
            )

        chunks = self._chunker.chunk(document)
        logger.info("  ✂️  Chunked into %d pieces", len(chunks))

        if not chunks:
            logger.warning("  ⚠️  No chunks produced from %s", source_path)
            return IngestResult(
                doc_id=document.doc_id,
                source_path=source_path,
                chunks_indexed=0,
                skipped=True,
                skip_reason="No chunks produced",
            )

        indexed = await self._embed_and_upsert(chunks)
        logger.info("  ✅ File complete: %d chunks embedded & indexed", indexed)
        return IngestResult(
            doc_id=document.doc_id,
            source_path=source_path,
            chunks_indexed=indexed,
        )

    async def ingest_directory(self, directory: str, recursive: bool = False) -> IngestResponse:
        """Load, chunk, embed and index all supported files in a directory."""
        logger.debug("Starting ingest_directory: %s (recursive=%s)", directory, recursive)

        documents, skipped_files = load_directory(directory, recursive=recursive)
        logger.info("  📁 Loaded %d documents, %d files skipped", len(documents), len(skipped_files))

        results: list[IngestResult] = []
        total_indexed = 0

        for skip in skipped_files:
            logger.debug("    ⏭️  Skipped: %s (%s)", skip["path"], skip["reason"])
            results.append(
                IngestResult(
                    doc_id="",
                    source_path=skip["path"],
                    chunks_indexed=0,
                    skipped=True,
                    skip_reason=skip["reason"],
                )
            )

        for i, document in enumerate(documents, 1):
            logger.info("  [%d/%d] Processing: %s", i, len(documents), document.source_path)
            chunks = self._chunker.chunk(document)
            logger.debug("    ✂️  Chunked into %d pieces", len(chunks))

            if not chunks:
                logger.warning("    ⚠️  No chunks produced")
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
            logger.info("    ✅ Embedded & indexed %d chunks", indexed)

            results.append(
                IngestResult(
                    doc_id=document.doc_id,
                    source_path=document.source_path,
                    chunks_indexed=indexed,
                )
            )

        logger.info("  🎯 Directory ingestion complete: %d chunks total", total_indexed)
        return IngestResponse(indexed=total_indexed, documents=results)

    async def _embed_and_upsert(self, chunks: list[Chunk]) -> int:
        """Embed each chunk and upsert the batch into Qdrant. Returns chunk count."""
        logger.debug("Starting _embed_and_upsert for %d chunks", len(chunks))
        batch: list[dict] = []
        embedding_errors = 0

        for i, chunk in enumerate(chunks, 1):
            try:
                vector = await self._embedding_client.create_embedding(
                    self._settings.embedding_model, chunk.text
                )
                logger.debug("  🔢 [%d/%d] Embedded chunk (dim=%d): %s", i, len(chunks), len(vector), chunk.chunk_id[:12])
            except Exception as exc:
                embedding_errors += 1
                logger.error("  ❌ [%d/%d] Embedding failed for chunk %s: %s", i, len(chunks), chunk.chunk_id[:12], exc)
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
            logger.debug("  📤 Upserting %d vectors to vector store", len(batch))
            await self._vector_store.upsert(batch)
            logger.debug("  ✅ Upsert complete")

        if embedding_errors:
            logger.warning("  ⚠️  %d embedding errors during batch processing", embedding_errors)

        return len(batch)
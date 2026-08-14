from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

from app.chunkers.chunker_adapter import ChunkerConfig, ChunkerFactory
from app.chunkers.python_code_chunker import chunk_python_document
from app.chunkers.java_code_chunker import chunk_java_document
from app.domain.models import IngestedChunk, IngestedDocumentResult, IngestionResult, SourceType
from app.loaders.registry import UnsupportedFileTypeError, load_directory, load_document
from app.config import Settings
from app.services.repository_metadata import get_repository_metadata


class IngestionService:
    def __init__(
            self,
            settings: Settings,
            embedding_client: Any,
            vector_store: Any,
    ) -> None:
        self._settings = settings
        self._embedding_client = embedding_client
        self._vector_store = vector_store
        self._chunker = ChunkerFactory.build(
            ChunkerConfig(
                provider=getattr(settings, "chunker_provider", "default"),
                chunk_size=getattr(settings, "chunk_size", 512),
                chunk_overlap=getattr(settings, "chunk_overlap", 64),
                semantic_threshold=getattr(settings, "chunker_semantic_threshold", 0.5),
                recipe=getattr(settings, "chunker_recipe", None),
                embedding_model=getattr(settings, "chunker_embedding_model", None),
            )
        )

    async def ingest_path(self, source_path: str, recursive: bool = False) -> IngestionResult:
        """Ingest a single file or all supported files in a directory."""
        path = Path(source_path)

        if path.is_dir():
            documents, _skipped = load_directory(source_path, recursive=recursive)
        else:
            try:
                documents = [load_document(source_path)]
            except UnsupportedFileTypeError as exc:
                raise ValueError(str(exc)) from exc
        repository_context = get_repository_metadata(str(path if path.is_dir() else path.parent))

        chunks_to_index: list[IngestedChunk] = []
        document_results: list[IngestedDocumentResult] = []
        total_documents = 0

        for document in documents:
            total_documents += 1
            text = (document.content or "").strip()
            if not text:
                continue

            if document.source_type == SourceType.code and document.metadata.get("language") == "python":
                chunked = chunk_python_document(document)
            elif document.source_type == SourceType.code and document.metadata.get("language") == "java":
                chunked = chunk_java_document(document) or self._chunker.chunk(text)
            else:
                chunked = self._chunker.chunk(text)
            repository_metadata = dict(repository_context)
            repository_root = repository_metadata.get("repository_path")
            if repository_root:
                try:
                    repository_metadata["repository_relative_path"] = str(
                        Path(document.source_path).resolve().relative_to(Path(repository_root))
                    )
                except ValueError:
                    pass
            valid_chunks = [
                (chunk_index, chunk)
                for chunk_index, chunk in enumerate(chunked)
                if (chunk.text or "").strip()
            ]

            if not valid_chunks:
                document_results.append(
                    IngestedDocumentResult(
                        doc_id=document.doc_id,
                        source_path=document.source_path,
                        chunks_indexed=0,
                    )
                )
                continue

            # Embed all chunks for this document concurrently
            embeddings = await asyncio.gather(*[
                self._embedding_client.create_embedding(
                    self._settings.embedding_model,
                    chunk.text.strip(),
                )
                for _, chunk in valid_chunks
            ])

            chunker_provider = getattr(self._settings, "chunker_provider", "default")
            for (chunk_index, chunk), embedding in zip(valid_chunks, embeddings):
                chunk_text = chunk.text.strip()
                chunks_to_index.append(
                    IngestedChunk(
                        doc_id=document.doc_id,
                        chunk_id=f"{document.doc_id}:{chunk_index}",
                        text=chunk_text,
                        embedding=embedding,
                        source_path=document.source_path,
                        title=document.title,
                        page=document.metadata.get("page"),
                        section=document.metadata.get("section"),
                        metadata={
                            **document.metadata,
                            **repository_metadata,
                            "source_type": document.source_type.value,
                            "chunk_index": chunk_index,
                            "chunker_provider": chunker_provider,
                            "token_count": chunk.token_count,
                            "start_index": chunk.start_index,
                            "end_index": chunk.end_index,
                            **(chunk.metadata or {}),
                            "chunker_metadata": chunk.metadata or {},
                        },
                    )
                )
            document_results.append(
                IngestedDocumentResult(
                    doc_id=document.doc_id,
                    source_path=document.source_path,
                    chunks_indexed=len(valid_chunks),
                )
            )

        if chunks_to_index:
            await self._vector_store.upsert([c.to_dict() for c in chunks_to_index])

        return IngestionResult(
            source_path=str(path),
            documents_processed=total_documents,
            chunks_indexed=len(chunks_to_index),
            chunker_provider=getattr(self._settings, "chunker_provider", "default"),
            documents=document_results,
        )

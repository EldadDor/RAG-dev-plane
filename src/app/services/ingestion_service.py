from __future__ import annotations

import asyncio
import hashlib
from pathlib import Path
from typing import Any

from app.chunkers.chunker_adapter import ChunkerConfig, ChunkerFactory
from app.chunkers.python_code_chunker import chunk_python_document
from app.chunkers.java_code_chunker import chunk_java_document
from app.chunkers.kotlin_code_chunker import chunk_kotlin_document
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
    def _chunker_for(self, chunking_profile: str):
        _, profile = self._settings.chunking_profile(chunking_profile)
        return ChunkerFactory.build(
            ChunkerConfig(
                provider=profile.provider,
                chunk_size=profile.chunk_size,
                chunk_overlap=profile.chunk_overlap,
                semantic_threshold=profile.semantic_threshold,
                recipe=profile.recipe,
                embedding_model=profile.embedding_model,
            )
        )

    async def ingest_path(
        self, source_path: str, recursive: bool = False, workspace_id: str | None = None,
        chunking_profile: str | None = None, dry_run: bool = False,
    ) -> IngestionResult:
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
        workspace_id = workspace_id or self._settings.default_workspace_id
        profile_name, profile = self._settings.chunking_profile(chunking_profile)
        chunker = self._chunker_for(profile_name)
        root_path = str(path.resolve()) if path.is_dir() else None

        chunks_indexed = 0
        document_results: list[IngestedDocumentResult] = []
        total_documents = 0
        present_doc_ids: list[str] = []

        for document in documents:
            total_documents += 1
            present_doc_ids.append(document.doc_id)
            text = (document.content or "").strip()
            content_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
            if not text:
                if not dry_run:
                    await self._vector_store.replace_document({
                        "doc_id": document.doc_id,
                        "workspace_id": workspace_id,
                        "chunking_profile": profile_name,
                        "root_path": root_path,
                        "source_path": document.source_path,
                        "source_type": document.source_type.value,
                        "content_hash": content_hash,
                        "metadata": {**document.metadata, **repository_context},
                    }, [])
                document_results.append(IngestedDocumentResult(
                    doc_id=document.doc_id, source_path=document.source_path, chunks_indexed=0,
                    skipped=True, skip_reason="empty",
                ))
                continue
            if not dry_run and await self._vector_store.get_document_hash(document.doc_id, workspace_id, profile_name) == content_hash:
                document_results.append(IngestedDocumentResult(
                    doc_id=document.doc_id, source_path=document.source_path, chunks_indexed=0,
                    skipped=True, skip_reason="unchanged",
                ))
                continue

            if document.source_type == SourceType.code and document.metadata.get("language") == "python":
                chunked = chunk_python_document(document)
            elif document.source_type == SourceType.code and document.metadata.get("language") == "java":
                chunked = chunk_java_document(document) or chunker.chunk(text)
            elif document.source_type == SourceType.code and document.metadata.get("language") == "kotlin":
                chunked = chunk_kotlin_document(document) or chunker.chunk(text)
            else:
                chunked = chunker.chunk(text)
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

            chunks_indexed += len(valid_chunks)
            if dry_run:
                document_results.append(IngestedDocumentResult(
                    doc_id=document.doc_id, source_path=document.source_path, chunks_indexed=len(valid_chunks),
                ))
                continue

            # Embed only persistent ingestions; dry runs must not contact a model.
            embeddings = await asyncio.gather(*[
                self._embedding_client.create_embedding(self._settings.embedding_model, chunk.text.strip())
                for _, chunk in valid_chunks
            ])

            chunker_provider = profile.provider
            document_chunks: list[IngestedChunk] = []
            for (chunk_index, chunk), embedding in zip(valid_chunks, embeddings):
                chunk_text = chunk.text.strip()
                document_chunks.append(
                    IngestedChunk(
                        doc_id=document.doc_id,
                        chunk_id=(f"{document.doc_id}:{chunk_index}" if profile_name == "default"
                                  else f"{document.doc_id}:{profile_name}:{chunk_index}"),
                        text=chunk_text,
                        embedding=embedding,
                        source_path=document.source_path,
                        title=document.title,
                        page=document.metadata.get("page"),
                        section=document.metadata.get("section"),
                        metadata={
                            **document.metadata,
                            **repository_metadata,
                            "workspace_id": workspace_id,
                            "chunking_profile": profile_name,
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
            await self._vector_store.replace_document(
                {
                    "doc_id": document.doc_id,
                    "workspace_id": workspace_id,
                    "chunking_profile": profile_name,
                    "root_path": root_path,
                    "source_path": document.source_path,
                    "source_type": document.source_type.value,
                    "content_hash": content_hash,
                    "metadata": {**document.metadata, **repository_metadata},
                },
                [chunk.to_dict() for chunk in document_chunks],
            )
            document_results.append(
                IngestedDocumentResult(
                    doc_id=document.doc_id,
                    source_path=document.source_path,
                    chunks_indexed=len(valid_chunks),
                )
            )

        if root_path and not dry_run:
            await self._vector_store.delete_missing_documents(root_path, workspace_id, present_doc_ids, profile_name)

        return IngestionResult(
            source_path=str(path),
            documents_processed=total_documents,
            chunks_indexed=chunks_indexed,
            chunker_provider=profile.provider,
            chunking_profile=profile_name,
            dry_run=dry_run,
            documents=document_results,
        )

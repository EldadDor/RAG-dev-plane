from __future__ import annotations

import asyncio
import hashlib
from pathlib import Path
from typing import Any

from app.chunkers.chunker_adapter import ChunkerConfig, ChunkerFactory
from app.chunkers.python_code_chunker import chunk_python_document
from app.chunkers.java_code_chunker import chunk_java_document
from app.chunkers.kotlin_code_chunker import chunk_kotlin_document
from app.domain.models import Document, IngestedChunk, IngestedDocumentResult, IngestionResult, SourceType
from app.loaders.registry import UnsupportedFileTypeError, load_directory, load_document
from app.config import Settings
from app.services.repository_metadata import get_repository_metadata
from app.services.asset_store import AssetStore, InMemoryAssetStore


class IngestionService:
    def __init__(
            self,
            settings: Settings,
            embedding_client: Any,
            vector_store: Any,
            asset_store: AssetStore | None = None,
    ) -> None:
        self._settings = settings
        self._embedding_client = embedding_client
        self._vector_store = vector_store
        self._asset_store = asset_store or InMemoryAssetStore()

    @staticmethod
    def _chunk_id(document_id: str, profile_name: str, chunk_index: int) -> str:
        return (
            f"{document_id}:{chunk_index}"
            if profile_name == "default"
            else f"{document_id}:{profile_name}:{chunk_index}"
        )

    async def _prepare_assets(
        self,
        document: Document,
        valid_chunks: list[tuple[int, Any]],
        workspace_id: str,
        profile_name: str,
        *,
        persist: bool,
    ) -> tuple[list[dict], dict[int, list[str]]]:
        if len(document.assets) > self._settings.asset_max_images_per_document:
            raise ValueError("Document exceeds ASSET_MAX_IMAGES_PER_DOCUMENT")
        total_bytes = sum(len(asset.content) for asset in document.assets)
        if total_bytes > self._settings.asset_max_total_bytes_per_document:
            raise ValueError("Document exceeds ASSET_MAX_TOTAL_BYTES_PER_DOCUMENT")

        records: list[dict] = []
        chunk_assets: dict[int, list[str]] = {}
        for asset in document.assets:
            if len(asset.content) > self._settings.asset_max_image_bytes:
                raise ValueError(f"Embedded image exceeds ASSET_MAX_IMAGE_BYTES: {asset.original_name or asset.anchor_id}")
            asset_id = hashlib.sha256(
                f"{workspace_id}:{profile_name}:{document.doc_id}:{asset.anchor_id}".encode("utf-8")
            ).hexdigest()
            storage_key = asset.content_hash or hashlib.sha256(asset.content).hexdigest()

            related_index: int | None = None
            if valid_chunks:
                source_index = asset.source_index if asset.source_index is not None else 0
                containing = [
                    chunk_index
                    for chunk_index, chunk in valid_chunks
                    if chunk.start_index is not None
                    and chunk.end_index is not None
                    and chunk.start_index <= source_index <= chunk.end_index
                ]
                if containing:
                    related_index = containing[0]
                else:
                    related_index = min(
                        valid_chunks,
                        key=lambda item: abs((item[1].start_index or 0) - source_index),
                    )[0]
                chunk_assets.setdefault(related_index, []).append(asset_id)

            related_chunk_ids = (
                [self._chunk_id(document.doc_id, profile_name, related_index)]
                if related_index is not None
                else []
            )
            records.append(
                {
                    "asset_id": asset_id,
                    "storage_key": storage_key,
                    "content_hash": storage_key,
                    "media_type": asset.media_type,
                    "byte_size": len(asset.content),
                    "original_name": asset.original_name,
                    "relationship_id": asset.relationship_id,
                    "ordinal": asset.ordinal,
                    "width": asset.width,
                    "height": asset.height,
                    "alt_text": asset.alt_text,
                    "caption": asset.caption,
                    "anchor_block_id": asset.block_id,
                    "related_chunk_ids": related_chunk_ids,
                }
            )
            if persist:
                await self._asset_store.put(storage_key, asset.content)
        return records, chunk_assets
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

    async def _embed_chunks(self, chunks: list[tuple[int, Any]]) -> list[list[float]]:
        """Embed chunks in bounded batches to avoid exhausting OS socket limits."""
        embeddings: list[list[float]] = []
        batch_size = self._settings.embedding_concurrency
        for start in range(0, len(chunks), batch_size):
            batch = chunks[start:start + batch_size]
            embeddings.extend(await asyncio.gather(*[
                self._embedding_client.create_embedding(self._settings.embedding_model, chunk.text.strip())
                for _, chunk in batch
            ]))
        return embeddings

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
            content_hash = document.content_hash or hashlib.sha256(text.encode("utf-8")).hexdigest()
            if not text:
                if not dry_run:
                    assets, _ = await self._prepare_assets(
                        document, [], workspace_id, profile_name, persist=True
                    )
                    await self._vector_store.replace_document({
                        "doc_id": document.doc_id,
                        "workspace_id": workspace_id,
                        "chunking_profile": profile_name,
                        "root_path": root_path,
                        "source_path": document.source_path,
                        "source_type": document.source_type.value,
                        "content_hash": content_hash,
                        "metadata": {**document.metadata, **repository_context},
                    }, [], assets)
                document_results.append(IngestedDocumentResult(
                    doc_id=document.doc_id, source_path=document.source_path, chunks_indexed=0,
                    skipped=True, skip_reason="empty", assets_found=len(document.assets),
                ))
                continue
            if not dry_run and await self._vector_store.get_document_hash(document.doc_id, workspace_id, profile_name) == content_hash:
                document_results.append(IngestedDocumentResult(
                    doc_id=document.doc_id, source_path=document.source_path, chunks_indexed=0,
                    skipped=True, skip_reason="unchanged", assets_found=len(document.assets),
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
                        assets_found=len(document.assets),
                    )
                )
                continue

            chunks_indexed += len(valid_chunks)
            if dry_run:
                document_results.append(IngestedDocumentResult(
                    doc_id=document.doc_id, source_path=document.source_path, chunks_indexed=len(valid_chunks),
                    assets_found=len(document.assets),
                ))
                continue

            # Embed only persistent ingestions; dry runs must not contact a model.
            embeddings = await self._embed_chunks(valid_chunks)
            assets, chunk_assets = await self._prepare_assets(
                document, valid_chunks, workspace_id, profile_name, persist=True
            )
            public_assets = {
                asset["asset_id"]: {
                    key: asset.get(key)
                    for key in (
                        "asset_id", "media_type", "width", "height", "alt_text", "caption"
                    )
                }
                for asset in assets
            }

            chunker_provider = profile.provider
            document_chunks: list[IngestedChunk] = []
            for (chunk_index, chunk), embedding in zip(valid_chunks, embeddings):
                chunk_text = chunk.text.strip()
                document_chunks.append(
                    IngestedChunk(
                        doc_id=document.doc_id,
                        chunk_id=self._chunk_id(document.doc_id, profile_name, chunk_index),
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
                            "related_asset_ids": chunk_assets.get(chunk_index, []),
                            "related_assets": [
                                public_assets[asset_id]
                                for asset_id in chunk_assets.get(chunk_index, [])
                            ],
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
                assets,
            )
            document_results.append(
                IngestedDocumentResult(
                    doc_id=document.doc_id,
                    source_path=document.source_path,
                    chunks_indexed=len(valid_chunks),
                    assets_found=len(document.assets),
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

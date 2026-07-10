from __future__ import annotations

from pathlib import Path
from typing import Any

from app.chunkers.chunker_adapter import ChunkerConfig, ChunkerFactory
from app.domain.documents import IngestedChunk, IngestionResult
from app.loaders.registry import LoaderRegistry
from app.config import Settings


class IngestionService:
    def __init__(
            self,
            settings: Settings,
            loader_registry: LoaderRegistry,
            embedding_client: Any,
            vector_store: Any,
    ) -> None:
        self._settings = settings
        self._loader_registry = loader_registry
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

    async def ingest_path(self, source_path: str) -> IngestionResult:
        path = Path(source_path)
        loader = self._loader_registry.get_loader(path)
        loaded = await loader.load(path)

        chunks_to_index: list[IngestedChunk] = []
        total_documents = 0

        for document in loaded:
            total_documents += 1
            text = (document.text or "").strip()
            if not text:
                continue

            chunked = self._chunker.chunk(text)
            for chunk_index, chunk in enumerate(chunked):
                chunk_text = (chunk.text or "").strip()
                if not chunk_text:
                    continue

                embedding = await self._embedding_client.embed(chunk_text)
                chunks_to_index.append(
                    IngestedChunk(
                        doc_id=getattr(document, "doc_id", path.stem),
                        chunk_id=f"{getattr(document, 'doc_id', path.stem)}:{chunk_index}",
                        text=chunk_text,
                        embedding=embedding,
                        source_path=str(path),
                        title=getattr(document, "title", None),
                        page=getattr(document, "page", None),
                        section=getattr(document, "section", None),
                        metadata={
                            **(getattr(document, "metadata", {}) or {}),
                            "chunk_index": chunk_index,
                            "chunker_provider": getattr(self._settings, "chunker_provider", "default"),
                            "token_count": chunk.token_count,
                            "start_index": chunk.start_index,
                            "end_index": chunk.end_index,
                            "chunker_metadata": chunk.metadata or {},
                        },
                    )
                )

        if chunks_to_index:
            await self._vector_store.upsert(chunks_to_index)

        return IngestionResult(
            source_path=str(path),
            documents_processed=total_documents,
            chunks_indexed=len(chunks_to_index),
            chunker_provider=getattr(self._settings, "chunker_provider", "default"),
        )

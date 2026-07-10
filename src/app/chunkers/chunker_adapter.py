from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass
class ChunkerConfig:
    provider: str = "default"
    chunk_size: int = 512
    chunk_overlap: int = 64
    semantic_threshold: float = 0.5
    recipe: str | None = None
    embedding_model: str | None = None
    min_characters_per_chunk: int = 24


@dataclass
class ChunkedText:
    text: str
    token_count: int | None = None
    start_index: int | None = None
    end_index: int | None = None
    metadata: dict | None = None


class TextChunker(Protocol):
    def chunk(self, text: str) -> list[ChunkedText]: ...


class DefaultChunker:
    def __init__(self, chunk_size: int = 512, chunk_overlap: int = 64) -> None:
        from langchain_text_splitters import RecursiveCharacterTextSplitter

        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )

    def chunk(self, text: str) -> list[ChunkedText]:
        return [ChunkedText(text=part) for part in self._splitter.split_text(text)]


class ChonkieRecursiveAdapter:
    def __init__(self, config: ChunkerConfig) -> None:
        from chonkie import RecursiveChunker

        kwargs = {
            "chunk_size": config.chunk_size,
            "min_characters_per_chunk": config.min_characters_per_chunk,
        }
        if config.recipe:
            self._chunker = RecursiveChunker.from_recipe(config.recipe, **kwargs)
        else:
            self._chunker = RecursiveChunker(**kwargs)

    def chunk(self, text: str) -> list[ChunkedText]:
        chunks = self._chunker.chunk(text)
        return [
            ChunkedText(
                text=getattr(chunk, "text", str(chunk)),
                token_count=getattr(chunk, "token_count", None),
                start_index=getattr(chunk, "start_index", None),
                end_index=getattr(chunk, "end_index", None),
                metadata={"level": getattr(chunk, "level", None)},
            )
            for chunk in chunks
        ]


class ChonkieSemanticAdapter:
    def __init__(self, config: ChunkerConfig) -> None:
        from chonkie import SDPMChunker

        self._chunker = SDPMChunker(
            embedding_model=config.embedding_model or "minishlab/potion-base-8M",
            threshold=config.semantic_threshold,
            chunk_size=config.chunk_size,
            skip_window=1,
        )

    def chunk(self, text: str) -> list[ChunkedText]:
        chunks = self._chunker.chunk(text)
        return [
            ChunkedText(
                text=getattr(chunk, "text", str(chunk)),
                token_count=getattr(chunk, "token_count", None),
                start_index=getattr(chunk, "start_index", None),
                end_index=getattr(chunk, "end_index", None),
                metadata={"sentences": len(getattr(chunk, "sentences", [])) if getattr(chunk, "sentences", None) else None},
            )
            for chunk in chunks
        ]


class ChunkerFactory:
    @staticmethod
    def build(config: ChunkerConfig) -> TextChunker:
        provider = config.provider.lower()
        if provider in {"default", "langchain", "recursive-character"}:
            return DefaultChunker(chunk_size=config.chunk_size, chunk_overlap=config.chunk_overlap)
        if provider in {"chonkie-recursive", "recursive"}:
            return ChonkieRecursiveAdapter(config)
        if provider in {"chonkie-semantic", "semantic", "sdpm"}:
            return ChonkieSemanticAdapter(config)
        raise ValueError(f"Unsupported chunker provider: {config.provider}")

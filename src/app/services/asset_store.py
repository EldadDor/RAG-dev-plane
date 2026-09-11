from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Protocol
from uuid import uuid4


class AssetNotFoundError(FileNotFoundError):
    pass


class AssetStore(Protocol):
    async def put(self, storage_key: str, content: bytes) -> None: ...
    async def read(self, storage_key: str) -> bytes: ...
    async def delete_unreferenced(self, referenced_keys: set[str]) -> int: ...


def _validated_key(storage_key: str) -> str:
    if len(storage_key) != 64 or any(character not in "0123456789abcdef" for character in storage_key):
        raise ValueError("Invalid asset storage key")
    return storage_key


class LocalFileAssetStore:
    """Content-addressed local storage; paths are never exposed to callers."""

    def __init__(self, root: Path) -> None:
        self._root = root.resolve()

    def _path(self, storage_key: str) -> Path:
        key = _validated_key(storage_key)
        return self._root / key[:2] / key

    async def put(self, storage_key: str, content: bytes) -> None:
        path = self._path(storage_key)

        def write() -> None:
            path.parent.mkdir(parents=True, exist_ok=True)
            if path.exists():
                return
            temporary = path.with_name(f".{path.name}.{uuid4().hex}.tmp")
            try:
                temporary.write_bytes(content)
                temporary.replace(path)
            finally:
                temporary.unlink(missing_ok=True)

        await asyncio.to_thread(write)

    async def read(self, storage_key: str) -> bytes:
        path = self._path(storage_key)
        try:
            return await asyncio.to_thread(path.read_bytes)
        except FileNotFoundError as exc:
            raise AssetNotFoundError(storage_key) from exc

    async def delete_unreferenced(self, referenced_keys: set[str]) -> int:
        valid_references = {_validated_key(key) for key in referenced_keys}

        def prune() -> int:
            if not self._root.exists():
                return 0
            removed = 0
            for path in self._root.glob("??/*"):
                if path.is_file() and path.suffix != ".tmp" and path.name not in valid_references:
                    path.unlink()
                    removed += 1
            return removed

        return await asyncio.to_thread(prune)


class InMemoryAssetStore:
    def __init__(self) -> None:
        self.items: dict[str, bytes] = {}

    async def put(self, storage_key: str, content: bytes) -> None:
        self.items[_validated_key(storage_key)] = bytes(content)

    async def read(self, storage_key: str) -> bytes:
        try:
            return self.items[_validated_key(storage_key)]
        except KeyError as exc:
            raise AssetNotFoundError(storage_key) from exc

    async def delete_unreferenced(self, referenced_keys: set[str]) -> int:
        stale = set(self.items) - referenced_keys
        for key in stale:
            del self.items[key]
        return len(stale)

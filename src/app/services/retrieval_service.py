from app.clients.embedding_client import EmbeddingClient
from app.clients.vector_store import VectorStore
from app.config import Settings
from app.domain.models import RetrievedChunk


class RetrievalService:
    def __init__(self, settings: Settings, embedding_client: EmbeddingClient, vector_store: VectorStore) -> None:
        self._settings = settings
        self._embedding_client = embedding_client
        self._vector_store = vector_store

    async def retrieve(self, question: str, top_k: int | None = None) -> list[RetrievedChunk]:
        embedding = await self._embedding_client.create_embedding(self._settings.embedding_model, question)
        return await self._vector_store.search(embedding, limit=top_k or self._settings.top_k)

from fastapi import Depends

from app.clients.chat_client import OpenAICompatibleChatClient
from app.clients.embedding_client import EmbeddingClient, OllamaEmbeddingClient
from app.clients.qdrant_client import QdrantVectorStore
from app.config import Settings, get_settings
from app.services.chat_service import ChatService
from app.services.retrieval_service import RetrievalService


def get_chat_client(settings: Settings = Depends(get_settings)) -> OpenAICompatibleChatClient:
    return OpenAICompatibleChatClient(base_url=settings.chat_base_url, api_key=settings.chat_api_key)


def get_embedding_client(settings: Settings = Depends(get_settings)) -> EmbeddingClient:
    if settings.embedding_provider == "ollama":
        return OllamaEmbeddingClient(base_url=settings.embedding_base_url)
    raise ValueError(f"Unsupported embedding provider: {settings.embedding_provider}")


def get_vector_store(settings: Settings = Depends(get_settings)) -> QdrantVectorStore:
    return QdrantVectorStore(
        url=settings.qdrant_url,
        api_key=settings.qdrant_api_key,
        collection_name=settings.qdrant_collection,
    )


def get_retrieval_service(
    settings: Settings = Depends(get_settings),
    embedding_client: EmbeddingClient = Depends(get_embedding_client),
    vector_store: QdrantVectorStore = Depends(get_vector_store),
) -> RetrievalService:
    return RetrievalService(settings=settings, embedding_client=embedding_client, vector_store=vector_store)


def get_chat_service(
    settings: Settings = Depends(get_settings),
    retrieval_service: RetrievalService = Depends(get_retrieval_service),
    chat_client: OpenAICompatibleChatClient = Depends(get_chat_client),
) -> ChatService:
    return ChatService(settings=settings, retrieval_service=retrieval_service, chat_client=chat_client)

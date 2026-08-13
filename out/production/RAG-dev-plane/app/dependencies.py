from fastapi import Depends, Request

from app.clients.chat_client import ChatClient, OpenAICompatibleChatClient
from app.clients.embedding_client import EmbeddingClient, OllamaEmbeddingClient
from app.clients.qdrant_client import QdrantVectorStore
from app.clients.vector_store import VectorStore
from app.config import Settings, get_settings
from app.services.chat_service import ChatService
from app.services.ingestion_service import IngestionService
from app.services.retrieval_service import RetrievalService


def get_chat_client(settings: Settings = Depends(get_settings)) -> ChatClient:
    if settings.chat_provider == "azure_openai":
        from app.clients.azure_chat_client import AzureOpenAIChatClient
        return AzureOpenAIChatClient(
            endpoint=settings.azure_openai_endpoint or "",
            api_version=settings.azure_openai_api_version,
            api_key=settings.chat_api_key if not settings.azure_openai_use_entra else None,
            use_entra=settings.azure_openai_use_entra,
        )
    return OpenAICompatibleChatClient(base_url=settings.chat_base_url or "", api_key=settings.chat_api_key)


def get_embedding_client(settings: Settings = Depends(get_settings)) -> EmbeddingClient:
    if settings.embedding_provider == "azure_openai":
        from app.clients.azure_embedding_client import AzureOpenAIEmbeddingClient
        return AzureOpenAIEmbeddingClient(
            endpoint=settings.azure_openai_endpoint or "",
            api_version=settings.azure_openai_api_version,
            api_key=settings.embedding_api_key if not settings.azure_openai_use_entra else None,
            use_entra=settings.azure_openai_use_entra,
        )
    if settings.embedding_provider == "ollama":
        return OllamaEmbeddingClient(base_url=settings.embedding_base_url)
    raise ValueError(f"Unsupported embedding provider: {settings.embedding_provider}")


def get_vector_store(request: Request, settings: Settings = Depends(get_settings)) -> VectorStore:
    if settings.vector_store == "postgres":
        # Pool is initialized in lifespan (main.py) and stored in app.state
        return request.app.state.vector_store
    return QdrantVectorStore(
        url=settings.qdrant_url,
        api_key=settings.qdrant_api_key,
        collection_name=settings.qdrant_collection,
    )


def get_retrieval_service(
    settings: Settings = Depends(get_settings),
    embedding_client: EmbeddingClient = Depends(get_embedding_client),
    vector_store: VectorStore = Depends(get_vector_store),
) -> RetrievalService:
    return RetrievalService(settings=settings, embedding_client=embedding_client, vector_store=vector_store)


def get_chat_service(
    settings: Settings = Depends(get_settings),
    retrieval_service: RetrievalService = Depends(get_retrieval_service),
    chat_client: ChatClient = Depends(get_chat_client),
) -> ChatService:
    return ChatService(settings=settings, retrieval_service=retrieval_service, chat_client=chat_client)


def get_ingestion_service(
    settings: Settings = Depends(get_settings),
    embedding_client: EmbeddingClient = Depends(get_embedding_client),
    vector_store: VectorStore = Depends(get_vector_store),
) -> IngestionService:
    return IngestionService(
        settings=settings,
        embedding_client=embedding_client,
        vector_store=vector_store,
    )

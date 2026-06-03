from functools import lru_cache
from pathlib import Path
from typing import Self

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Resolve .env relative to this file's location, walking up to the project root
_ENV_FILE = Path(__file__).resolve().parent.parent.parent/ ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=_ENV_FILE, env_file_encoding="utf-8", extra="ignore")

    # model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = Field(default="local", alias="APP_ENV")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    api_host: str = Field(default="0.0.0.0", alias="API_HOST")
    api_port: int = Field(default=8000, alias="API_PORT")

    # ---- Vector store selection ----
    vector_store: str = Field(default="qdrant", alias="VECTOR_STORE")

    # ---- Qdrant (local dev default) ----
    qdrant_url: str = Field(default="http://localhost:6333", alias="QDRANT_URL")
    qdrant_api_key: str | None = Field(default=None, alias="QDRANT_API_KEY")
    qdrant_collection: str = Field(default="developer_docs", alias="QDRANT_COLLECTION")

    # ---- PostgreSQL + pgvector ----
    pg_host: str | None = Field(default=None, alias="PG_HOST")
    pg_port: int = Field(default=5432, alias="PG_PORT")
    pg_database: str = Field(default="ragdb", alias="PG_DATABASE")
    pg_user: str | None = Field(default=None, alias="PG_USER")
    pg_password: str | None = Field(default=None, alias="PG_PASSWORD")
    pg_sslmode: str = Field(default="require", alias="PG_SSLMODE")
    pg_use_entra: bool = Field(default=False, alias="PG_USE_ENTRA")
    pg_table: str = Field(default="document_chunks", alias="PG_TABLE")
    pg_vector_dim: int = Field(default=1536, alias="PG_VECTOR_DIM")

    # ---- Chat provider ----
    chat_provider: str = Field(default="openai_compatible", alias="CHAT_PROVIDER")
    chat_base_url: str | None = Field(default=None, alias="CHAT_BASE_URL")
    chat_api_key: str = Field(default="dummy", alias="CHAT_API_KEY")
    chat_model: str = Field(default="qwen2.5:7b-instruct-q4_K_M", alias="CHAT_MODEL")

    # ---- Embedding provider ----
    embedding_provider: str = Field(default="ollama", alias="EMBEDDING_PROVIDER")
    embedding_base_url: str = Field(default="http://localhost:11434", alias="EMBEDDING_BASE_URL")
    embedding_api_key: str | None = Field(default=None, alias="EMBEDDING_API_KEY")
    embedding_model: str = Field(default="mxbai-embed-large", alias="EMBEDDING_MODEL")

    # ---- Azure OpenAI (shared by chat + embeddings when using azure_openai provider) ----
    azure_openai_endpoint: str | None = Field(default=None, alias="AZURE_OPENAI_ENDPOINT")
    azure_openai_api_version: str = Field(default="2024-10-21", alias="AZURE_OPENAI_API_VERSION")
    azure_openai_use_entra: bool = Field(default=False, alias="AZURE_OPENAI_USE_ENTRA")

    # ---- RAG tuning ----
    top_k: int = Field(default=5, alias="TOP_K")
    chunk_size: int = Field(default=800, alias="CHUNK_SIZE")
    chunk_overlap: int = Field(default=120, alias="CHUNK_OVERLAP")
    rerank_enabled: bool = Field(default=False, alias="RERANK_ENABLED")

    @model_validator(mode="after")
    def validate_providers(self) -> Self:
        if self.chat_provider == "openai_compatible" and not self.chat_base_url:
            raise ValueError("CHAT_BASE_URL is required when CHAT_PROVIDER=openai_compatible")
        if self.chat_provider == "azure_openai" and not self.azure_openai_endpoint:
            raise ValueError("AZURE_OPENAI_ENDPOINT is required when CHAT_PROVIDER=azure_openai")
        if self.embedding_provider == "azure_openai" and not self.azure_openai_endpoint:
            raise ValueError("AZURE_OPENAI_ENDPOINT is required when EMBEDDING_PROVIDER=azure_openai")
        if self.vector_store == "postgres" and not self.pg_host:
            raise ValueError("PG_HOST is required when VECTOR_STORE=postgres")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()

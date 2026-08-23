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
    auth_mode: str = Field(default="local", alias="AUTH_MODE")
    chat_identity_header: str = Field(default="X-Forwarded-User", alias="CHAT_IDENTITY_HEADER")
    chat_identity_name_header: str = Field(default="X-Forwarded-Name", alias="CHAT_IDENTITY_NAME_HEADER")
    chat_identity_email_header: str = Field(default="X-Forwarded-Email", alias="CHAT_IDENTITY_EMAIL_HEADER")
    local_subject: str = Field(default="local-dev", alias="LOCAL_SUBJECT")
    local_display_name: str = Field(default="Local Developer", alias="LOCAL_DISPLAY_NAME")
    local_email: str | None = Field(default="dev@localhost", alias="LOCAL_EMAIL")
    chat_history_retention_days: int = Field(default=90, alias="CHAT_HISTORY_RETENTION_DAYS", ge=1)

    # ---- Observability (optional Langfuse) ----
    langfuse_enabled: bool = Field(default=False, alias="LANGFUSE_ENABLED")
    langfuse_public_key: str | None = Field(default=None, alias="LANGFUSE_PUBLIC_KEY")
    langfuse_secret_key: str | None = Field(default=None, alias="LANGFUSE_SECRET_KEY")
    langfuse_base_url: str | None = Field(default=None, alias="LANGFUSE_BASE_URL")
    langfuse_capture_content: bool = Field(default=False, alias="LANGFUSE_CAPTURE_CONTENT")

    # ---- Vector store selection ----
    vector_store: str = Field(default="postgres", alias="VECTOR_STORE")

    # ---- Qdrant (local dev alternative) ----
    qdrant_url: str = Field(default="http://localhost:6333", alias="QDRANT_URL")
    qdrant_api_key: str | None = Field(default=None, alias="QDRANT_API_KEY")
    qdrant_collection: str = Field(default="developer_docs", alias="QDRANT_COLLECTION")
    qdrant_check_compatibility: bool = Field(default=True, alias="QDRANT_CHECK_COMPATIBILITY")

    # ---- PostgreSQL + pgvector (matches RAG_Embabel-AI local profile) ----
    pg_host: str | None = Field(default=None, alias="PG_HOST")
    pg_port: int = Field(default=5432, alias="PG_PORT")
    pg_database: str = Field(default="ragdb", alias="PG_DATABASE")
    pg_user: str | None = Field(default=None, alias="PG_USER")
    pg_password: str | None = Field(default=None, alias="PG_PASSWORD")
    pg_sslmode: str = Field(default="disable", alias="PG_SSLMODE")
    pg_use_entra: bool = Field(default=False, alias="PG_USE_ENTRA")
    pg_schema: str = Field(default="rag", alias="PG_SCHEMA")
    pg_table: str = Field(default="document_chunks", alias="PG_TABLE")
    pg_vector_dim: int = Field(default=768, alias="PG_VECTOR_DIM")
    default_workspace_id: str = Field(default="local", alias="DEFAULT_WORKSPACE_ID")

    # ---- Chat provider ----
    chat_provider: str = Field(default="openai_compatible", alias="CHAT_PROVIDER")
    chat_base_url: str | None = Field(default=None, alias="CHAT_BASE_URL")
    chat_api_key: str = Field(default="dummy", alias="CHAT_API_KEY")
    chat_model: str = Field(default="qwen2.5:7b-instruct-q4_K_M", alias="CHAT_MODEL")
    chat_timeout_seconds: float = Field(default=240.0, alias="CHAT_TIMEOUT_SECONDS", gt=0)
    chat_max_tokens: int = Field(default=400, alias="CHAT_MAX_TOKENS", ge=1)
    chat_think: bool = Field(default=False, alias="CHAT_THINK")

    # ---- Embedding provider (matches RAG_Embabel-AI local profile) ----
    embedding_provider: str = Field(default="ollama", alias="EMBEDDING_PROVIDER")
    embedding_base_url: str = Field(default="http://localhost:11434", alias="EMBEDDING_BASE_URL")
    embedding_api_key: str | None = Field(default=None, alias="EMBEDDING_API_KEY")
    embedding_model: str = Field(default="nomic-embed-text", alias="EMBEDDING_MODEL")
    embedding_timeout_seconds: float = Field(default=120.0, alias="EMBEDDING_TIMEOUT_SECONDS", gt=0)

    # ---- Azure OpenAI (shared by chat + embeddings when using azure_openai provider) ----
    azure_openai_endpoint: str | None = Field(default=None, alias="AZURE_OPENAI_ENDPOINT")
    azure_openai_api_version: str = Field(default="2024-10-21", alias="AZURE_OPENAI_API_VERSION")
    azure_openai_use_entra: bool = Field(default=False, alias="AZURE_OPENAI_USE_ENTRA")

    # ---- RAG tuning ----
    top_k: int = Field(default=5, alias="TOP_K")
    chunk_size: int = Field(default=800, alias="CHUNK_SIZE")
    chunk_overlap: int = Field(default=120, alias="CHUNK_OVERLAP")
    rerank_enabled: bool = Field(default=False, alias="RERANK_ENABLED")
    min_retrieval_score: float = Field(default=0.35, alias="MIN_RETRIEVAL_SCORE")
    hybrid_search_enabled: bool = Field(default=True, alias="HYBRID_SEARCH_ENABLED")
    retrieval_candidate_k: int = Field(default=20, alias="RETRIEVAL_CANDIDATE_K")
    rrf_k: int = Field(default=60, alias="RRF_K")

    # ---- Conversation memory ----
    memory_max_turns: int = Field(default=10, alias="MEMORY_MAX_TURNS")
    memory_retention_days: int = Field(default=90, alias="MEMORY_RETENTION_DAYS")
    memory_summary_after_turns: int = Field(default=8, alias="MEMORY_SUMMARY_AFTER_TURNS")

    @model_validator(mode="after")
    def validate_providers(self) -> Self:
        if self.auth_mode not in {"local", "gateway"}:
            raise ValueError("AUTH_MODE must be 'local' or 'gateway'")
        if self.app_env != "local" and self.auth_mode != "gateway":
            raise ValueError("AUTH_MODE=gateway is required outside APP_ENV=local")
        if self.langfuse_enabled and (not self.langfuse_public_key or not self.langfuse_secret_key):
            raise ValueError("LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY are required when LANGFUSE_ENABLED=true")
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

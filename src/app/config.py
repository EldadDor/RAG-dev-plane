from functools import lru_cache
from pathlib import Path

from pydantic import Field
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

    qdrant_url: str = Field(default="http://localhost:6333", alias="QDRANT_URL")
    qdrant_api_key: str | None = Field(default=None, alias="QDRANT_API_KEY")
    qdrant_collection: str = Field(default="developer_docs", alias="QDRANT_COLLECTION")

    chat_provider: str = Field(default="openai_compatible", alias="CHAT_PROVIDER")
    chat_base_url: str = Field(alias="CHAT_BASE_URL")
    chat_api_key: str = Field(default="dummy", alias="CHAT_API_KEY")
    chat_model: str = Field(default="Qwen3-Coder-30B-A3B-Instruct-Q4_K_M", alias="CHAT_MODEL")

    embedding_provider: str = Field(default="ollama", alias="EMBEDDING_PROVIDER")
    embedding_base_url: str = Field(default="http://localhost:11434", alias="EMBEDDING_BASE_URL")
    embedding_api_key: str | None = Field(default=None, alias="EMBEDDING_API_KEY")
    embedding_model: str = Field(default="mxbai-embed-large", alias="EMBEDDING_MODEL")

    top_k: int = Field(default=5, alias="TOP_K")
    chunk_size: int = Field(default=800, alias="CHUNK_SIZE")
    chunk_overlap: int = Field(default=120, alias="CHUNK_OVERLAP")
    rerank_enabled: bool = Field(default=False, alias="RERANK_ENABLED")


@lru_cache
def get_settings() -> Settings:
    return Settings()

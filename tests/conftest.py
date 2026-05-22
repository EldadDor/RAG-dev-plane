import os
import pytest

# Set required env vars before any app module is imported
os.environ.setdefault("CHAT_BASE_URL", "http://localhost:8080/v1")
os.environ.setdefault("CHAT_API_KEY", "dummy")
os.environ.setdefault("CHAT_MODEL", "test-model")
os.environ.setdefault("EMBEDDING_BASE_URL", "http://localhost:11434")
os.environ.setdefault("EMBEDDING_MODEL", "test-embed")
os.environ.setdefault("QDRANT_URL", "http://localhost:6333")
os.environ.setdefault("QDRANT_COLLECTION", "test")

from app.config import Settings
from app.services.observability import Observability


def test_observability_is_noop_when_langfuse_is_disabled():
    settings = Settings(
        LANGFUSE_ENABLED=False,
        CHAT_BASE_URL="http://test/v1",
        VECTOR_STORE="qdrant",
    )

    with Observability(settings).request("chat.request", {"workspace_id": "test"}):
        pass

"""Safe, optional observability boundary for Langfuse."""
from __future__ import annotations

from contextlib import nullcontext
from typing import Any

from app.config import Settings


class Observability:
    def __init__(self, settings: Settings) -> None:
        self._enabled = settings.langfuse_enabled

    def request(self, name: str, metadata: dict[str, Any]):
        """Return a no-op context unless Langfuse tracing is explicitly enabled."""
        if not self._enabled:
            return nullcontext()
        from langfuse import get_client
        return get_client().start_as_current_observation(as_type="span", name=name, metadata=metadata)

"""Short, durable conversation memory for follow-up questions.

This deliberately stores only chat turns. Workplace knowledge remains in the
document index; conversation text is not embedded or mixed into that corpus.
"""

from __future__ import annotations

import asyncio
from collections import defaultdict
from dataclasses import dataclass
from typing import Protocol

import asyncpg


@dataclass(frozen=True)
class ChatTurn:
    role: str
    content: str


class ConversationStore(Protocol):
    async def get(self, session_id: str) -> list[ChatTurn]: ...
    async def append(self, session_id: str, role: str, content: str) -> None: ...


class InMemoryConversationStore:
    """Shared-process fallback for non-PostgreSQL development profiles."""

    def __init__(self, max_turns: int = 10) -> None:
        self._max_turns = max_turns
        self._sessions: dict[str, list[ChatTurn]] = defaultdict(list)
        self._lock = asyncio.Lock()

    async def get(self, session_id: str) -> list[ChatTurn]:
        async with self._lock:
            return list(self._sessions.get(session_id, []))

    async def append(self, session_id: str, role: str, content: str) -> None:
        async with self._lock:
            turns = self._sessions[session_id]
            turns.append(ChatTurn(role=role, content=content))
            self._sessions[session_id] = turns[-self._max_turns:]


class PostgresConversationStore:
    """PostgreSQL-backed memory shared by all API workers."""

    def __init__(
        self,
        pool: asyncpg.Pool,
        schema: str,
        max_turns: int,
        retention_days: int,
    ) -> None:
        self._pool = pool
        self._schema = schema
        self._max_turns = max_turns
        self._retention_days = retention_days

    async def ensure_schema(self) -> None:
        async with self._pool.acquire() as conn:
            await conn.execute(f"CREATE SCHEMA IF NOT EXISTS {self._schema};")
            await conn.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {self._schema}.conversation_turns (
                    id BIGSERIAL PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
                    content TEXT NOT NULL,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
                );
                CREATE INDEX IF NOT EXISTS idx_{self._schema}_conversation_turns_session_created
                    ON {self._schema}.conversation_turns (session_id, created_at DESC, id DESC);
                """
            )

    async def get(self, session_id: str) -> list[ChatTurn]:
        async with self._pool.acquire() as conn:
            # TTL is enforced lazily, avoiding a background worker for this small memory.
            await conn.execute(
                f"DELETE FROM {self._schema}.conversation_turns "
                "WHERE created_at < now() - ($1 * INTERVAL '1 day')",
                self._retention_days,
            )
            rows = await conn.fetch(
                f"""
                SELECT role, content
                FROM (
                    SELECT role, content, created_at, id
                    FROM {self._schema}.conversation_turns
                    WHERE session_id = $1
                    ORDER BY created_at DESC, id DESC
                    LIMIT $2
                ) recent
                ORDER BY created_at ASC, id ASC
                """,
                session_id,
                self._max_turns,
            )
        return [ChatTurn(role=row["role"], content=row["content"]) for row in rows]

    async def append(self, session_id: str, role: str, content: str) -> None:
        if role not in {"user", "assistant"}:
            raise ValueError(f"Unsupported conversation role: {role}")
        async with self._pool.acquire() as conn:
            await conn.execute(
                f"INSERT INTO {self._schema}.conversation_turns (session_id, role, content) VALUES ($1, $2, $3)",
                session_id,
                role,
                content,
            )

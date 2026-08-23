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


class SessionScopeError(ValueError):
    """Raised when a session ID belongs to a different owner or workspace."""


class ConversationStore(Protocol):
    async def get(self, session_id: str) -> list[ChatTurn]: ...
    async def append(self, session_id: str, role: str, content: str) -> None: ...
    async def get_summary(self, session_id: str) -> str | None: ...
    async def get_unsummarized_turns(self, session_id: str) -> list[ChatTurn]: ...
    async def save_summary(self, session_id: str, summary: str) -> None: ...
    async def ensure_session(self, session_id: str, owner_id: str, workspace_id: str, title: str) -> None: ...
    async def update_session(self, session_id: str, owner_id: str, workspace_id: str, preview: str) -> None: ...
    async def list_sessions(self, owner_id: str, workspace_id: str) -> list[dict]: ...
    async def get_session(self, session_id: str, owner_id: str, workspace_id: str | None = None) -> dict | None: ...
    async def rename_session(self, session_id: str, owner_id: str, workspace_id: str, title: str) -> bool: ...
    async def archive_session(self, session_id: str, owner_id: str, workspace_id: str) -> bool: ...


class InMemoryConversationStore:
    """Shared-process fallback for non-PostgreSQL development profiles."""

    def __init__(self, max_turns: int = 10) -> None:
        self._max_turns = max_turns
        self._sessions: dict[str, list[ChatTurn]] = defaultdict(list)
        self._summaries: dict[str, str] = {}
        self._summarized_counts: dict[str, int] = defaultdict(int)
        self._lock = asyncio.Lock()
        self._session_meta: dict[str, dict] = {}

    async def get(self, session_id: str) -> list[ChatTurn]:
        async with self._lock:
            return list(self._sessions.get(session_id, [])[-self._max_turns:])

    async def append(self, session_id: str, role: str, content: str) -> None:
        async with self._lock:
            turns = self._sessions[session_id]
            turns.append(ChatTurn(role=role, content=content))

    async def get_summary(self, session_id: str) -> str | None:
        async with self._lock:
            return self._summaries.get(session_id)

    async def get_unsummarized_turns(self, session_id: str) -> list[ChatTurn]:
        async with self._lock:
            return list(self._sessions.get(session_id, [])[self._summarized_counts[session_id]:])

    async def save_summary(self, session_id: str, summary: str) -> None:
        async with self._lock:
            self._summaries[session_id] = summary
            self._summarized_counts[session_id] = len(self._sessions.get(session_id, []))

    async def ensure_session(self, session_id, owner_id, workspace_id, title):
        async with self._lock:
            existing = self._session_meta.get(session_id)
            if existing and (existing["owner_id"] != owner_id or existing["workspace_id"] != workspace_id):
                raise SessionScopeError("Chat session belongs to a different owner or workspace")
            self._session_meta.setdefault(session_id, {"session_id": session_id, "owner_id": owner_id, "workspace_id": workspace_id, "title": title, "last_preview": None, "archived": False})
    async def update_session(self, session_id, owner_id, workspace_id, preview):
        async with self._lock:
            existing = self._session_meta.get(session_id)
            if existing and existing["owner_id"] == owner_id and existing["workspace_id"] == workspace_id:
                existing["last_preview"] = preview[:300]
    async def list_sessions(self, owner_id, workspace_id):
        async with self._lock: return [v for v in self._session_meta.values() if v["owner_id"] == owner_id and v["workspace_id"] == workspace_id and not v["archived"]]
    async def get_session(self, session_id, owner_id, workspace_id=None):
        async with self._lock:
            v = self._session_meta.get(session_id)
            return v if v and v["owner_id"] == owner_id and (workspace_id is None or v["workspace_id"] == workspace_id) and not v["archived"] else None
    async def rename_session(self, session_id, owner_id, workspace_id, title):
        v = await self.get_session(session_id, owner_id, workspace_id)
        if not v: return False
        v["title"] = title; return True
    async def archive_session(self, session_id, owner_id, workspace_id):
        v = await self.get_session(session_id, owner_id, workspace_id)
        if not v: return False
        v["archived"] = True; return True


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

    async def get_summary(self, session_id: str) -> str | None:
        async with self._pool.acquire() as conn:
            return await conn.fetchval(
                f"SELECT summary FROM {self._schema}.conversation_summaries WHERE session_id = $1",
                session_id,
            )

    async def get_unsummarized_turns(self, session_id: str) -> list[ChatTurn]:
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                f"""
                SELECT role, content
                FROM {self._schema}.conversation_turns
                WHERE session_id = $1
                  AND id > COALESCE(
                      (SELECT last_turn_id FROM {self._schema}.conversation_summaries WHERE session_id = $1),
                      0
                  )
                ORDER BY id ASC
                """,
                session_id,
            )
        return [ChatTurn(role=row["role"], content=row["content"]) for row in rows]

    async def save_summary(self, session_id: str, summary: str) -> None:
        async with self._pool.acquire() as conn:
            last_turn_id = await conn.fetchval(
                f"SELECT COALESCE(MAX(id), 0) FROM {self._schema}.conversation_turns WHERE session_id = $1",
                session_id,
            )
            await conn.execute(
                f"""
                INSERT INTO {self._schema}.conversation_summaries
                    (session_id, summary, last_turn_id)
                VALUES ($1, $2, $3)
                ON CONFLICT (session_id) DO UPDATE SET
                    summary = EXCLUDED.summary,
                    last_turn_id = EXCLUDED.last_turn_id,
                    updated_at = now()
                """,
                session_id,
                summary,
                last_turn_id,
            )
            await conn.execute(f"DELETE FROM {self._schema}.conversation_turns WHERE session_id=$1 AND id < (SELECT id FROM {self._schema}.conversation_turns WHERE session_id=$1 ORDER BY id DESC OFFSET $2 LIMIT 1)", session_id, self._max_turns)

    async def ensure_session(self, session_id, owner_id, workspace_id, title):
        async with self._pool.acquire() as conn:
            await conn.execute(f"INSERT INTO {self._schema}.chat_sessions (session_id, owner_id, workspace_id, title) VALUES ($1,$2,$3,$4) ON CONFLICT (session_id) DO NOTHING", session_id, owner_id, workspace_id, title[:200])
            matches_scope = await conn.fetchval(
                f"SELECT EXISTS(SELECT 1 FROM {self._schema}.chat_sessions WHERE session_id=$1 AND owner_id=$2 AND workspace_id=$3)",
                session_id, owner_id, workspace_id,
            )
            if not matches_scope:
                raise SessionScopeError("Chat session belongs to a different owner or workspace")
    async def update_session(self, session_id, owner_id, workspace_id, preview):
        async with self._pool.acquire() as conn:
            await conn.execute(f"UPDATE {self._schema}.chat_sessions SET last_preview=$4, updated_at=now() WHERE session_id=$1 AND owner_id=$2 AND workspace_id=$3", session_id, owner_id, workspace_id, preview[:300])
    async def list_sessions(self, owner_id, workspace_id):
        async with self._pool.acquire() as conn:
            return [dict(r) for r in await conn.fetch(f"SELECT session_id, workspace_id, title, last_preview, updated_at::text FROM {self._schema}.chat_sessions WHERE owner_id=$1 AND workspace_id=$2 AND NOT archived ORDER BY updated_at DESC", owner_id, workspace_id)]
    async def get_session(self, session_id, owner_id, workspace_id=None):
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(f"SELECT session_id, workspace_id, title, last_preview, updated_at::text FROM {self._schema}.chat_sessions WHERE session_id=$1 AND owner_id=$2 AND ($3::text IS NULL OR workspace_id=$3) AND NOT archived", session_id, owner_id, workspace_id)
            if not row: return None
            result=dict(row); result["summary"] = await conn.fetchval(f"SELECT summary FROM {self._schema}.conversation_summaries WHERE session_id=$1", session_id); result["turns"]=[dict(r) for r in await conn.fetch(f"SELECT role, content FROM {self._schema}.conversation_turns WHERE session_id=$1 ORDER BY id", session_id)]; return result
    async def rename_session(self, session_id, owner_id, workspace_id, title):
        async with self._pool.acquire() as conn: return await conn.execute(f"UPDATE {self._schema}.chat_sessions SET title=$4, updated_at=now() WHERE session_id=$1 AND owner_id=$2 AND workspace_id=$3 AND NOT archived", session_id, owner_id, workspace_id, title[:200]) == "UPDATE 1"
    async def archive_session(self, session_id, owner_id, workspace_id):
        async with self._pool.acquire() as conn: return await conn.execute(f"UPDATE {self._schema}.chat_sessions SET archived=true, updated_at=now() WHERE session_id=$1 AND owner_id=$2 AND workspace_id=$3 AND NOT archived", session_id, owner_id, workspace_id) == "UPDATE 1"

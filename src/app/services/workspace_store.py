"""Workspace discovery and membership authorization stores."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

import asyncpg
from fastapi import HTTPException

from app.identity import Principal


@dataclass(frozen=True)
class AuthorizedWorkspace:
    workspace_id: str
    display_name: str
    role: str


class WorkspaceStore(Protocol):
    async def list_for_subject(self, subject: str) -> list[AuthorizedWorkspace]: ...
    async def is_authorized(self, subject: str, workspace_id: str) -> bool: ...


class InMemoryWorkspaceStore:
    """Local/Qdrant fallback; production membership remains PostgreSQL-backed."""

    def __init__(self, memberships: dict[str, list[AuthorizedWorkspace]] | None = None) -> None:
        self._memberships = memberships or {}

    async def list_for_subject(self, subject: str) -> list[AuthorizedWorkspace]:
        return list(self._memberships.get(subject, []))

    async def is_authorized(self, subject: str, workspace_id: str) -> bool:
        return any(item.workspace_id == workspace_id for item in self._memberships.get(subject, []))


class PostgresWorkspaceStore:
    def __init__(self, pool: asyncpg.Pool, schema: str) -> None:
        self._pool = pool
        self._schema = schema

    async def list_for_subject(self, subject: str) -> list[AuthorizedWorkspace]:
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                f"""
                SELECT workspace.workspace_id, workspace.display_name, member.role
                FROM {self._schema}.workspace_members member
                JOIN {self._schema}.workspaces workspace USING (workspace_id)
                WHERE member.subject = $1
                ORDER BY workspace.display_name, workspace.workspace_id
                """,
                subject,
            )
        return [AuthorizedWorkspace(**dict(row)) for row in rows]

    async def is_authorized(self, subject: str, workspace_id: str) -> bool:
        async with self._pool.acquire() as conn:
            return bool(
                await conn.fetchval(
                    f"SELECT EXISTS(SELECT 1 FROM {self._schema}.workspace_members WHERE subject=$1 AND workspace_id=$2)",
                    subject,
                    workspace_id,
                )
            )


async def require_workspace_access(
    workspace_id: str,
    principal: Principal,
    workspace_store: WorkspaceStore,
) -> str:
    if not await workspace_store.is_authorized(principal.subject, workspace_id):
        raise HTTPException(status_code=403, detail="Not authorized for this workspace")
    return workspace_id

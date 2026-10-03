"""Principal-scoped preferences with explicit persistence guarantees."""

import asyncio
from typing import Literal, Protocol

import asyncpg

RECENT_CHAT_LIMITS = (10, 20, 50, 100)
DEFAULT_RECENT_CHAT_LIMIT = 10
ACCOUNT_HEADERS = {"Cache-Control": "private, no-store", "Vary": "Cookie, Authorization"}
PreferencePersistence = Literal["server", "process", "unavailable"]


class AccountUnavailableError(Exception):
    def __init__(self, resource: Literal["profile", "preferences"] = "preferences") -> None:
        self.code = f"account_{resource}_unavailable"
        self.message = (
            "Account preferences are temporarily unavailable." if resource == "preferences"
            else "Account profile is temporarily unavailable."
        )
        super().__init__(self.message)


class AccountPreferenceStore(Protocol):
    persistence: PreferencePersistence

    async def read(self, subject: str) -> int: ...
    async def update(self, subject: str, recent_chat_limit: int) -> int: ...


def _validate_limit(value: int) -> int:
    if type(value) is not int or value not in RECENT_CHAT_LIMITS:
        raise ValueError("Unsupported recent-chat limit")
    return value


class InMemoryAccountPreferenceStore:
    persistence: PreferencePersistence = "process"

    def __init__(self) -> None:
        self._limits: dict[str, int] = {}
        self._lock = asyncio.Lock()

    async def read(self, subject: str) -> int:
        async with self._lock:
            return self._limits.get(subject, DEFAULT_RECENT_CHAT_LIMIT)

    async def update(self, subject: str, recent_chat_limit: int) -> int:
        value = _validate_limit(recent_chat_limit)
        async with self._lock:
            self._limits[subject] = value
        return value


class UnavailableAccountPreferenceStore:
    persistence: PreferencePersistence = "unavailable"

    async def read(self, subject: str) -> int:
        raise AccountUnavailableError()

    async def update(self, subject: str, recent_chat_limit: int) -> int:
        raise AccountUnavailableError()


class PostgresAccountPreferenceStore:
    persistence: PreferencePersistence = "server"

    def __init__(self, pool: asyncpg.Pool, schema: str) -> None:
        self._pool = pool
        self._schema = schema

    async def read(self, subject: str) -> int:
        try:
            async with self._pool.acquire() as conn:
                value = await conn.fetchval(
                    f"SELECT recent_chat_limit FROM {self._schema}.account_preferences WHERE subject=$1",
                    subject,
                )
        except (asyncpg.PostgresError, asyncpg.InterfaceError, OSError) as exc:
            raise AccountUnavailableError() from exc
        return DEFAULT_RECENT_CHAT_LIMIT if value is None else _validate_limit(value)

    async def update(self, subject: str, recent_chat_limit: int) -> int:
        value = _validate_limit(recent_chat_limit)
        try:
            async with self._pool.acquire() as conn:
                saved = await conn.fetchval(
                    f"""
                    INSERT INTO {self._schema}.account_preferences (subject, recent_chat_limit)
                    VALUES ($1, $2)
                    ON CONFLICT (subject) DO UPDATE
                    SET recent_chat_limit=EXCLUDED.recent_chat_limit, updated_at=now()
                    RETURNING recent_chat_limit
                    """,
                    subject, value,
                )
        except (asyncpg.PostgresError, asyncpg.InterfaceError, OSError) as exc:
            raise AccountUnavailableError() from exc
        return _validate_limit(saved)

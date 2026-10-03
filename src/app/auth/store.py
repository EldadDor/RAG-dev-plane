"""Encrypted gateway records with atomic consumption and session admission."""

import asyncio
from dataclasses import dataclass, replace
from datetime import datetime, timedelta
from typing import Literal, Protocol

import asyncpg

Kind = Literal["session", "bootstrap", "login"]


class StoreUnavailable(Exception):
    """Never fall back to unauthenticated access or a different store."""


@dataclass(frozen=True)
class Record:
    token_hash: str
    kind: Kind
    payload: str
    created_at: datetime
    last_seen: datetime
    expires_at: datetime
    revoked: bool = False


class SessionStore(Protocol):
    async def put(self, record: Record, now: datetime) -> None: ...
    async def get(self, token_hash: str, kind: Kind, now: datetime) -> Record | None: ...
    async def consume(self, token_hash: str, kind: Kind, now: datetime) -> Record | None: ...
    async def admit(self, token_hash: str, now: datetime, idle: int) -> Record | None: ...
    async def revoke(self, token_hash: str) -> None: ...
    async def cleanup(self, now: datetime) -> int: ...


class MemorySessionStore:
    def __init__(self, max_records: int = 10000):
        self._records: dict[str, Record] = {}
        self._lock = asyncio.Lock()
        self._limit = max_records

    def _cleanup(self, now: datetime) -> int:
        expired = [key for key, row in self._records.items() if row.expires_at <= now]
        for key in expired:
            del self._records[key]
        return len(expired)

    async def cleanup(self, now: datetime) -> int:
        async with self._lock:
            return self._cleanup(now)

    async def put(self, record: Record, now: datetime) -> None:
        async with self._lock:
            self._cleanup(now)
            if len(self._records) >= self._limit or record.token_hash in self._records:
                raise StoreUnavailable()
            self._records[record.token_hash] = record

    async def get(self, token_hash: str, kind: Kind, now: datetime) -> Record | None:
        async with self._lock:
            row = self._records.get(token_hash)
            return row if row and row.kind == kind and row.expires_at > now else None

    async def consume(self, token_hash: str, kind: Kind, now: datetime) -> Record | None:
        async with self._lock:
            row = self._records.get(token_hash)
            if not row or row.kind != kind or row.expires_at <= now or row.revoked:
                return None
            del self._records[token_hash]
            return row

    async def admit(self, token_hash: str, now: datetime, idle: int) -> Record | None:
        async with self._lock:
            row = self._records.get(token_hash)
            if (not row or row.kind != "session" or row.revoked or row.expires_at <= now
                    or row.last_seen + timedelta(seconds=idle) <= now):
                return None
            row = replace(row, last_seen=max(row.last_seen, now))
            self._records[token_hash] = row
            return row

    async def revoke(self, token_hash: str) -> None:
        async with self._lock:
            row = self._records.get(token_hash)
            if row and row.kind == "session":
                self._records[token_hash] = replace(row, revoked=True)


class PostgresSessionStore:
    def __init__(self, pool: asyncpg.Pool, schema: str, max_records: int = 10000):
        # Identifier interpolation is permitted only after validation.
        import re
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", schema):
            raise ValueError("Invalid gateway schema")
        self.pool = pool
        self.table = f'"{schema}".auth_sessions'
        self.schema = schema
        self._limit = max_records

    @staticmethod
    def _record(row) -> Record | None:
        return Record(**dict(row)) if row else None

    async def validate(self) -> None:
        async with self.pool.acquire() as conn:
            if not await conn.fetchval("SELECT to_regclass($1)", self.table):
                raise StoreUnavailable()
            if not await conn.fetchval(
                f'SELECT EXISTS(SELECT 1 FROM "{self.schema}".schema_migrations WHERE version=$1)',
                "009_auth_sessions",
            ):
                raise StoreUnavailable()

    async def cleanup(self, now: datetime) -> int:
        async with self.pool.acquire() as conn:
            result = await conn.execute(f"DELETE FROM {self.table} WHERE expires_at <= $1", now)
            return int(result.split()[-1])

    async def put(self, record: Record, now: datetime) -> None:
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                # Serialize capacity checks across replicas, without session reads caching.
                await conn.execute("SELECT pg_advisory_xact_lock(hashtext($1)::bigint)", self.table)
                await conn.execute(f"DELETE FROM {self.table} WHERE expires_at <= $1", now)
                if await conn.fetchval(f"SELECT count(*) FROM {self.table}") >= self._limit:
                    raise StoreUnavailable()
                await conn.execute(
                    f"INSERT INTO {self.table} (token_hash,kind,payload,created_at,last_seen,expires_at,revoked) "
                    "VALUES ($1,$2,$3,$4,$5,$6,$7)",
                    record.token_hash, record.kind, record.payload, record.created_at,
                    record.last_seen, record.expires_at, record.revoked,
                )

    async def get(self, token_hash: str, kind: Kind, now: datetime) -> Record | None:
        async with self.pool.acquire() as conn:
            return self._record(await conn.fetchrow(
                f"SELECT * FROM {self.table} WHERE token_hash=$1 AND kind=$2 AND expires_at>$3",
                token_hash, kind, now,
            ))

    async def consume(self, token_hash: str, kind: Kind, now: datetime) -> Record | None:
        async with self.pool.acquire() as conn:
            return self._record(await conn.fetchrow(
                f"DELETE FROM {self.table} WHERE token_hash=$1 AND kind=$2 "
                "AND expires_at>$3 AND NOT revoked RETURNING *", token_hash, kind, now,
            ))

    async def admit(self, token_hash: str, now: datetime, idle: int) -> Record | None:
        async with self.pool.acquire() as conn:
            return self._record(await conn.fetchrow(
                f"UPDATE {self.table} SET last_seen=GREATEST(last_seen,$2) WHERE token_hash=$1 "
                "AND kind='session' AND NOT revoked AND expires_at>$2 "
                "AND last_seen>$2-($3 * interval '1 second') RETURNING *",
                token_hash, now, idle,
            ))

    async def revoke(self, token_hash: str) -> None:
        async with self.pool.acquire() as conn:
            await conn.execute(
                f"UPDATE {self.table} SET revoked=true WHERE token_hash=$1 AND kind='session'", token_hash,
            )

"""Read-only document discovery and shared publication metadata primitives."""
from __future__ import annotations

import base64
import binascii
import hashlib
import hmac
import json
import re
import time
import unicodedata
from datetime import datetime, timezone
from pathlib import PurePosixPath, PureWindowsPath
from typing import Any
from contextlib import asynccontextmanager

import asyncpg

from app.api.schemas import DocumentListResponse, DocumentScope, DocumentPage, DocumentSummary


DOCUMENT_TYPES = frozenset({"word", "pdf", "markdown", "html", "text", "code", "unknown"})
DOCUMENT_HEADERS = {"Cache-Control": "private, no-store", "Vary": "Cookie, Authorization"}
_IDENTIFIER = re.compile(r"^[a-z_][a-z0-9_]*$")


class PinnedConnectionPool:
    """Sequential adapters reuse a session lock owner's connection.

    Borrowing another pool connection while writers wait on this session's
    locks can exhaust the pool and deadlock warming/backfill.
    """
    def __init__(self, connection):
        self.connection = connection

    @asynccontextmanager
    async def acquire(self):
        yield self.connection


class DocumentListError(Exception):
    def __init__(self, status: int):
        self.status = status
        super().__init__("Document list request failed")


def safe_display_metadata(document: dict) -> dict[str, str]:
    """Only display text is public; paths/loader metadata never leave this layer."""
    def clean(value: str, maximum: int) -> str:
        # Cf includes bidi overrides/isolates and invisible formatting controls.
        value = "".join(" " if c.isspace() else c for c in value
                        if c.isspace() or unicodedata.category(c) not in {"Cc", "Cf"})
        return " ".join(value.split())[:maximum]

    path = str(document.get("source_path") or "")
    name = clean(path.replace("\\", "/").rsplit("/", 1)[-1], 255) or "Untitled document"
    title = str(document.get("title") or "")
    if PureWindowsPath(title).is_absolute() or PurePosixPath(title).is_absolute():
        title = ""
    title = clean(title, 300) or name
    kind = document.get("source_type", document.get("document_type"))
    return {"title": title, "file_name": name,
            "document_type": kind if isinstance(kind, str) and kind in DOCUMENT_TYPES else "unknown"}


def profile_lock_key(schema: str, profile: str) -> str:
    return f"document-publication:{schema}:{profile}"


async def lock_publication(conn: Any, schema: str, profile: str) -> None:
    """Writers coordinate with long-running warm/backfill sessions."""
    await conn.execute("SELECT pg_advisory_xact_lock(hashtextextended($1, 0))",
                       profile_lock_key(schema, profile))


async def lock_document(conn: Any, schema: str, workspace: str, chunking: str, doc_id: str) -> None:
    # Shared source/asset cleanup must also serialize across model profiles.
    key = json.dumps(["document", schema, workspace, chunking, doc_id], separators=(",", ":"))
    await conn.execute("SELECT pg_advisory_xact_lock(hashtextextended($1,0))", key)


async def bump_revision(conn: Any, schema: str, workspace: str, model: str, chunking: str) -> None:
    await conn.execute(
        f"""INSERT INTO {schema}.document_list_revisions
            (workspace_id, model_profile, chunking_profile, revision) VALUES ($1,$2,$3,1)
            ON CONFLICT (workspace_id, model_profile, chunking_profile)
            DO UPDATE SET revision={schema}.document_list_revisions.revision+1,
                          updated_at=clock_timestamp()""", workspace, model, chunking)


async def publish_metadata(conn: Any, schema: str, table: str, model: str, document: dict,
                           *, preserve_time: bool = False) -> None:
    workspace, chunking, doc_id = (document["workspace_id"], document["chunking_profile"], document["doc_id"])
    display = safe_display_metadata(document)
    old_public = await conn.fetchrow(
        f"""SELECT title,file_name,document_type,last_ingested_at,indexed_chunk_count
            FROM {schema}.document_index_metadata
            WHERE workspace_id=$1 AND model_profile=$2 AND chunking_profile=$3 AND doc_id=$4""",
        workspace, model, chunking, doc_id)
    count = await conn.fetchval(
        f"""SELECT count(*) FROM {schema}.{table}
            WHERE metadata->>'workspace_id'=$1 AND metadata->>'doc_id'=$2
            AND COALESCE(metadata->>'chunking_profile','default')=$3""", workspace, doc_id, chunking)
    ingested_at = document.get("last_ingested_at") if preserve_time else await conn.fetchval("SELECT clock_timestamp()")
    changed = await conn.fetchval(
        f"""INSERT INTO {schema}.document_index_metadata AS current
            (workspace_id,model_profile,chunking_profile,doc_id,title,file_name,document_type,
             content_hash,last_ingested_at,indexed_chunk_count,source_path,root_path)
            VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12)
            ON CONFLICT (workspace_id,model_profile,chunking_profile,doc_id) DO UPDATE SET
                title=EXCLUDED.title, file_name=EXCLUDED.file_name,
                document_type=EXCLUDED.document_type, content_hash=EXCLUDED.content_hash,
                last_ingested_at=EXCLUDED.last_ingested_at,
                indexed_chunk_count=EXCLUDED.indexed_chunk_count,
                source_path=EXCLUDED.source_path, root_path=EXCLUDED.root_path,
                updated_at=clock_timestamp()
            WHERE (current.title,current.file_name,current.document_type,current.content_hash,
                   current.last_ingested_at,current.indexed_chunk_count,current.source_path,current.root_path)
                IS DISTINCT FROM
                  (EXCLUDED.title,EXCLUDED.file_name,EXCLUDED.document_type,EXCLUDED.content_hash,
                   EXCLUDED.last_ingested_at,EXCLUDED.indexed_chunk_count,EXCLUDED.source_path,EXCLUDED.root_path)
            RETURNING 1""",
        workspace, model, chunking, doc_id, display["title"], display["file_name"], display["document_type"],
        document.get("content_hash"), ingested_at, count, document["source_path"], document.get("root_path"))
    public_values = {**display, "last_ingested_at": ingested_at, "indexed_chunk_count": count}
    if changed and (old_public is None or dict(old_public) != public_values):
        await bump_revision(conn, schema, workspace, model, chunking)


class DocumentCursor:
    """Authenticated, bounded continuation token; never an authorization grant."""
    def __init__(self, secret: str):
        self.key = secret.encode()

    def subject(self, subject: str) -> str:
        return hmac.new(self.key, b"subject\0" + subject.encode(), hashlib.sha256).hexdigest()

    def encode(self, payload: dict) -> str:
        data = base64.urlsafe_b64encode(json.dumps(payload, separators=(",", ":"), sort_keys=True).encode()).rstrip(b"=")
        signature = hmac.new(self.key, data, hashlib.sha256).hexdigest()
        return data.decode() + "." + signature

    def decode(self, token: str) -> dict:
        try:
            if not 1 <= len(token) <= 4096:
                raise ValueError()
            data, signature = token.split(".")
            if not re.fullmatch(r"[A-Za-z0-9_-]+", data):
                raise ValueError()
            if not hmac.compare_digest(hmac.new(self.key, data.encode(), hashlib.sha256).hexdigest(), signature):
                raise ValueError()
            value = json.loads(base64.b64decode(data + "=" * (-len(data) % 4), altchars=b"-_", validate=True))
            if not isinstance(value, dict) or type(value.get("v")) is not int or value["v"] != 1:
                raise ValueError()
            for field in ("workspace", "model", "chunking", "subject", "revision", "last_id"):
                if not isinstance(value.get(field), str) or not value[field]:
                    raise ValueError()
            if not value["revision"].isdigit():
                raise ValueError()
            if type(value.get("limit")) is not int or not 1 <= value["limit"] <= 100:
                raise ValueError()
            for field in ("issued", "expires"):
                if type(value.get(field)) is not int:
                    raise ValueError()
            if value["expires"] - value["issued"] != 900 or value["issued"] > int(time.time()) + 30:
                raise ValueError()
            if value.get("last_time") is not None:
                parsed = datetime.fromisoformat(value["last_time"])
                if parsed.tzinfo is None:
                    raise ValueError()
            return value
        except DocumentListError:
            raise
        except (ValueError, TypeError, KeyError, binascii.Error, OverflowError) as exc:
            raise DocumentListError(422) from exc


class PostgresDocumentCatalog:
    def __init__(self, pool: asyncpg.Pool, schema: str):
        if not _IDENTIFIER.fullmatch(schema):
            raise ValueError("Invalid schema")
        self.pool, self.schema = pool, schema

    async def page(self, workspace: str, model: str, chunking: str, limit: int,
                   cursor: dict | None) -> tuple[str, list[dict]]:
        try:
            async with self.pool.acquire() as conn:
                async with conn.transaction(isolation="repeatable_read", readonly=True):
                    if not await conn.fetchval(f"SELECT ready FROM {self.schema}.document_catalog_state WHERE singleton=TRUE"):
                        raise DocumentListError(503)
                    revision = str(await conn.fetchval(
                        f"""SELECT revision FROM {self.schema}.document_list_revisions
                            WHERE workspace_id=$1 AND model_profile=$2 AND chunking_profile=$3""",
                        workspace, model, chunking) or 0)
                    if cursor and cursor["revision"] != revision:
                        raise DocumentListError(409)
                    # Recheck profile readiness in the same snapshot as the page.
                    if await conn.fetchval(f"SELECT status FROM {self.schema}.model_profiles WHERE profile_name=$1", model) != "ready":
                        raise DocumentListError(503)
                    last_id = cursor["last_id"] if cursor else None
                    last_time = datetime.fromisoformat(cursor["last_time"]) if cursor and cursor["last_time"] else None
                    rows = await conn.fetch(
                        f"""SELECT doc_id,title,file_name,document_type,last_ingested_at,indexed_chunk_count
                            FROM {self.schema}.document_index_metadata
                            WHERE workspace_id=$1 AND model_profile=$2 AND chunking_profile=$3
                            AND ($4::text IS NULL OR
                                 ($5::timestamptz IS NULL AND last_ingested_at IS NULL AND doc_id COLLATE "C">$4 COLLATE "C") OR
                                 ($5::timestamptz IS NOT NULL AND
                                  (last_ingested_at IS NULL OR last_ingested_at<$5 OR
                                   (last_ingested_at=$5 AND doc_id COLLATE "C">$4 COLLATE "C"))))
                            ORDER BY last_ingested_at DESC NULLS LAST, doc_id COLLATE "C" ASC LIMIT $6""",
                        workspace, model, chunking, last_id, last_time, limit + 1)
                    return revision, [dict(row) for row in rows]
        except (asyncpg.PostgresError, asyncpg.InterfaceError, OSError, TimeoutError) as exc:
            raise DocumentListError(503) from exc


class DocumentCatalogService:
    def __init__(self, settings: Any, store: Any, profiles: Any, cursors: DocumentCursor):
        self.settings, self.store, self.profiles, self.cursors = settings, store, profiles, cursors

    async def list(self, workspace: str, subject: str, limit: int = 25, cursor: str | None = None,
                   model_profile: str | None = None, chunking_profile: str | None = None) -> DocumentListResponse:
        if not self.settings.document_list_enabled or self.store is None or self.profiles is None:
            raise DocumentListError(503)
        token = self.cursors.decode(cursor) if cursor is not None else None
        model = model_profile or self.settings.model_profile
        try:
            chunking, _ = self.settings.chunking_profile(chunking_profile)
        except ValueError as exc:
            raise DocumentListError(422 if chunking_profile else 503) from exc
        if token:
            if token["workspace"] != workspace or token["subject"] != self.cursors.subject(subject) or token["limit"] != limit:
                raise DocumentListError(422)
            if token["model"] != model or token["chunking"] != chunking:
                explicit_change = ((token["model"] != model and model_profile is not None) or
                                   (token["chunking"] != chunking and chunking_profile is not None))
                raise DocumentListError(422 if explicit_change else 409)
            if time.time() >= token["expires"]:
                raise DocumentListError(409)
        try:
            profile = await self.profiles.get(model)
        except (asyncpg.PostgresError, asyncpg.InterfaceError, OSError, TimeoutError) as exc:
            raise DocumentListError(503) from exc
        if profile is None or profile.status != "ready" or profile.provider != self.settings.embedding_provider:
            raise DocumentListError(422 if model_profile else 503)
        revision, rows = await self.store.page(workspace, model, chunking, limit, token)
        has_more = len(rows) > limit
        rows = rows[:limit]
        next_cursor = None
        if has_more:
            now = int(time.time())
            last = rows[-1]
            next_cursor = self.cursors.encode({
                "v": 1, "workspace": workspace, "model": model, "chunking": chunking,
                "subject": self.cursors.subject(subject), "limit": limit, "revision": revision,
                "last_id": last["doc_id"],
                "last_time": last["last_ingested_at"].isoformat() if last["last_ingested_at"] else None,
                "issued": token["issued"] if token else now,
                "expires": token["expires"] if token else now + 900,
            })
        return DocumentListResponse(
            workspace_id=workspace, scope=DocumentScope(model_profile=model, chunking_profile=chunking),
            items=[DocumentSummary(**row) for row in rows],
            page=DocumentPage(limit=limit, has_more=has_more, next_cursor=next_cursor,
                              list_revision=revision, generated_at=datetime.now(timezone.utc)))

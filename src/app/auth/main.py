"""Gateway ASGI factory: uvicorn app.auth.main:create_gateway --factory."""

import hashlib
import hmac
import json
import logging
import re
import secrets
from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta
from typing import Callable

import asyncpg
import httpx
from cryptography.fernet import Fernet, InvalidToken
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, RedirectResponse, Response
from pydantic import BaseModel, ConfigDict
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.auth.config import GatewaySettings
from app.auth.oidc import EntraProvider, LoginProvider
from app.auth.store import MemorySessionStore, PostgresSessionStore, Record, SessionStore, StoreUnavailable

PRIVATE = {"Cache-Control": "private, no-store", "Vary": "Cookie, Authorization"}
DEV_IDENTITIES = {
    "local-dev": {"subject": "local-dev", "display_name": "Local Developer", "email": "dev@localhost"},
    "local-test-2": {"subject": "local-test-2", "display_name": "Local Test User 2", "email": None},
}
SAFE_ERRORS = {
    400: ("invalid_auth_request", "The authentication request is invalid."),
    401: ("authentication_required", "Authentication is required."),
    403: ("auth_request_denied", "The authentication request is not permitted."),
    404: ("resource_not_found", "The requested resource was not found."),
    405: ("method_not_allowed", "The request method is not allowed."),
    413: ("request_too_large", "The authentication request is too large."),
    415: ("unsupported_media_type", "The authentication request requires JSON."),
    422: ("invalid_request", "The request is invalid."),
    500: ("internal_error", "An unexpected server error occurred."),
    503: ("auth_unavailable", "Authentication is temporarily unavailable."),
}


def digest(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def opaque_cookie(request: Request, name: str) -> str:
    value = request.cookies.get(name, "")
    return value if re.fullmatch(r"[A-Za-z0-9_-]{43}", value) else ""


def error(status: int) -> JSONResponse:
    code, message = SAFE_ERRORS.get(status, SAFE_ERRORS[500])
    return JSONResponse({"code": code, "message": message}, status_code=status, headers=PRIVATE)


class DevLogin(BaseModel):
    model_config = ConfigDict(extra="forbid")
    identity: str


def create_gateway(
    settings: GatewaySettings | None = None,
    store: SessionStore | None = None,
    provider: LoginProvider | None = None,
    clock: Callable[[], datetime] | None = None,
) -> FastAPI:
    settings = settings or GatewaySettings()
    clock = clock or (lambda: datetime.now(UTC))
    cipher = Fernet(
        settings.encryption_key.get_secret_value().encode() if settings.encryption_key else Fernet.generate_key()
    )
    # OAuth client DEBUG logs can include PKCE data; HTTP client logs can include callback URLs.
    for name in ("authlib", "httpx", "httpcore", "httpx2", "httpcore2"):
        logging.getLogger(name).setLevel(logging.WARNING)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        pool = None
        if app.state.store is None:
            if settings.store == "memory":
                app.state.store = MemorySessionStore(settings.max_records)
            else:
                try:
                    pool = await asyncpg.create_pool(
                        settings.database_url.get_secret_value(), min_size=1, max_size=5, command_timeout=10,
                    )
                    app.state.store = PostgresSessionStore(pool, settings.pg_schema, settings.max_records)
                    await app.state.store.validate()
                except Exception:
                    if pool:
                        await pool.close()
                    # Do not emit connection-string/provider details through startup errors.
                    raise RuntimeError("Gateway store unavailable; verify migration 009 and credentials") from None
        try:
            yield
        finally:
            if pool:
                await pool.close()
            app.state.store = None

    app = FastAPI(title="RAG Authentication Gateway", lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None)
    app.state.store = store
    app.state.provider = provider or (EntraProvider(settings) if settings.provider == "entra" else None)

    def database() -> SessionStore:
        if app.state.store is None:
            raise StoreUnavailable()
        return app.state.store

    def encode(payload: dict) -> str:
        return cipher.encrypt(json.dumps(payload).encode()).decode()

    def decode(row: Record) -> dict:
        try:
            return json.loads(cipher.decrypt(row.payload.encode()))
        except (InvalidToken, ValueError, TypeError):
            raise StoreUnavailable() from None

    async def create_record(kind, payload: dict, lifetime: int) -> tuple[str, Record]:
        token = secrets.token_urlsafe(32)
        now = clock()
        row = Record(digest(token), kind, encode(payload), now, now, now + timedelta(seconds=lifetime))
        await database().put(row, now)
        return token, row

    def set_cookie(response: Response, name: str, token: str, seconds: int) -> None:
        response.set_cookie(name, token, max_age=seconds, path="/", secure=settings.cookie_secure,
                            httponly=True, samesite=settings.cookie_samesite)

    def clear_cookie(response: Response, name: str) -> None:
        response.delete_cookie(name, path="/", secure=settings.cookie_secure,
                               httponly=True, samesite=settings.cookie_samesite)

    context_cookie = settings.cookie_name + "_context"
    login_cookie = settings.cookie_name + "_login"

    async def session(request: Request, include_inactive: bool = False) -> Record | None:
        row = await database().get(digest(opaque_cookie(request, settings.cookie_name)), "session", clock())
        if row and not include_inactive and (
            row.revoked or row.last_seen + timedelta(seconds=settings.idle_seconds) <= clock()
        ):
            return None
        return row

    async def csrf_context(request: Request) -> Record | None:
        # Revoked/idle-expired sessions support safe logout retries until absolute expiry.
        row = await session(request, include_inactive=True)
        return row or await database().get(digest(opaque_cookie(request, context_cookie)), "bootstrap", clock())

    def validate_csrf(request: Request, row: Record | None) -> None:
        if request.headers.get("origin") != settings.public_origin or row is None:
            raise HTTPException(403)
        token = request.headers.get("x-csrf-token", "")
        if not hmac.compare_digest(digest(token), decode(row)["csrf_hash"]):
            raise HTTPException(403)

    async def finish_login(request: Request, identity: dict, return_to: str) -> Response:
        # New state is durable before the previous session is revoked; failure yields no new cookie.
        csrf = secrets.token_urlsafe(32)
        token, _ = await create_record(
            "session", {**identity, "csrf": csrf, "csrf_hash": digest(csrf)}, settings.absolute_seconds,
        )
        try:
            await database().revoke(digest(opaque_cookie(request, settings.cookie_name)))
        except Exception:
            await database().revoke(digest(token))
            raise
        response = RedirectResponse(return_to, status_code=303)
        set_cookie(response, settings.cookie_name, token, settings.absolute_seconds)
        clear_cookie(response, login_cookie)
        clear_cookie(response, context_cookie)
        return response

    @app.middleware("http")
    async def privacy(request: Request, call_next):
        try:
            response = await call_next(request)
        except (StoreUnavailable, asyncpg.PostgresError, asyncpg.InterfaceError, OSError, TimeoutError):
            response = error(503)
        except Exception:
            response = error(500)
        response.headers.update(PRIVATE)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        return response

    @app.exception_handler(StarletteHTTPException)
    async def http_error(_: Request, exc: StarletteHTTPException):
        return error(exc.status_code)

    @app.exception_handler(RequestValidationError)
    async def invalid_request(_: Request, __: RequestValidationError):
        return error(422)

    @app.get("/auth/session")
    async def session_status(request: Request):
        if request.query_params:
            raise HTTPException(422)
        row = await session(request)
        if row:
            payload = decode(row)
            return JSONResponse({
                "authenticated": True,
                "profile": {"display_name": payload["display_name"], "email": payload.get("email")},
                "csrf_token": payload["csrf"], "idle_expires_at": (row.last_seen + timedelta(seconds=settings.idle_seconds)).isoformat(),
                "absolute_expires_at": row.expires_at.isoformat(), "persistence": settings.store,
            })
        bootstrap = await database().get(digest(opaque_cookie(request, context_cookie)), "bootstrap", clock())
        token = None
        if bootstrap is None:
            csrf = secrets.token_urlsafe(32)
            token, bootstrap = await create_record("bootstrap", {"csrf": csrf, "csrf_hash": digest(csrf)}, 300)
        response = JSONResponse({
            "authenticated": False, "profile": None, "csrf_token": decode(bootstrap)["csrf"],
            "idle_expires_at": None, "absolute_expires_at": None, "persistence": settings.store,
        })
        if token:
            set_cookie(response, context_cookie, token, 300)
        clear_cookie(response, settings.cookie_name)
        return response

    @app.get("/auth/login")
    async def login(request: Request):
        if set(request.query_params) - {"return_to"} or len(request.query_params.getlist("return_to")) > 1:
            raise HTTPException(422)
        return_to = request.query_params.get("return_to", "/")
        if return_to not in settings.return_paths:
            raise HTTPException(400)
        if settings.provider == "dev":
            # Selection is an explicit POST; GET never creates a development session.
            return JSONResponse({"provider": "dev", "identities": [
                {"identity": key, "display_name": value["display_name"]} for key, value in DEV_IDENTITIES.items()
            ], "session_url": "/auth/session", "login_url": "/auth/dev-login"})
        try:
            transaction = await app.state.provider.begin()
        except Exception:
            raise HTTPException(503) from None
        transaction["return_to"] = return_to
        # The cookie binds the callback to the initiating browser, not just its query state.
        token, _ = await create_record("login", transaction, 300)
        previous = opaque_cookie(request, login_cookie)
        if previous:
            await database().consume(digest(previous), "login", clock())
        response = RedirectResponse(transaction["url"], status_code=302)
        set_cookie(response, login_cookie, token, 300)
        return response

    @app.get("/auth/callback")
    async def callback(request: Request):
        if settings.provider != "entra":
            raise HTTPException(404)
        if any(len(request.query_params.getlist(key)) > 1 for key in request.query_params):
            raise HTTPException(400)
        row = await database().consume(digest(opaque_cookie(request, login_cookie)), "login", clock())
        if not row:
            raise HTTPException(400)
        transaction = decode(row)
        state = request.query_params.get("state", "")
        code = request.query_params.get("code", "")
        if (not hmac.compare_digest(digest(state), digest(transaction["state"])) or not code or len(code) > 4096
                or request.query_params.get("error")):
            raise HTTPException(400)
        try:
            identity = await app.state.provider.finish(transaction, code)
            # Header values must be printable ASCII; display fields are UTF-8 encoded by
            # the internal header contract below, preserving Unicode without header injection.
            if not identity.get("subject"):
                raise ValueError("Missing principal")
        except httpx.HTTPError:
            raise HTTPException(503) from None
        except Exception:
            raise HTTPException(400) from None
        return await finish_login(request, identity, transaction["return_to"])

    @app.post("/auth/dev-login")
    async def dev_login(request: Request):
        if settings.provider != "dev":
            raise HTTPException(404)
        row = await csrf_context(request)
        validate_csrf(request, row)
        if request.query_params:
            raise HTTPException(422)
        if request.headers.get("content-type", "").split(";", 1)[0].strip().lower() != "application/json":
            raise HTTPException(415)
        content = bytearray()
        async for chunk in request.stream():
            content.extend(chunk)
            if len(content) > 4096:
                raise HTTPException(413)
        try:
            body = DevLogin.model_validate_json(content)
        except ValueError:
            raise HTTPException(422) from None
        if body.identity not in DEV_IDENTITIES:
            raise HTTPException(422)
        if row.kind == "bootstrap" and not await database().consume(row.token_hash, "bootstrap", clock()):
            raise HTTPException(403)
        return await finish_login(request, DEV_IDENTITIES[body.identity], "/")

    @app.post("/auth/logout")
    async def logout(request: Request):
        if request.query_params:
            raise HTTPException(422)
        validate_csrf(request, await csrf_context(request))
        await database().revoke(digest(opaque_cookie(request, settings.cookie_name)))
        await database().consume(digest(opaque_cookie(request, login_cookie)), "login", clock())
        response = Response(status_code=204)
        clear_cookie(response, settings.cookie_name)
        clear_cookie(response, login_cookie)
        return response

    @app.get("/internal/authorize")
    async def authorize(request: Request):
        if not hmac.compare_digest(
            request.headers.get("x-auth-proxy-secret", "").encode(), settings.proxy_secret.get_secret_value().encode(),
        ):
            raise HTTPException(403)
        row = await session(request)
        if not row:
            raise HTTPException(401)
        method = request.headers.get("x-original-method", "")
        if method not in {"GET", "HEAD", "POST", "PATCH", "PUT", "DELETE", "OPTIONS"}:
            raise HTTPException(400)
        if method not in {"GET", "HEAD", "OPTIONS"}:
            validate_csrf(request, row)
        row = await database().admit(row.token_hash, clock(), settings.idle_seconds)
        if not row:
            raise HTTPException(401)
        payload = decode(row)
        # Percent encoding is decoded only in the explicit NP-24 gateway identity mode.
        from urllib.parse import quote
        headers = {
            "X-Forwarded-User": quote(payload["subject"], safe=""),
            "X-Forwarded-Name": quote(payload["display_name"], safe=""),
            "X-Forwarded-Email": quote(payload.get("email") or "", safe=""),
        }
        return Response(status_code=204, headers=headers)

    return app

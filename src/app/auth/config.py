"""Fail-closed gateway policy, independent of RAG provider configuration."""

import re
from typing import Literal, Self
from urllib.parse import parse_qs, urlsplit
from uuid import UUID

from cryptography.fernet import Fernet
from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class GatewaySettings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore", hide_input_in_errors=True)

    app_env: str = Field(default="local", alias="APP_ENV")
    provider: Literal["dev", "entra"] = Field(default="dev", alias="AUTH_PROVIDER")
    public_origin: str = Field(default="http://localhost:8080", alias="AUTH_PUBLIC_ORIGIN")
    store: Literal["memory", "postgres"] = Field(default="memory", alias="AUTH_SESSION_STORE")
    cookie_name: str = Field(default="rag_session_dev", alias="AUTH_COOKIE_NAME")
    cookie_secure: bool = Field(default=False, alias="AUTH_COOKIE_SECURE")
    cookie_samesite: Literal["lax", "strict"] = Field(default="lax", alias="AUTH_COOKIE_SAMESITE")
    idle_seconds: int = Field(default=1800, ge=60, le=86400, alias="AUTH_IDLE_SECONDS")
    absolute_seconds: int = Field(default=28800, ge=60, le=604800, alias="AUTH_ABSOLUTE_SECONDS")
    max_records: int = Field(default=10000, ge=10, le=1000000, alias="AUTH_MAX_RECORDS")
    encryption_key: SecretStr | None = Field(default=None, alias="AUTH_STATE_ENCRYPTION_KEY")
    tenant_id: str | None = Field(default=None, alias="AUTH_ENTRA_TENANT_ID")
    client_id: str | None = Field(default=None, alias="AUTH_ENTRA_CLIENT_ID")
    client_secret: SecretStr | None = Field(default=None, alias="AUTH_ENTRA_CLIENT_SECRET")
    database_url: SecretStr | None = Field(default=None, alias="AUTH_DATABASE_URL")
    proxy_secret: SecretStr = Field(alias="AUTH_PROXY_SECRET")
    pg_schema: str = Field(default="rag", alias="AUTH_PG_SCHEMA", pattern=r"^[A-Za-z_][A-Za-z0-9_]*$")
    return_paths: list[str] = Field(default_factory=lambda: ["/"], alias="AUTH_RETURN_PATHS")

    @model_validator(mode="after")
    def policy(self) -> Self:
        if not re.fullmatch(r"[A-Za-z0-9_-]{32,256}", self.proxy_secret.get_secret_value()):
            raise ValueError("AUTH_PROXY_SECRET must be 32-256 URL-safe random characters")
        origin = urlsplit(self.public_origin)
        if (origin.scheme not in {"http", "https"} or not origin.hostname or origin.username
                or origin.password or origin.path or origin.query or origin.fragment):
            raise ValueError("AUTH_PUBLIC_ORIGIN must be an exact HTTP(S) origin without a path")
        # Accessing port also rejects malformed ports during validation.
        _ = origin.port
        loopback = origin.hostname in {"localhost", "127.0.0.1", "::1"}
        if origin.scheme == "http" and (self.app_env != "local" or not loopback):
            raise ValueError("HTTP authentication is restricted to local loopback origins")
        if self.provider == "dev" and (self.app_env != "local" or not loopback):
            raise ValueError("Development identities are restricted to local loopback origins")
        if not re.fullmatch(r"[A-Za-z0-9_-]{1,80}", self.cookie_name):
            raise ValueError("Invalid authentication cookie name")
        if self.cookie_name.startswith("__Host-") and not self.cookie_secure:
            raise ValueError("__Host- cookies require Secure")
        if self.cookie_secure and origin.scheme != "https":
            raise ValueError("Secure cookies require a configured HTTPS origin")
        if origin.scheme == "https" and not self.cookie_secure:
            raise ValueError("HTTPS authentication requires Secure cookies")
        if self.app_env != "local":
            if self.store != "postgres" or not self.cookie_name.startswith("__Host-"):
                raise ValueError("Nonlocal sessions require PostgreSQL and __Host- cookies")
        if self.idle_seconds > self.absolute_seconds:
            raise ValueError("Idle lifetime must not exceed absolute lifetime")
        if self.store == "postgres" and (not self.database_url or not self.encryption_key):
            raise ValueError("PostgreSQL sessions require AUTH_DATABASE_URL and a stable encryption key")
        if self.database_url:
            database = urlsplit(self.database_url.get_secret_value())
            if database.scheme not in {"postgres", "postgresql"} or not database.hostname:
                raise ValueError("Invalid gateway PostgreSQL URL")
            if self.app_env != "local" and parse_qs(database.query).get("sslmode") not in (
                ["require"], ["verify-ca"], ["verify-full"],
            ):
                raise ValueError("Workplace gateway PostgreSQL connections require explicit TLS")
        if self.encryption_key:
            Fernet(self.encryption_key.get_secret_value().encode("ascii"))
        if self.provider == "entra":
            if not self.tenant_id or not self.client_id or not self.client_secret:
                raise ValueError("Entra requires tenant ID, client ID and client secret")
            self.tenant_id = str(UUID(self.tenant_id))
            self.client_id = str(UUID(self.client_id))
            if self.cookie_samesite != "lax":
                raise ValueError("Entra GET callback requires SameSite=Lax")
        for path in self.return_paths:
            if not re.fullmatch(r"/(?:[A-Za-z0-9_/-]*)", path) or path.startswith("//"):
                raise ValueError("Return destinations must be simple relative paths")
        if "/" not in self.return_paths:
            raise ValueError("Return destinations must include /")
        return self

    @property
    def issuer(self) -> str:
        return f"https://login.microsoftonline.com/{self.tenant_id}/v2.0"

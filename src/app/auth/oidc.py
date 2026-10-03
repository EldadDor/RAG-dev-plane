"""Entra adapter using Authlib's OIDC and PKCE implementation."""

from typing import Protocol
from urllib.parse import urlsplit
from uuid import UUID

from authlib.integrations.starlette_client import OAuth

from app.auth.config import GatewaySettings


class LoginProvider(Protocol):
    async def begin(self) -> dict: ...
    async def finish(self, transaction: dict, code: str) -> dict: ...


class EntraProvider:
    def __init__(self, settings: GatewaySettings):
        self.settings = settings
        self.client = OAuth().register(
            "entra", client_id=settings.client_id,
            client_secret=settings.client_secret.get_secret_value(),
            server_metadata_url=f"{settings.issuer}/.well-known/openid-configuration",
            client_kwargs={"scope": "openid profile email", "code_challenge_method": "S256", "timeout": 15},
        )

    async def _metadata(self) -> None:
        metadata = await self.client.load_server_metadata()
        if metadata.get("issuer") != self.settings.issuer:
            raise ValueError("Invalid provider issuer")
        for key in ("authorization_endpoint", "token_endpoint", "jwks_uri"):
            parsed = urlsplit(metadata.get(key, ""))
            if parsed.scheme != "https" or parsed.hostname != "login.microsoftonline.com" or parsed.username:
                raise ValueError("Invalid provider endpoint")
        # Pin Entra's expected asymmetric ID-token algorithm, never accept none/HMAC.
        metadata["id_token_signing_alg_values_supported"] = ["RS256"]

    async def begin(self) -> dict:
        await self._metadata()
        return await self.client.create_authorization_url(
            f"{self.settings.public_origin}/auth/callback", prompt="select_account",
        )

    async def finish(self, transaction: dict, code: str) -> dict:
        await self._metadata()
        token = await self.client.fetch_access_token(
            redirect_uri=f"{self.settings.public_origin}/auth/callback", code=code,
            code_verifier=transaction["code_verifier"], grant_type="authorization_code",
        )
        claims = await self.client.parse_id_token(
            token, nonce=transaction["nonce"], leeway=0,
            claims_options={
                "iss": {"essential": True, "value": self.settings.issuer},
                "aud": {"essential": True, "value": self.settings.client_id},
                "exp": {"essential": True}, "sub": {"essential": True},
            },
        )
        # Also require nonce equality: providers cannot disable our nonce policy.
        if claims.get("nonce") != transaction["nonce"] or claims.get("tid") != self.settings.tenant_id:
            raise ValueError("Invalid identity claims")
        oid = str(UUID(claims["oid"]))
        name = claims.get("name") or "Microsoft user"
        email = claims.get("email")
        if not isinstance(name, str) or len(name) > 300:
            raise ValueError("Invalid display name")
        if email is not None and (not isinstance(email, str) or len(email) > 320):
            raise ValueError("Invalid display email")
        return {
            "subject": f"entra:{self.settings.tenant_id}:{oid}",
            "display_name": name,
            "email": email,
        }

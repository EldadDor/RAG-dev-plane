"""Entra ID / Managed Identity auth helpers for Azure services.

Uses a single shared DefaultAzureCredential instance which handles token
caching and refresh internally. Works with:
  - az login  (local dev)
  - Managed Identity (Azure Container Apps / App Service)
"""

from __future__ import annotations

from azure.identity import DefaultAzureCredential

# Singleton credential — DefaultAzureCredential manages its own token cache.
_credential: DefaultAzureCredential | None = None

AZURE_OPENAI_SCOPE = "https://cognitiveservices.azure.com/.default"
AZURE_POSTGRES_SCOPE = "https://ossrdbms-aad.database.windows.net/.default"


def get_azure_credential() -> DefaultAzureCredential:
    global _credential
    if _credential is None:
        _credential = DefaultAzureCredential()
    return _credential


def get_azure_openai_token() -> str:
    return get_azure_credential().get_token(AZURE_OPENAI_SCOPE).token


def get_azure_postgres_token() -> str:
    """Return an Entra token to use as the Postgres password.

    Note: tokens expire in ~60 minutes. asyncpg pools are configured with
    max_inactive_connection_lifetime=3000s (50 min) so connections are
    recycled before expiry. For very-high-availability deployments, consider
    a periodic pool refresh task that calls this function and recreates the pool.
    """
    return get_azure_credential().get_token(AZURE_POSTGRES_SCOPE).token

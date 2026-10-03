"""Read-only trusted profile and strictly bounded user preferences."""

import asyncpg
from fastapi import APIRouter, Depends, HTTPException, Request

from app.api.schemas import (
    AccountCapabilities, AccountLogoutCapability, GatewayLogoutCapability, AccountPreferenceCapabilities,
    AccountPreferences, AccountPreferencesResponse, AccountProfile,
    AccountProfileResponse, ApiErrorResponse, WorkspaceSummary,
)
from app.config import Settings, get_settings
from app.dependencies import get_account_preference_store, get_workspace_store
from app.identity import Principal, get_principal
from app.services.account_preferences import AccountPreferenceStore, AccountUnavailableError
from app.services.workspace_store import WorkspaceStore


def require_account_request(request: Request) -> None:
    if request.query_params:
        raise HTTPException(status_code=422)
    if request.method == "PATCH":
        media_type = request.headers.get("content-type", "").split(";", 1)[0].strip().lower()
        if media_type != "application/json":
            raise HTTPException(status_code=415)


router = APIRouter(
    prefix="/account", tags=["account"], dependencies=[Depends(require_account_request)],
    responses={code: {"model": ApiErrorResponse} for code in (401, 415, 422, 500, 503)},
)


@router.get("/profile", response_model=AccountProfileResponse)
async def get_profile(
    principal: Principal = Depends(get_principal),
    settings: Settings = Depends(get_settings),
    workspace_store: WorkspaceStore = Depends(get_workspace_store),
    preference_store: AccountPreferenceStore = Depends(get_account_preference_store),
) -> AccountProfileResponse:
    try:
        memberships = await workspace_store.list_for_subject(principal.subject)
    except (asyncpg.PostgresError, asyncpg.InterfaceError, OSError) as exc:
        raise AccountUnavailableError("profile") from exc
    available = preference_store.persistence != "unavailable"
    return AccountProfileResponse(
        profile=AccountProfile(display_name=principal.display_name, email=principal.email),
        workspaces=[WorkspaceSummary(**vars(item)) for item in memberships],
        capabilities=AccountCapabilities(
            preferences=AccountPreferenceCapabilities(
                read=available, update=available, persistence=preference_store.persistence,
                editable_fields=["recent_chat_limit"] if available else [],
            ),
            logout=GatewayLogoutCapability() if (
                settings.auth_mode == "gateway" and getattr(settings, "auth_session_gateway_enabled", False)
            ) else AccountLogoutCapability(
                reason="fixed_local_identity" if settings.auth_mode == "local" else "not_configured",
            ),
        ),
    )


@router.get("/preferences", response_model=AccountPreferencesResponse)
async def get_preferences(
    principal: Principal = Depends(get_principal),
    store: AccountPreferenceStore = Depends(get_account_preference_store),
) -> AccountPreferencesResponse:
    limit = await store.read(principal.subject)
    return AccountPreferencesResponse(
        preferences=AccountPreferences(recent_chat_limit=limit), persistence=store.persistence,
    )


@router.patch("/preferences", response_model=AccountPreferencesResponse)
async def update_preferences(
    body: AccountPreferences,
    principal: Principal = Depends(get_principal),
    store: AccountPreferenceStore = Depends(get_account_preference_store),
) -> AccountPreferencesResponse:
    limit = await store.update(principal.subject, body.recent_chat_limit)
    return AccountPreferencesResponse(
        preferences=AccountPreferences(recent_chat_limit=limit), persistence=store.persistence,
    )

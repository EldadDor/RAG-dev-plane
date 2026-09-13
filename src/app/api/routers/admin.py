"""Local operator endpoints. These are intentionally unavailable in gateway deployments."""

from fastapi import APIRouter, Depends, HTTPException

from app.api.schemas import WarmModelProfileRequest, WarmModelProfileResponse
from app.config import Settings, get_settings
from app.dependencies import get_model_profile_warmer, get_workspace_store
from app.identity import Principal, get_principal
from app.services.model_profile_warmer import ModelProfileWarmer
from app.services.model_profiles import ModelProfileUnavailable
from app.services.workspace_store import WorkspaceStore, require_workspace_access

router = APIRouter(prefix="/admin/model-profiles", tags=["admin"])


@router.post("/{profile_name}/warm", response_model=WarmModelProfileResponse)
async def warm_model_profile(
    profile_name: str,
    body: WarmModelProfileRequest,
    settings: Settings = Depends(get_settings),
    principal: Principal = Depends(get_principal),
    workspace_store: WorkspaceStore = Depends(get_workspace_store),
    warmer: ModelProfileWarmer = Depends(get_model_profile_warmer),
) -> WarmModelProfileResponse:
    if settings.app_env != "local":
        raise HTTPException(status_code=403, detail="Local operator endpoint only")
    workspace_id = body.workspace_id or settings.default_workspace_id
    await require_workspace_access(workspace_id, principal, workspace_store)
    try:
        result = await warmer.warm(
            profile_name, body.source_model_profile, workspace_id, dry_run=body.dry_run
        )
    except (ModelProfileUnavailable, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return WarmModelProfileResponse(**result.__dict__)

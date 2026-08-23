from fastapi import APIRouter, Depends

from app.api.schemas import PrincipalSummary, WorkspaceListResponse, WorkspaceSummary
from app.dependencies import get_workspace_store
from app.identity import Principal, get_principal
from app.services.workspace_store import WorkspaceStore

router = APIRouter(tags=["workspaces"])


@router.get("/workspaces", response_model=WorkspaceListResponse)
async def list_workspaces(
    principal: Principal = Depends(get_principal),
    workspace_store: WorkspaceStore = Depends(get_workspace_store),
) -> WorkspaceListResponse:
    memberships = await workspace_store.list_for_subject(principal.subject)
    return WorkspaceListResponse(
        principal=PrincipalSummary(display_name=principal.display_name),
        workspaces=[WorkspaceSummary(**vars(item)) for item in memberships],
    )

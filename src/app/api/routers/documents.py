"""Authorized, provider-free discovery of published document metadata."""
from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, Response

from app.api.schemas import ApiErrorResponse, DocumentListResponse
from app.dependencies import get_document_catalog_service, get_workspace_store
from app.identity import Principal, get_principal
from app.services.document_catalog import DOCUMENT_HEADERS, DocumentCatalogService
from app.services.workspace_store import WorkspaceStore, require_workspace_access

router = APIRouter(prefix="/workspaces/{workspace_id}/documents", tags=["documents"])
ProfileQuery = Annotated[str | None, Query(min_length=1, max_length=100, pattern=r"^[A-Za-z0-9][A-Za-z0-9_-]*$")]


@router.get("", response_model=DocumentListResponse, responses={
    code: {"model": ApiErrorResponse} for code in (401, 403, 409, 422, 500, 503)
})
async def list_documents(
    response: Response,
    workspace_id: Annotated[str, Path(min_length=1)],
    limit: Annotated[int, Query(ge=1, le=100)] = 25,
    cursor: Annotated[str | None, Query(min_length=1, max_length=4096)] = None,
    model_profile: ProfileQuery = None,
    chunking_profile: ProfileQuery = None,
    principal: Principal = Depends(get_principal),
    workspace_store: WorkspaceStore = Depends(get_workspace_store),
    service: DocumentCatalogService = Depends(get_document_catalog_service),
) -> DocumentListResponse:
    await require_workspace_access(workspace_id, principal, workspace_store)
    response.headers.update(DOCUMENT_HEADERS)
    return await service.list(workspace_id, principal.subject, limit, cursor, model_profile, chunking_profile)

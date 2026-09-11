from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, Response

from app.clients.vector_store import VectorStore
from app.dependencies import get_asset_store, get_vector_store, get_workspace_store
from app.identity import Principal, get_principal
from app.services.asset_store import AssetNotFoundError, AssetStore
from app.services.workspace_store import WorkspaceStore, require_workspace_access


router = APIRouter(prefix="/workspaces/{workspace_id}/assets", tags=["assets"])
_BROWSER_IMAGE_TYPES = {"image/png", "image/jpeg", "image/gif", "image/webp"}


def _matches_image_signature(media_type: str, content: bytes) -> bool:
    if media_type == "image/png":
        return content.startswith(b"\x89PNG\r\n\x1a\n")
    if media_type == "image/jpeg":
        return content.startswith(b"\xff\xd8\xff")
    if media_type == "image/gif":
        return content.startswith((b"GIF87a", b"GIF89a"))
    if media_type == "image/webp":
        return len(content) >= 12 and content[:4] == b"RIFF" and content[8:12] == b"WEBP"
    return False


@router.get("/{asset_id}")
async def get_asset(
    workspace_id: str,
    asset_id: str,
    request: Request,
    principal: Principal = Depends(get_principal),
    workspace_store: WorkspaceStore = Depends(get_workspace_store),
    vector_store: VectorStore = Depends(get_vector_store),
    asset_store: AssetStore = Depends(get_asset_store),
) -> Response:
    await require_workspace_access(workspace_id, principal, workspace_store)
    metadata = await vector_store.get_asset_metadata(workspace_id, asset_id)
    if metadata is None:
        raise HTTPException(status_code=404, detail="Asset not found")
    media_type = metadata["media_type"]
    if media_type not in _BROWSER_IMAGE_TYPES:
        raise HTTPException(status_code=415, detail="Asset type cannot be displayed")

    etag = f'"{metadata["content_hash"]}"'
    if request.headers.get("if-none-match") == etag:
        return Response(status_code=304, headers={"ETag": etag})
    try:
        content = await asset_store.read(metadata["storage_key"])
    except AssetNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Asset not found") from exc
    if not _matches_image_signature(media_type, content):
        raise HTTPException(status_code=415, detail="Asset content does not match its image type")
    return Response(
        content=content,
        media_type=media_type,
        headers={
            "Cache-Control": "private, max-age=3600",
            "Content-Disposition": "inline",
            "ETag": etag,
            "X-Content-Type-Options": "nosniff",
        },
    )

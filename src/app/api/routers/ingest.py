import logging
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException

from app.api.schemas import IngestRequest, IngestResponse, IngestResult
from app.dependencies import get_ingestion_service
from app.services.ingestion_service import IngestionService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ingest", tags=["ingestion"])


@router.post("", response_model=IngestResponse)
async def ingest(
        request: IngestRequest,
        ingestion_service: IngestionService = Depends(get_ingestion_service),
) -> IngestResponse:
    logger.info("📥 Ingest request received: source_path=%s recursive=%s", request.source_path, request.recursive)

    path = Path(request.source_path)
    if not path.exists():
        logger.error("❌ Path not found: %s", request.source_path)
        raise HTTPException(status_code=404, detail=f"Path not found: {request.source_path}")

    try:
        if path.is_dir():
            logger.info("📂 Processing directory: %s (recursive=%s)", request.source_path, request.recursive)
            result = await ingestion_service.ingest_directory(
                directory=request.source_path,
                recursive=request.recursive,
            )
        else:
            logger.info("📄 Processing file: %s", request.source_path)
            result = await ingestion_service.ingest_file(request.source_path)
            result = IngestResponse(
                indexed=result.chunks_indexed,
                documents=[result],
            )

        logger.info("✅ Ingestion complete: %d chunks indexed across %d documents", result.indexed, len(result.documents))
        return result
    except Exception as exc:
        logger.error("❌ Ingestion failed for %s: %s", request.source_path, exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Ingestion failed") from exc
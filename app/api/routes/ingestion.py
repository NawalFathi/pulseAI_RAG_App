
import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.models.database import get_db
from app.api.dependencies import get_ingestion_service
from app.schemas.ingestion import (
    IngestRequest,
    IngestResponse,
)
from app.schemas.response import ErrorResponse
from app.services.ingestion_service import (
    IngestionError,
    IngestionService,
)
from app.services.scraper_service import ScraperError


logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1",
    tags=["Ingestion"],
)


@router.post(
    "/ingest",
    response_model=IngestResponse,
    responses={
        422: {"model": ErrorResponse},
        502: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
    summary="Ingest a public website",
    description="Scrapes, chunks, embeds, and stores website content.",
)
async def ingest_website(
    request: IngestRequest,
    db: Session = Depends(get_db),
    service: IngestionService = Depends(get_ingestion_service),
):
    """Scrape, embed, and persist a website."""

    try:
        website, already_exists = await service.ingest(
            db=db,
            url=str(request.url),
        )

        message = (
            "Website already ingested"
            if already_exists
            else "Website ingested successfully"
        )

        return {
            "success": True,
            "data": {
                "ingest_id": website.ingest_id,
                "url": website.url,
                "message": message,
            },
        }

    except ScraperError as exc:
        logger.warning("Website scraping rejected or failed: %s", exc)

        raise HTTPException(
            status_code=502,
            detail={
                "success": False,
                "data": None,
                "error": {
                    "code": "SCRAPE_FAILED",
                    "message": str(exc),
                },
            },
        ) from exc

    except IngestionError as exc:
        logger.exception("Ingestion failed")

        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "data": None,
                "error": {
                    "code": "INGESTION_FAILED",
                    "message": str(exc),
                },
            },
        ) from exc

    except Exception as exc:
        logger.exception("Unexpected ingestion error")

        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "data": None,
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "An unexpected error occurred.",
                },
            },
        ) from exc

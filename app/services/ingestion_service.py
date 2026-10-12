
import logging
from urllib.parse import urlsplit

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.website import Website
from app.repositories.website_repository import WebsiteRepository
from app.repositories.chunk_repository import ChunkRepository
from app.services.scraper_service import (
    ScraperError,
    ScraperService,
)
from app.services.chunking_service import ChunkingService
from app.services.embedding_service import EmbeddingService
from app.services.url_normalizer import URLNormalizer


logger = logging.getLogger(__name__)


class IngestionError(Exception):
    """Raised when website ingestion fails."""


class IngestionService:
    """Coordinate website scraping, embedding, and persistence."""

    def __init__(
        self,
        website_repository: WebsiteRepository,
        chunk_repository: ChunkRepository,
        scraper: ScraperService,
        chunker: ChunkingService,
        embedder: EmbeddingService,
    ) -> None:
        """Set the repository and service collaborators used for ingestion."""

        self.website_repository = website_repository
        self.chunk_repository = chunk_repository
        self.scraper = scraper
        self.chunker = chunker
        self.embedder = embedder

    async def ingest(
        self,
        db: Session,
        url: str,
    ) -> tuple[Website, bool]:
        """
        Ingest a URL once.

        Returns:
            A tuple containing the website record and whether it
            was already ingested.
        """

        normalized_url = URLNormalizer.normalize(url)

        existing = self.website_repository.get_by_normalized_url(
            db,
            normalized_url,
        )

        if existing:
            logger.info(
                "Duplicate URL; reusing ingest_id=%s",
                existing.ingest_id,
            )
            return existing, True

        logger.info(
            "Ingestion started | host=%s",
            urlsplit(url).hostname,
        )

        try:
            text = await self.scraper.scrape(url)

            chunks = self.chunker.create_chunks(text)

            if not chunks:
                raise IngestionError(
                    "No readable content was found on the website."
                )

            embeddings = await self.embedder.create_embeddings(
                [chunk.content for chunk in chunks]
            )

            # Save the website and its chunks atomically.
            website = self.website_repository.create(
                db=db,
                url=url,
                normalized_url=normalized_url,
            )

            self.chunk_repository.save_chunks(
                db=db,
                ingest_id=website.ingest_id,
                contents=[chunk.content for chunk in chunks],
                embeddings=embeddings,
            )

            db.commit()
            db.refresh(website)

            logger.info(
                "Ingestion completed | ingest_id=%s | chunks=%d",
                website.ingest_id,
                len(chunks),
            )

            return website, False

        except IntegrityError:
            db.rollback()

            # A concurrent request may have inserted the same URL.
            existing = self.website_repository.get_by_normalized_url(
                db,
                normalized_url,
            )

            if existing:
                logger.info(
                    "Concurrent duplicate detected | ingest_id=%s",
                    existing.ingest_id,
                )
                return existing, True

            logger.exception("Database integrity error during ingestion")
            raise IngestionError(
                "Unable to save the ingested website."
            )

        except Exception:
            db.rollback()
            logger.exception("Website ingestion failed")
            raise

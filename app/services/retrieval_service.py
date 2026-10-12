
import logging

from sqlalchemy.orm import Session

from app.core.config import settings
from app.repositories.website_repository import WebsiteRepository
from app.repositories.chunk_repository import ChunkRepository
from app.schemas.retrieval import RetrievedChunk
from app.services.embedding_service import EmbeddingService


logger = logging.getLogger(__name__)


class WebsiteNotFoundError(Exception):
    """Raised when the requested ingest_id does not exist."""


class RetrievalService:
    """Retrieve relevant content for a website question."""

    def __init__(
        self,
        website_repository: WebsiteRepository,
        chunk_repository: ChunkRepository,
        embedding_service: EmbeddingService,
        top_k: int | None = None,
        similarity_threshold: float | None = None,
    ) -> None:
        """Configure repository clients and retrieval relevance limits."""

        self.website_repository = website_repository
        self.chunk_repository = chunk_repository
        self.embedding_service = embedding_service

        self.top_k = (
            settings.top_k if top_k is None else top_k
        )

        self.similarity_threshold = (
            settings.similarity_threshold
            if similarity_threshold is None
            else similarity_threshold
        )

    async def retrieve(
        self,
        db: Session,
        ingest_id: str,
        question: str,
    ) -> list[RetrievedChunk]:
        """Return the most relevant chunks for a known website.

        Chunks below the configured similarity threshold are excluded.
        Raise ``WebsiteNotFoundError`` when ``ingest_id`` is unknown.
        """

        website = self.website_repository.get_by_ingest_id(
            db,
            ingest_id,
        )

        if website is None:
            raise WebsiteNotFoundError(
                "No website found for the provided ingest_id."
            )

        logger.info(
            "Retrieval started | ingest_id=%s",
            ingest_id,
        )

        query_embedding = (
            await self.embedding_service.create_embedding(
                question
            )
        )

        results = self.chunk_repository.search_similar(
            db=db,
            ingest_id=ingest_id,
            query_embedding=query_embedding,
            top_k=self.top_k,
        )

        retrieved = [
            RetrievedChunk(
                chunk_id=chunk.id,
                chunk_index=chunk.chunk_index,
                content=chunk.content,
                similarity=similarity,
            )
            for chunk, similarity in results
            if similarity >= self.similarity_threshold
        ]

        logger.info(
            "Retrieval completed | ingest_id=%s | candidates=%d "
            "| accepted=%d | threshold=%.3f | scores=%s",
            ingest_id,
            len(results),
            len(retrieved),
            self.similarity_threshold,
            [round(similarity, 3) for _, similarity in results],
        )

        return retrieved

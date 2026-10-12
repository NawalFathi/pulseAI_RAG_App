
import logging
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.chunk import DocumentChunk


logger = logging.getLogger(__name__)


class ChunkRepository:
    """Persist and retrieve website chunks."""

    def save_chunks(
        self,
        db: Session,
        ingest_id: str,
        contents: list[str],
        embeddings: list[list[float]],
    ) -> list[DocumentChunk]:
        """Save chunks and embeddings in one transaction."""

        if len(contents) != len(embeddings):
            raise ValueError(
                "Chunk and embedding counts must match."
            )

        if not contents:
            return []

        for embedding in embeddings:
            if len(embedding) != settings.embedding_dimension:
                raise ValueError(
                    "Embedding dimension does not match configuration."
                )

        records = [
            DocumentChunk(
                ingest_id=ingest_id,
                content=content,
                chunk_index=index,
                embedding=embedding,
            )
            for index, (content, embedding) in enumerate(
                zip(contents, embeddings)
            )
        ]

        try:
            db.add_all(records)
            db.flush()

            logger.info(
                "Chunks persisted | ingest_id=%s | count=%d",
                ingest_id,
                len(records),
            )

            return records

        except Exception:
            db.rollback()
            logger.exception(
                "Failed to save chunks | ingest_id=%s",
                ingest_id,
            )
            raise

    def search_similar(
        self,
        db: Session,
        ingest_id: str,
        query_embedding: list[float],
        top_k: int = 5,
    ) -> list[tuple[DocumentChunk, float]]:
        """
        Retrieve chunks ordered by cosine similarity.

        Only chunks belonging to the requested website are searched.

        Returns:
            A list of (chunk, similarity) pairs, ordered from
            highest to lowest similarity.
        """

        if not 1 <= top_k <= 20:
            raise ValueError("top_k must be between 1 and 20")

        if len(query_embedding) != settings.embedding_dimension:
            raise ValueError(
                "Query embedding dimension does not match configuration."
            )

        distance = DocumentChunk.embedding.cosine_distance(
            query_embedding
        )

        statement = (
            select(
                DocumentChunk,
                (1.0 - distance).label("similarity"),
            )
            .where(
                DocumentChunk.ingest_id == ingest_id,
                DocumentChunk.embedding.is_not(None),
            )
            .order_by(distance.asc())
            .limit(top_k)
        )

        rows = db.execute(statement).all()

        return [
            (chunk, float(similarity))
            for chunk, similarity in rows
        ]

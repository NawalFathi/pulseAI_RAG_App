
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.website import Website


class WebsiteRepository:
    """Database operations for ingested websites."""

    def get_by_normalized_url(
        self,
        db: Session,
        normalized_url: str,
    ) -> Website | None:
        """Return an existing website, if present."""

        statement = select(Website).where(
            Website.normalized_url == normalized_url
        )

        return db.scalar(statement)

    def get_by_ingest_id(
        self,
        db: Session,
        ingest_id: str,
    ) -> Website | None:
        """Find a website by its public ingestion ID."""

        statement = select(Website).where(
            Website.ingest_id == ingest_id
        )

        return db.scalar(statement)

    def create(
        self,
        db: Session,
        url: str,
        normalized_url: str,
    ) -> Website:
        """Add a website record to the current transaction."""

        website = Website(
            ingest_id=str(uuid.uuid4()),
            url=url,
            normalized_url=normalized_url,
            status="completed",
        )

        db.add(website)
        db.flush()

        return website

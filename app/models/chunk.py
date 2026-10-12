from datetime import datetime
from pgvector.sqlalchemy import Vector
from sqlalchemy import DateTime, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.config import settings
from app.models.database import Base


class DocumentChunk(Base):
    """
    Stores a chunk of scraped website content
    together with its vector embedding.
    """

    __tablename__ = "content_chunks"

    id: Mapped [int]= mapped_column(
        primary_key=True,
    )

    ingest_id: Mapped[str] = mapped_column(
        ForeignKey("websites.ingest_id"),
        nullable=False,
        index=True
    )

    chunk_index: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    embedding: Mapped[list[float] | None] = mapped_column(
        Vector(settings.embedding_dimension),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
       
    )

    
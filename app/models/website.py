import uuid
from datetime import datetime
from sqlalchemy import DateTime,String
from sqlalchemy.orm import Mapped, mapped_column
from app.models.database import Base

class Website(Base):
    """represents an injested website"""
    __tablename__ = "websites"

    id:Mapped[int]=mapped_column(
        primary_key=True,
    )

    ingest_id:Mapped[str] = mapped_column(
        String(36),
        unique=True,
        nullable=False,
        default= lambda: str(uuid.uuid4()),
    )

    url:Mapped[str] = mapped_column(
        String(2048),
        nullable=False,
    )

    normalized_url:Mapped[str] = mapped_column(
        String(2048),
        unique=True,
        nullable=False,
    )

    status:Mapped[str] = mapped_column(
        String(50),
        default="completed",
        nullable=False,
    )

    created_at:Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    updated_at:Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

   
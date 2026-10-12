
from pydantic import BaseModel, Field
from uuid import UUID

class QuestionRequest(BaseModel):
    """Request to query an ingested website."""

    ingest_id: UUID

    question: str = Field(
        min_length=1,
        max_length=2000,
    )

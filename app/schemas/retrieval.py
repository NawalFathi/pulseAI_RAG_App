
from pydantic import BaseModel, Field


class RetrievedChunk(BaseModel):
    """Represent a relevant chunk retrieved from a website."""

    chunk_id: int
    chunk_index: int
    content: str
    similarity: float = Field(ge=-1.0, le=1.0)

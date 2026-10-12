
from pydantic import BaseModel, ConfigDict, HttpUrl


class IngestRequest(BaseModel):
    """Request to ingest a public website."""

    url: HttpUrl


class IngestData(BaseModel):
    """Successful ingestion response data."""

    ingest_id: str
    url: str
    message: str


class IngestResponse(BaseModel):
    """Standard success response."""

    success: bool
    data: IngestData


from typing import Any

from pydantic import BaseModel


class ErrorDetail(BaseModel):
    """Consistent API error details."""

    code: str
    message: str


class ErrorResponse(BaseModel):
    """Consistent API error response."""

    success: bool = False
    data: None = None
    error: ErrorDetail

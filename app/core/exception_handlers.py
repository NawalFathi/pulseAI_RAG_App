
import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)


def register_exception_handlers(app: FastAPI) -> None:
    """Register handlers for consistent API error responses."""

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_exception(
        request: Request,
        exc: StarletteHTTPException,
    ):
        """Log an HTTP error and return it in the standard API envelope."""

        logger.warning(
            "HTTP error | method=%s | path=%s | status=%d",
            request.method,
            request.url.path,
            exc.status_code,
        )
        detail = exc.detail

        if isinstance(detail, dict) and "error" in detail:
            payload = {
                "success": False,
                "data": None,
                "error": detail["error"],
            }
        else:
            payload = {
                "success": False,
                "data": None,
                "error": {
                    "code": "HTTP_ERROR",
                    "message": (
                        detail
                        if isinstance(detail, str)
                        else "The request could not be completed."
                    ),
                },
            }

        return JSONResponse(
            status_code=exc.status_code,
            content=payload,
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(
        request: Request,
        exc: RequestValidationError,
    ):
        """Log request validation details without exposing them to clients."""

        logger.warning(
            "Request validation failed | method=%s | path=%s | errors=%d",
            request.method,
            request.url.path,
            len(exc.errors()),
        )
        return JSONResponse(
            status_code=422,
            content={
                "success": False,
                "data": None,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "The request contains invalid input.",
                },
            },
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_error(
        request: Request,
        exc: Exception,
    ):
        """Log an unhandled exception and return a generic server error."""

        logger.exception(
            "Unhandled error while handling %s %s: %s",
            request.method,
            request.url.path,
            exc,
        )
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "data": None,
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "An unexpected error occurred.",
                },
            },
        )


import logging

from app.core.config import settings

def configure_logging() -> None:
    """Configure application-wide logging using the configured log level."""

    logging.basicConfig(
        level=getattr(logging, settings.log_level),
        format=(
            "%(asctime)s | %(levelname)s | "
            "%(name)s | %(message)s"
        ),
    )

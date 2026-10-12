from typing import Literal, Self

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application credentials and configuration loaded from `.env`."""

    database_url: str
    openai_api_key: str
    openai_embedding_model: str
    openai_chat_model: str
    embedding_dimension: int = Field(gt=0)

    chunk_size: int = Field(gt=0)
    chunk_overlap: int = Field(ge=0)

    top_k: int = Field(ge=1, le=20)
    similarity_threshold: float = Field(ge=-1.0, le=1.0)
    scrape_timeout: int = Field(gt=0)
    log_level: Literal[
        "DEBUG",
        "INFO",
        "WARNING",
        "ERROR",
        "CRITICAL",
    ]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @model_validator(mode="after")
    def validate_chunk_overlap(self) -> Self:
        """Ensure the configured overlap is smaller than each chunk."""
        if self.chunk_overlap >= self.chunk_size:
            raise ValueError("CHUNK_OVERLAP must be smaller than CHUNK_SIZE")
        return self


settings = Settings()
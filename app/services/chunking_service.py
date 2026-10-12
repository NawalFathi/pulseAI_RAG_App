
import re
import logging

from dataclasses import dataclass


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class TextChunk:
    """Represent a chunk of cleaned website content."""

    chunk_index: int
    content: str


class TextCleaningService:
    """Clean and normalize extracted webpage text."""

    @staticmethod
    def clean(text: str) -> str:
        """
        Normalize whitespace and remove empty lines.

        The scraper already removes unwanted HTML elements.
        This method cleans the resulting plain text.
        """

        if not text or not text.strip():
            return ""

        text = text.replace("\x00", " ")

        # Normalize whitespace within each line.
        lines = [
            re.sub(r"\s+", " ", line).strip()
            for line in text.splitlines()
        ]

        # Remove empty lines and consecutive duplicate lines.
        cleaned_lines = []

        for line in lines:
            if not line:
                continue

            if cleaned_lines and cleaned_lines[-1] == line:
                continue

            cleaned_lines.append(line)

        return "\n".join(cleaned_lines)


class ChunkingService:
    """Split cleaned website text into overlapping chunks."""

    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
    ) -> None:
        """Initialize chunk limits and reject invalid size configurations."""

        if chunk_size <= 0:
            raise ValueError("chunk_size must be positive")

        if chunk_overlap < 0:
            raise ValueError("chunk_overlap cannot be negative")

        if chunk_overlap >= chunk_size:
            raise ValueError(
                "chunk_overlap must be smaller than chunk_size"
            )

        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def create_chunks(self, text: str) -> list[TextChunk]:
        """
        Split text into chunks with overlapping characters.

        Chunk indices start at zero.
        """

        cleaned_text = TextCleaningService.clean(text)

        if not cleaned_text:
            return []

        chunks: list[TextChunk] = []

        start = 0
        text_length = len(cleaned_text)
        step = self.chunk_size - self.chunk_overlap

        while start < text_length:
            end = min(start + self.chunk_size, text_length)

            content = cleaned_text[start:end].strip()

            if content:
                chunks.append(
                    TextChunk(
                        chunk_index=len(chunks),
                        content=content,
                    )
                )

            start += step

        logger.info(
            "Chunking completed | characters=%d | chunks=%d",
            text_length,
            len(chunks),
        )

        return chunks

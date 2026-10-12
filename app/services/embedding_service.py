
import logging

from openai import AsyncOpenAI

from app.core.config import settings


logger = logging.getLogger(__name__)


class EmbeddingService:
    """Generate vector embeddings for website text."""

    def __init__(self) -> None:
        self.client = AsyncOpenAI(
            api_key=settings.openai_api_key,
        )
        self.model = settings.openai_embedding_model

    async def create_embedding(
        self,
        text: str,
    ) -> list[float]:
        """Return the vector embedding for a single non-empty text."""

        embeddings = await self.create_embeddings([text])
        return embeddings[0]

    async def create_embeddings(
        self,
        texts: list[str],
    ) -> list[list[float]]:
        """Generate dimension-checked embeddings in input order.

        Empty input returns an empty list; blank text or an unexpected API
        response raises an error rather than returning partial results.
        """

        if not texts:
            return []

        if any(not text.strip() for text in texts):
            raise ValueError(
                "Embedding input cannot contain empty text."
            )

        logger.info(
            "Embedding request started | model=%s | count=%d",
            self.model,
            len(texts),
        )
        response = await self.client.embeddings.create(
            model=self.model,
            input=texts,
        )

        # API response items include their original input indices.
        ordered_items = sorted(
            response.data,
            key=lambda item: item.index,
        )

        embeddings = [
            item.embedding
            for item in ordered_items
        ]

        if len(embeddings) != len(texts):
            raise RuntimeError(
                "Embedding count does not match input count."
            )

        if any(
            len(embedding) != settings.embedding_dimension
            for embedding in embeddings
        ):
            raise RuntimeError(
                "Embedding dimension does not match configuration."
            )

        logger.info(
            "Embeddings generated | count=%d | model=%s",
            len(embeddings),
            self.model,
        )

        return embeddings

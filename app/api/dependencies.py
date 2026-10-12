
from app.core.config import settings
from app.repositories.website_repository import WebsiteRepository
from app.repositories.chunk_repository import ChunkRepository
from app.services.scraper_service import ScraperService
from app.services.chunking_service import ChunkingService
from app.services.embedding_service import EmbeddingService
from app.services.ingestion_service import IngestionService
from app.services.llm_service import LLMService
from app.services.retrieval_service import RetrievalService
from app.repositories.website_repository import WebsiteRepository
from app.repositories.chunk_repository import ChunkRepository
from app.services.embedding_service import EmbeddingService


def get_ingestion_service() -> IngestionService:
    """Construct the services required for ingestion."""

    return IngestionService(
        website_repository=WebsiteRepository(),
        chunk_repository=ChunkRepository(),
        scraper=ScraperService(
            timeout_ms=settings.scrape_timeout,
        ),
        chunker=ChunkingService(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
        ),
        embedder=EmbeddingService(),
    )

def get_retrieval_service() -> RetrievalService:
    """Build the retrieval service and its repository dependencies."""

    return RetrievalService(
        website_repository=WebsiteRepository(),
        chunk_repository=ChunkRepository(),
        embedding_service=EmbeddingService(),
    )

def get_llm_service() -> LLMService:
    """Create the language-model service used to answer questions."""

    return LLMService()

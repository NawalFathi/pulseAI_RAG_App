from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest

from app.services.ingestion_service import IngestionService


@pytest.mark.asyncio
async def test_duplicate_url_returns_existing_id_without_reingesting():
    """Reuse a prior ingestion and skip scraping and embedding duplicate URLs."""

    existing_website = SimpleNamespace(
        ingest_id="12345678-1234-1234-1234-123456789012",
        url="https://example.com/",
    )
    website_repository = Mock()
    website_repository.get_by_normalized_url.return_value = existing_website
    scraper = Mock()
    scraper.scrape = AsyncMock()
    embedder = Mock()
    embedder.create_embeddings = AsyncMock()

    service = IngestionService(
        website_repository=website_repository,
        chunk_repository=Mock(),
        scraper=scraper,
        chunker=Mock(),
        embedder=embedder,
    )

    website, already_exists = await service.ingest(
        db=Mock(),
        url="https://example.com/",
    )

    assert website.ingest_id == existing_website.ingest_id
    assert already_exists is True
    scraper.scrape.assert_not_awaited()
    embedder.create_embeddings.assert_not_awaited()


from app.services.chunking_service import (
    ChunkingService,
    TextCleaningService,
)


def test_clean_removes_extra_whitespace():
    """Collapse repeated whitespace while preserving line boundaries."""

    result = TextCleaningService.clean(
        "  Hello   world  \n\n Python   API "
    )

    assert result == "Hello world\nPython API"


def test_clean_removes_duplicate_lines():
    """Remove consecutive duplicate lines from cleaned text."""

    result = TextCleaningService.clean(
        "Welcome\nWelcome\nAbout us"
    )

    assert result == "Welcome\nAbout us"


def test_empty_text_returns_no_chunks():
    """Return no chunks when the source contains only whitespace."""

    service = ChunkingService(
        chunk_size=10,
        chunk_overlap=2,
    )

    assert service.create_chunks("   ") == []


def test_create_chunks_returns_content():
    """Split non-empty text into indexed chunks with content."""

    service = ChunkingService(
        chunk_size=10,
        chunk_overlap=2,
    )

    chunks = service.create_chunks(
        "abcdefghijklmnopqrst"
    )

    assert len(chunks) > 1
    assert chunks[0].chunk_index == 0
    assert chunks[0].content
    assert chunks[1].chunk_index == 1


def test_chunks_have_expected_overlap():
    """Preserve the configured overlap between neighboring chunks."""

    service = ChunkingService(
        chunk_size=10,
        chunk_overlap=2,
    )

    chunks = service.create_chunks(
        "abcdefghijklmnopqrst"
    )

    assert chunks[0].content[-2:] == chunks[1].content[:2]

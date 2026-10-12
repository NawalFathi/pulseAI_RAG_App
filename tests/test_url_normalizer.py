
from app.services.url_normalizer import URLNormalizer


def test_normalize_lowercases_domain():
    """Normalize uppercase domain characters to lowercase."""

    result = URLNormalizer.normalize(
        "https://EXAMPLE.COM/about"
    )

    assert result == "https://example.com/about"


def test_normalize_removes_trailing_slash():
    """Normalize a non-root path by removing its trailing slash."""

    result = URLNormalizer.normalize(
        "https://example.com/about/"
    )

    assert result == "https://example.com/about"


def test_normalize_preserves_query_parameters():
    """Keep query parameters when normalizing a URL."""

    result = URLNormalizer.normalize(
        "https://example.com/search?q=python"
    )

    assert result == "https://example.com/search?q=python"

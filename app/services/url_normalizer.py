
from urllib.parse import urlparse, urlunparse


class URLNormalizer:
    """Normalize URLs for duplicate-ingestion detection."""

    @staticmethod
    def normalize(url: str) -> str:
        """Normalize URL casing and trailing slashes for duplicate checks.

        Query parameters are retained, while fragments are removed because
        they do not identify distinct server-side resources.
        """

        parsed = urlparse(url.strip())

        scheme = parsed.scheme.lower()
        netloc = parsed.netloc.lower()
        path = parsed.path.rstrip("/") or "/"

        return urlunparse(
            (
                scheme,
                netloc,
                path,
                "",
                parsed.query,
                "",
            )
        )

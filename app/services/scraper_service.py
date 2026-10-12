import ipaddress
import logging
import socket

from urllib.parse import urlparse

from bs4 import BeautifulSoup
from playwright.sync_api import (
    sync_playwright,
    Error as PlaywrightError,
    TimeoutError as PlaywrightTimeoutError,
)
from starlette.concurrency import run_in_threadpool

logger = logging.getLogger(__name__)

class ScraperError(Exception):
    """Custom exception for scraping errors."""

class URLValidator:
    """Validates URLs to ensure they are well-formed and not pointing to private IP addresses."""
    AllowedSchemes = {"http", "https"}

    @classmethod
    def validate(cls, url: str) -> None:
        """Reject invalid URLs and private network destinations."""

        parsed = urlparse(url)

        if parsed.scheme.lower() not in cls.AllowedSchemes:
            raise ScraperError(
                f"Invalid URL scheme: {parsed.scheme}. Only HTTP and HTTPS are allowed.")

        hostname = parsed.hostname

        if not hostname:
            raise ScraperError(
            "URL must have a valid hostname."
            )

        if parsed.username or parsed.password:
            raise ScraperError(
                "URL must not contain username or password."
                )

        if hostname.lower() == "localhost":
            raise ScraperError(
                "URL must not point to localhost."
            )

        try:
            addresses = socket.getaddrinfo(
                hostname,
                parsed.port or(443 if parsed.scheme == "https" else 80),
                type = socket.SOCK_STREAM,
            )

        except (socket.gaierror,ValueError,OSError) as exc:
            raise ScraperError(
                "Unable to resolve the website hostname."
            )from exc

        if not addresses:
            raise ScraperError("The hostname has no usable address")

        for address in addresses:
            ip = ipaddress.ip_address(address[4][0])

            if not ip.is_global:
                raise ScraperError(
                    "Private or non-public network destinations "
                    "are not allowed."
                )


class ScraperService:
    """Extract readable text from a public webpage."""
    def __init__(self,timeout_ms:int = 3000):
        """Set the maximum browser navigation and page-wait duration."""

        self.timeout_ms = timeout_ms

    async def scrape(self,url:str)->str:
        """
        Navigate to a URL and return cleaned webpage text.
        Raises:
            ScraperError: If the URL is unsafe, navigation fails,
                the page returns an HTTP error, or no text is found.
        """

        URLValidator.validate(url)
        hostname = urlparse(url).hostname
        logger.info("Scraping started | host=%s", hostname)

        return await run_in_threadpool(self._scrape_sync, url)

    def _scrape_sync(self, url: str) -> str:
        """Load a page in a headless browser and extract its readable text."""

        hostname = urlparse(url).hostname

        with sync_playwright() as playwright:
            browser = None

            try:
                browser = playwright.chromium.launch(headless=True)
                page = browser.new_page()
                page.route("**/*", ScraperService._filter_resources)
                response = page.goto(
                    url,
                    wait_until="domcontentloaded",
                    timeout=self.timeout_ms,
                )

                if response is None:
                    raise ScraperError(
                        "Failed to load the page: no response."
                    )
                if response.status >= 400:
                    raise ScraperError(
                        f"Failed to load the page. HTTP status: {response.status}"
                    )

                page.locator("body").wait_for(
                    state="attached",
                    timeout=self.timeout_ms,
                )
                try:
                    page.wait_for_load_state(
                        "networkidle",
                        timeout=min(self.timeout_ms, 5000),
                    )
                except PlaywrightTimeoutError:
                    logger.debug(
                        "Page did not become network-idle before timeout | host=%s",
                        urlparse(url).hostname,
                    )

                text = ScraperService._extract_text(page.content())
                if not text:
                    raise ScraperError(
                        "No readable text found on the page."
                    )

                logger.info(
                    "Scraping completed | host=%s | characters=%d",
                    hostname,
                    len(text),
                )
                return text
            except PlaywrightTimeoutError as exc:
                logger.warning(
                    "Scraping timed out | host=%s",
                    hostname,
                )
                raise ScraperError(
                    "The website took too long to load."
                ) from exc
            except PlaywrightError as exc:
                logger.exception(
                    "Browser error while scraping | host=%s",
                    hostname,
                )
                raise ScraperError(
                    "Unable to load the website."
                ) from exc
            finally:
                if browser is not None:
                    browser.close()

    @staticmethod
    def _filter_resources(route) -> None:
        """Skip resource types unnecessary for text extraction."""

        if route.request.resource_type in {
            "image",
            "media",
            "font",
        }:
            route.abort()
        else:
            route.continue_()

    @staticmethod
    def _extract_text(html: str) -> str:
        """Remove irrelevant HTML and return readable text."""

        soup = BeautifulSoup(html, "html.parser")

        for element in soup.select(
            "script, style, noscript, nav, footer, "
            "header, aside, svg, canvas, iframe"
        ):
            element.decompose()

        text = soup.get_text(separator="\n")

        lines = [
            " ".join(line.split())
            for line in text.splitlines()
            if line.strip()
        ]

        return "\n".join(lines)

            
    

"""
Handles HTTP requests and overall headline scraping logic.
"""
import logging
import time

import requests
from requests.exceptions import RequestException, Timeout

from .parser import HeadlineParser


class NewsScraper:
    """
    Web scraper for fetching and extracting news headlines from a news site.
    """

    def __init__(
        self, url: str, timeout: int = 20, selectors: list | None = None
    ) -> None:
        """
        Initialize NewsScraper.

        :param url: Target website URL
        :param timeout: Max seconds to wait for response
        :param selectors: List of CSS selectors for headlines
        """
        self.url = url
        self.timeout = timeout
        # Allow user override; if not, parser will use its own defaults
        self.selectors = selectors if selectors else None
        self.logger = logging.getLogger("simple_news_scraper.scraper")

    def fetch_html(self) -> str:
        """
        Fetch HTML from the website. Raises on network errors.
        :returns: HTML string
        """
        self.logger.debug(f"Fetching HTML from {self.url}")
        try:
            start = time.time()
            resp = requests.get(
                self.url,
                timeout=self.timeout,
                headers={
                    "User-Agent": "Mozilla/5.0 (compatible; SimpleNewsScraper/1.0)"
                },
            )
            resp.raise_for_status()
            elapsed = time.time() - start
            self.logger.info(
                f"Fetched {self.url} in {elapsed:.2f} seconds (status {resp.status_code})"
            )
            return resp.text
        except Timeout:
            self.logger.error(f"Request timed out after {self.timeout} seconds")
            raise
        except RequestException as exc:
            self.logger.error(f"HTTP request failed: {exc}")
            raise

    def fetch_headlines(self) -> list[str]:
        """
        Fetch and extract news headlines from the configured website.
        :returns: List of headline strings
        """
        html = self.fetch_html()
        parser = HeadlineParser()
        # Use user selectors if provided, else try detect site and use defaults
        return parser.extract_headlines(html, url=self.url, selectors=self.selectors)

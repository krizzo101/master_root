# scraper/downloader.py
"""
HTTP Downloader with Rate Limiting and Retry
Handles downloading HTML content and rate limiting between requests.
"""
import requests
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)
import time
import logging
from typing import Optional
from requests import Response

logger = logging.getLogger("scraper.downloader")


class Downloader:
    """
    Handles HTTP downloads with rate limiting and retries.
    """

    def __init__(
        self,
        user_agent: str = "PythonNewsScraperBot/1.0",
        rate_limit_seconds: float = 1.0,
        max_attempts: int = 3,
    ):
        self.user_agent = user_agent
        self.rate_limit_seconds = rate_limit_seconds
        self.last_request_time = 0.0
        self.max_attempts = max_attempts

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(min=1, max=8),
        retry=retry_if_exception_type(requests.RequestException),
        reraise=True,
    )
    def get(self, url: str) -> Optional[Response]:
        """
        Fetches the content of the specified URL, with rate limiting and retries.
        Args:
            url (str): The URL to fetch.

        Returns:
            requests.Response | None: HTTP response, else None for failure.
        """
        # rate limiting
        elapsed = time.time() - self.last_request_time
        if elapsed < self.rate_limit_seconds:
            time.sleep(self.rate_limit_seconds - elapsed)
        self.last_request_time = time.time()

        try:
            logger.info(f"Downloading: {url}")
            headers = {"User-Agent": self.user_agent}
            resp = requests.get(url, timeout=10, headers=headers)
            resp.raise_for_status()
            return resp
        except requests.HTTPError as e:
            logger.error(f"HTTP error while downloading {url}: {e}")
            raise e
        except requests.RequestException as e:
            logger.error(f"Request exception for {url}: {e}")
            raise e
        except Exception as e:
            logger.error(f"Unexpected error downloading {url}: {e}")
            raise e

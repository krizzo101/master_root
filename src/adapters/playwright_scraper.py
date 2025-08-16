# mypy: ignore-errors
"""Playwright-based scraper with robots.txt compliance and retries."""
import asyncio
import os
from urllib import robotparser
from urllib.parse import urljoin, urlparse

import httpx
from playwright.async_api import Browser, Page, async_playwright
from playwright.async_api import Error as PlaywrightError

DEFAULT_TIMEOUT = int(os.getenv("SCRAPER_TIMEOUT", "15000"))  # ms
MAX_RETRIES = int(os.getenv("SCRAPER_MAX_RETRIES", "3"))
HEADLESS = os.getenv("SCRAPER_HEADLESS", "true").lower() == "true"
PROXY = os.getenv("SCRAPER_PROXY")  # e.g. http://proxy:3128


async def _is_allowed(url: str) -> bool:
    """Check robots.txt for URL."""
    parsed = urlparse(url)
    robots_url = urljoin(f"{parsed.scheme}://{parsed.netloc}", "/robots.txt")
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(robots_url)
            if resp.status_code != 200:
                return True  # be permissive if robots not accessible
            rp = robotparser.RobotFileParser()
            rp.parse(resp.text.splitlines())
            return rp.can_fetch("*", url)
    except Exception:
        return True  # default allow on error


async def scrape_page(url: str, wait_selector: str | None = None) -> str:
    """Return visible text of the page respecting robots.txt and retries."""
    if not await _is_allowed(url):
        raise PermissionError("Fetching disallowed by robots.txt")

    retry = 0
    backoff = 1
    while True:
        try:
            async with async_playwright() as pw:
                browser: Browser = await pw.chromium.launch(headless=HEADLESS, proxy={"server": PROXY} if PROXY else None)
                page: Page = await browser.new_page()
                await page.goto(url, timeout=DEFAULT_TIMEOUT)
                if wait_selector:
                    await page.wait_for_selector(wait_selector, timeout=DEFAULT_TIMEOUT)
                await browser.close()
                # Simple text extraction
                text = await page.inner_text("body")
                return text
        except (PlaywrightError, httpx.HTTPError) as exc:
            if retry >= MAX_RETRIES:
                raise exc
            await asyncio.sleep(backoff)
            backoff *= 2
            retry += 1

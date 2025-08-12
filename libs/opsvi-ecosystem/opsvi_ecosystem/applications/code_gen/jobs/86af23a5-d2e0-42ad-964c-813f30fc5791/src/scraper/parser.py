# scraper/parser.py
"""
HTML Parser and Headline Extractor:
Parses retrieved HTML using CSS selectors or XPath (BeautifulSoup/lxml) to extract news headlines.
"""
import logging
from typing import Any

from bs4 import BeautifulSoup

logger = logging.getLogger("scraper.parser")


class HeadlineExtractor:
    """
    Extracts headlines according to per-site parsing rules.
    """

    def __init__(self, parsing_rules: dict[str, Any]):
        self.parsing_rules = parsing_rules

    def extract_headlines(self, html: str) -> list[str]:
        """
        Extract headlines using configured CSS selectors or XPaths.
        Args:
            html (str): The HTML content to parse.
        Returns:
            List[str]: List of extracted headline strings.
        """
        try:
            soup = BeautifulSoup(html, "lxml")
        except Exception as e:
            logger.error(f"Failed to parse HTML: {e}")
            return []
        headlines = []
        selectors = self.parsing_rules.get("css_selectors", [])
        if not selectors:
            logger.warning("No parsing rules (css_selectors) provided for this site.")
            return []
        for selector in selectors:
            matches = soup.select(selector)
            for item in matches:
                text = item.get_text(strip=True)
                if text and text not in headlines:
                    headlines.append(text)
        logger.info(f"Extracted {len(headlines)} headlines.")
        return headlines

    def find_next_page_url(self, html: str, base_url: str) -> str | None:
        """
        Attempts to find the next page (pagination) link.
        Args:
            html (str): HTML content.
            base_url (str): Current URL to resolve relative links.
        Returns:
            Optional[str]: Next page URL or None.
        """
        next_page_selector = self.parsing_rules.get("next_page_selector")
        if not next_page_selector:
            return None
        try:
            soup = BeautifulSoup(html, "lxml")
            next_link = soup.select_one(next_page_selector)
            if next_link and next_link.has_attr("href"):
                href = next_link["href"]
                # handle relative URLs
                from urllib.parse import urljoin

                next_page_url = urljoin(base_url, href)
                return next_page_url
            return None
        except Exception as e:
            logger.error(f"Failed to parse next page from HTML: {e}")
            return None

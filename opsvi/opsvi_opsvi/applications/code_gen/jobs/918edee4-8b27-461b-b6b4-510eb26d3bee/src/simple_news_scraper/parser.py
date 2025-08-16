"""
HTML parser module for extracting news headlines with BeautifulSoup.
"""
import logging
import re
from typing import List, Optional
from bs4 import BeautifulSoup
from urllib.parse import urlparse


class HeadlineParser:
    """
    Parses HTML to extract news headlines for supported websites or generic selectors.
    """

    # Map of supported domain fragments to selector lists
    SITE_SELECTOR_MAP = {
        # Example: BBC News
        "bbc.co.uk": [
            "h3.gs-c-promo-heading__title",
            "h3.bbc-1tk6u44.e1v3edc10",
            "h3.bbc-1iy1y6f.e1v3edc10",
            "h3.headline",
        ],
        # Example: CNN
        "cnn.com": ["h2.cd__headline-text", "span.banner-text", ".container__headline"],
        # Example: Reuters
        "reuters.com": [
            "h3.story-title",
            "h2.story-title",
            "h2.Heading_headline",
            "a[data-testid='Heading']",
        ],
        # Example: NY Times
        "nytimes.com": ["h2.css-1j9dxys", "h3.indicate-hover", "h2.esl82me2"],
        # Example: The Guardian
        "theguardian.com": ["a[data-link-name='article']", "h3.fc-item__title"],
        # Example: AP News
        "apnews.com": ["h1.Page-headline", "h2.Component-headline"],
    }

    GENERIC_SELECTORS = [
        "h1",
        "h2",
        "h3",
        "article h1",
        "article h2",
        "article h3",
        "header h1",
        "header h2",
    ]

    def __init__(self) -> None:
        self.logger = logging.getLogger("simple_news_scraper.parser")

    @staticmethod
    def get_domain(url: str) -> str:
        """
        Returns the registered domain (e.g. 'bbc.co.uk', 'cnn.com')
        """
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        parts = domain.split(".")
        if len(parts) > 2:
            # e.g. 'www.bbc.co.uk' -> 'bbc.co.uk'
            return (
                ".".join(parts[-3:])
                if parts[-2] in ("co", "ac", "gov")
                else ".".join(parts[-2:])
            )
        return domain

    def get_selectors_for_url(
        self, url: str, selectors: Optional[list] = None
    ) -> List[str]:
        """
        Get a selector list appropriate for the URL, or fall back to GENERIC_SELECTORS.
        """
        domain = self.get_domain(url)
        self.logger.debug(f"Detected site domain: {domain}")

        if selectors and isinstance(selectors, list) and selectors:
            self.logger.info("Using user-provided headline selectors.")
            return selectors

        for known, sel_list in self.SITE_SELECTOR_MAP.items():
            if known in domain:
                self.logger.info(f"Using custom selectors for {domain}")
                return sel_list

        self.logger.info("Falling back to generic selectors for headlines.")
        return self.GENERIC_SELECTORS

    def extract_headlines(
        self, html: str, url: str, selectors: Optional[list] = None
    ) -> List[str]:
        """
        Given HTML and URL, extract a list of headline text.
        :param html: Raw HTML
        :param url: Source URL (for selector inference)
        :param selectors: (Optional) user-supplied selectors
        :return: List of headlines strings (may be empty)
        """
        soup = BeautifulSoup(html, features="html.parser")
        selectors_to_try = self.get_selectors_for_url(url, selectors)
        headlines = []
        seen = set()
        for selector in selectors_to_try:
            matches = soup.select(selector)
            for el in matches:
                txt = el.get_text(strip=True)
                txt = re.sub(r"\s+", " ", txt).strip()
                if txt and len(txt) > 3 and txt.lower() not in seen:
                    headlines.append(txt)
                    seen.add(txt.lower())
        self.logger.debug(f"Extracted {len(headlines)} candidate headlines.")
        # Try to dedupe (case-insensitive), keep insertion order
        return headlines

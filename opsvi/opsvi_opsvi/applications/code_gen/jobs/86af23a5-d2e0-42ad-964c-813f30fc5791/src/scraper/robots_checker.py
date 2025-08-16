# scraper/robots_checker.py
"""
Robots.txt Compliance Checker:
Fetches and parses robots.txt for each domain. Ensures URLs to scrape are permitted.
"""
from urllib import robotparser
from urllib.parse import urlparse
from typing import Dict
import requests
import logging

USER_AGENT = "PythonNewsScraperBot/1.0"
logger = logging.getLogger("scraper.robots_checker")


class RobotsChecker:
    """
    Checks robots.txt compliance for the specified URLs/domains.
    """

    def __init__(self, user_agent: str = USER_AGENT):
        self.user_agent = user_agent
        self.parsers: Dict[str, robotparser.RobotFileParser] = {}

    def is_allowed(self, url: str) -> bool:
        """
        Checks if the URL may be crawled per robots.txt.
        Args:
            url (str): The URL to be checked.
        Returns:
            bool: True if allowed, False otherwise.
        """
        domain = self._get_domain(url)
        if domain not in self.parsers:
            self.parsers[domain] = self._fetch_robots(domain)
        parser = self.parsers[domain]
        if parser is None:
            # if can't fetch robots.txt, follow conservative approach
            logger.warning(f"Assuming DISALLOW for {url}, unable to fetch robots.txt.")
            return False
        allowed = parser.can_fetch(self.user_agent, url)
        if not allowed:
            logger.warning(f"Scraping not allowed by robots.txt: {url}")
        return allowed

    def _get_domain(self, url: str) -> str:
        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}"

    def _fetch_robots(self, domain: str):
        robots_url = domain.rstrip("/") + "/robots.txt"
        parser = robotparser.RobotFileParser()
        try:
            resp = requests.get(
                robots_url, timeout=5, headers={"User-Agent": self.user_agent}
            )
            if resp.status_code == 200:
                parser.parse(resp.text.splitlines())
                logger.info(f"Fetched robots.txt for {domain}")
                return parser
            else:
                logger.warning(
                    f"robots.txt not found at: {robots_url} (HTTP {resp.status_code})"
                )
                return None
        except requests.RequestException as e:
            logger.error(f"Failed to fetch robots.txt for {domain}: {e}")
            return None

# scraper/url_handler.py
"""
URL Input Handler:
Accepts and validates a single URL or list of URLs for scraping.
Normalizes and prepares the list for processing.
"""
import argparse
import logging
import sys

import validators

logger = logging.getLogger("scraper.url_handler")


def parse_args() -> argparse.Namespace:
    """
    Parse command line arguments.
    """
    parser = argparse.ArgumentParser(
        description="Python Web Scraper for News Headlines"
    )
    parser.add_argument(
        "--urls",
        nargs="+",
        help="One or more news website URLs to scrape.",
        required=False,
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Output file path (CSV, JSON, or TXT). Defaults to 'headlines.csv'.",
        default="headlines.csv",
    )
    parser.add_argument(
        "--format",
        type=str,
        choices=["csv", "json", "txt"],
        default="csv",
        help="Output format (csv, json, or txt). Default: csv.",
    )
    parser.add_argument(
        "--config",
        type=str,
        help="Path to config.yaml file. Default: ./config.yaml.",
        default=None,
    )
    return parser.parse_args()


def normalize_and_validate_urls(urls: list[str]) -> list[str]:
    """
    Validates and normalizes input URLs.
    Args:
        urls (List[str]): List of URL strings.
    Returns:
        List[str]: Cleaned list of valid URLs.
    Raises:
        SystemExit: If any URL is invalid.
    """
    valid_urls = []
    for url in urls:
        url = url.strip()
        if not (url.startswith("http://") or url.startswith("https://")):
            url = "https://" + url
        if not validators.url(url):
            logger.error(f"Invalid URL: {url}")
            print(f"ERROR: Invalid URL: {url}", file=sys.stderr)
            sys.exit(1)
        valid_urls.append(url)
    logger.info(f"Validated URLs: {valid_urls}")
    return valid_urls

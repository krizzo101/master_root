"""
Entry point for Simple Python Web Scraper for News Headlines.
Handles CLI interface, configuration, and calls main logic.
"""
import sys
from argparse import ArgumentParser, Namespace
from typing import Optional, List
import os
from .scraper import NewsScraper
from .output import OutputHandler
from .config import setup_logging, DEFAULT_CONFIG_FILE, load_config
import logging


def parse_args() -> Namespace:
    """
    Parse command-line arguments and return the parsed Namespace.
    """
    parser = ArgumentParser(description="Simple Python Web Scraper for News Headlines")
    parser.add_argument("--url", type=str, help="Target news website URL to scrape")
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output file path to store headlines (optional)",
    )
    parser.add_argument(
        "--config", type=str, default=None, help="Path to config file (optional)"
    )
    parser.add_argument(
        "--loglevel",
        type=str,
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default=None,
        help="Override logging level for this run",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    # Load config from file if exists
    config_path = args.config or DEFAULT_CONFIG_FILE
    config = load_config(config_path)

    # Allow command-line args to override config
    url = args.url or config.get("url")
    output_file = args.output or config.get("output_file")
    timeout = config.get("timeout", 20)
    loglevel = args.loglevel or config.get("loglevel", "INFO")
    selectors = config.get("headline_selectors", [])

    setup_logging(loglevel=loglevel)
    logger = logging.getLogger("simple_news_scraper")

    if not url:
        logger.error("No URL provided. Use --url or set it in the config file.")
        sys.exit(1)

    logger.info(f"Scraping news headlines from {url}")
    try:
        scraper = NewsScraper(url=url, timeout=timeout, selectors=selectors)
        headlines = scraper.fetch_headlines()
    except Exception as exc:
        logger.error(f"Failed to fetch headlines: {exc}")
        sys.exit(2)

    if not headlines:
        logger.warning("No headlines found.")
    else:
        OutputHandler.print_headlines(headlines)
        if output_file:
            try:
                OutputHandler.save_headlines(headlines, output_file)
                logger.info(f"Headlines saved to {os.path.abspath(output_file)}")
            except Exception as exc:
                logger.error(f"Failed to write headlines to file: {exc}")


if __name__ == "__main__":
    main()

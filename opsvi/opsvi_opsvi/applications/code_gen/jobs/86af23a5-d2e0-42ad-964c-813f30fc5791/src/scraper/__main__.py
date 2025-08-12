# scraper/__main__.py
"""
Python Web Scraper for News Headlines
Main Execution Script
"""
import logging
import sys

from .config import load_config
from .downloader import Downloader
from .output_writer import write_headlines
from .parser import HeadlineExtractor
from .robots_checker import RobotsChecker
from .url_handler import normalize_and_validate_urls, parse_args


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )


def aggregate_headlines(
    urls: list[str], config: dict, output_fmt: str, output_file: str
) -> list[dict[str, str]]:
    """
    Orchestrates scraping workflow and aggregates all headlines.
    Returns:
        List[Dict]: Each dict has 'url' and 'headline'.
    """
    global_settings = config.get("global", {})
    user_agent = global_settings.get("user_agent", "PythonNewsScraperBot/1.0")
    rate_limit = global_settings.get("rate_limit_seconds", 1.0)
    max_pages = global_settings.get("max_pages", 3)

    robots_checker = RobotsChecker(user_agent=user_agent)
    downloader = Downloader(user_agent=user_agent, rate_limit_seconds=rate_limit)

    all_results = []
    for url in urls:
        # Map hostname to parsing rules (or fallback to 'default')
        from urllib.parse import urlparse

        parsed = urlparse(url)
        hostname = parsed.netloc
        site_rules = config.get("sites", {}).get(hostname)
        if not site_rules:
            logging.warning(
                f"No parsing rules found for {hostname}, using default parsing rules."
            )
            site_rules = config.get("sites", {}).get("default")
        if not site_rules:
            logging.error(f"No parsing rules available for {url}; skipping.")
            continue
        extractor = HeadlineExtractor(site_rules)
        if not robots_checker.is_allowed(url):
            logging.warning(f"Skipping URL due to robots.txt: {url}")
            continue
        to_scrape_urls = [url]
        pages_scraped = 0
        while to_scrape_urls and pages_scraped < max_pages:
            current_url = to_scrape_urls.pop(0)
            try:
                resp = downloader.get(current_url)
            except Exception as e:
                logging.error(f"Failed to download {current_url}: {e}")
                break
            if not resp or not resp.text:
                logging.error(f"No content retrieved from {current_url}")
                break
            headlines = extractor.extract_headlines(resp.text)
            # Aggregate results with URL
            for h in headlines:
                all_results.append({"url": url, "headline": h})
            # Pagination handling
            next_page_url = extractor.find_next_page_url(resp.text, current_url)
            if (
                next_page_url
                and next_page_url != current_url
                and next_page_url not in to_scrape_urls
            ):
                if robots_checker.is_allowed(next_page_url):
                    to_scrape_urls.append(next_page_url)
                    logging.info(f"Discovered next page: {next_page_url}")
                else:
                    logging.info(
                        f"Next page {next_page_url} not allowed by robots.txt; stopping pagination."
                    )
                    break
            else:
                break
            pages_scraped += 1
    return all_results


def main():
    setup_logging()
    args = parse_args()
    config = load_config(args.config)
    # Input URLs
    if not args.urls:
        print("ERROR: You must provide at least one --urls argument.", file=sys.stderr)
        sys.exit(1)
    urls = normalize_and_validate_urls(args.urls)
    logging.info(f"Scraping headlines from: {urls}")
    data = aggregate_headlines(
        urls=urls, config=config, output_fmt=args.format, output_file=args.output
    )
    if data:
        write_headlines(data, args.output, args.format)
        print(f"Scraping complete. Headlines written to {args.output}")
    else:
        print("No headlines were extracted.")


if __name__ == "__main__":
    main()

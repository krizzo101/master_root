#!/usr/bin/env python3
"""
Firecrawl MCP Client - Web Scraping and Crawling via MCP

This script provides a Python interface to the Firecrawl MCP server for web scraping,
crawling, and content extraction. Firecrawl is a powerful web scraping API that can
extract clean markdown content from websites.

## Official Documentation

- Firecrawl MCP Server: https://github.com/mendableai/firecrawl-mcp
- Firecrawl API: https://docs.firecrawl.dev/
- Firecrawl Python SDK: https://github.com/mendableai/firecrawl-py

## Prerequisites

```bash
# Install MCP Python SDK
pip install "mcp[cli]"

# Install Firecrawl MCP server
npm install -g firecrawl-mcp

# Get API key from https://firecrawl.dev/
```

## Configuration

Add to mcp.json:
```json
{
  "mcpServers": {
    "firecrawl": {
      "command": "npx",
      "args": ["-y", "firecrawl-mcp"],
      "env": {
        "FIRECRAWL_API_KEY": "your_api_key_here"
      }
    }
  }
}
```

## Features

- **Scrape**: Extract content from single web pages
- **Crawl**: Recursively crawl websites with depth control
- **Map**: Discover all URLs on a website
- **Search**: Search the web for specific content
- **Extract**: Extract structured data using LLM
- **Batch Operations**: Process multiple URLs efficiently
"""

import asyncio
from contextlib import asynccontextmanager
from dataclasses import dataclass
import json
import logging
import os
from pathlib import Path
import sys
from typing import Any, Dict, List, Optional

# MCP imports
try:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    from mcp.types import CallToolResult, TextContent
except ImportError:
    print("Error: MCP Python SDK not installed.")
    print("Install with: pip install 'mcp[cli]'")
    sys.exit(1)


# Custom exceptions
class FirecrawlError(Exception):
    """Base exception for Firecrawl-related errors."""

    pass


@dataclass
class ScrapingResult:
    """Result from web scraping operation."""

    url: str
    content: str
    success: bool = True
    error: str = ""
    format: str = "markdown"

    def __str__(self) -> str:
        return f"Scraped: {self.url} - {len(self.content)} chars"


@dataclass
class CrawlResult:
    """Result from web crawling operation."""

    job_id: str
    status: str
    urls_crawled: int = 0
    pages: List[Dict[str, Any]] = None
    success: bool = True
    error: str = ""

    def __post_init__(self):
        if self.pages is None:
            self.pages = []


class FirecrawlMCPClient:
    """
    Client for interacting with Firecrawl MCP server.

    This client provides high-level methods for web scraping, crawling,
    and content extraction using the Firecrawl service through MCP.
    """

    def __init__(self, mcp_config_path: Optional[str] = None, debug: bool = False):
        """
        Initialize the Firecrawl MCP client.

        Args:
            mcp_config_path: Path to mcp.json config file
            debug: Enable debug logging
        """
        self.mcp_config_path = mcp_config_path or "/home/opsvi/.cursor/mcp.json"
        self.debug = debug

        # Setup logging
        logging.basicConfig(
            level=logging.DEBUG if debug else logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )
        self.logger = logging.getLogger(__name__)

    @asynccontextmanager
    async def _get_session(self):
        """Create and manage an MCP session with Firecrawl server."""
        # Load server configuration
        config_path = Path(self.mcp_config_path)
        if not config_path.exists():
            raise FileNotFoundError(f"MCP config file not found: {config_path}")

        with open(config_path) as f:
            config = json.load(f)

        firecrawl_config = config.get("mcpServers", {}).get("web_scraping", {})
        if not firecrawl_config:
            raise ValueError("Firecrawl server not found in MCP configuration")

        # Server parameters for stdio connection
        server_params = StdioServerParameters(
            command=firecrawl_config.get("command", "npx"),
            args=firecrawl_config.get("args", ["-y", "firecrawl-mcp"]),
            env={**os.environ, **firecrawl_config.get("env", {})},
        )

        try:
            async with stdio_client(server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    self.logger.debug("Firecrawl MCP session initialized")
                    yield session
        except Exception as e:
            self.logger.error(f"Failed to establish MCP session: {e}")
            raise FirecrawlError(f"Failed to connect to Firecrawl MCP server: {e}")

    async def scrape(
        self,
        url: str,
        formats: List[str] = None,
        only_main_content: bool = True,
        timeout: int = 30000,
    ) -> ScrapingResult:
        """Scrape content from a single URL."""
        if not url.strip():
            raise ValueError("URL cannot be empty")

        if formats is None:
            formats = ["markdown"]

        arguments = {
            "url": url,
            "formats": formats,
            "onlyMainContent": only_main_content,
            "timeout": timeout,
        }

        self.logger.info(f"Scraping URL: {url}")

        async with self._get_session() as session:
            try:
                result = await session.call_tool("firecrawl_scrape", arguments)

                if result.content:
                    content = result.content[0]
                    if isinstance(content, TextContent):
                        try:
                            data = json.loads(content.text)
                            return ScrapingResult(
                                url=url,
                                content=data.get("markdown", content.text),
                                success=True,
                                format="markdown",
                            )
                        except json.JSONDecodeError:
                            return ScrapingResult(
                                url=url,
                                content=content.text,
                                success=True,
                                format="text",
                            )

                return ScrapingResult(
                    url=url, content="", success=False, error="No content received"
                )

            except Exception as e:
                self.logger.error(f"Scraping failed: {e}")
                return ScrapingResult(url=url, content="", success=False, error=str(e))

    async def crawl(
        self,
        url: str,
        max_depth: int = 2,
        limit: int = 50,
        allow_external_links: bool = False,
    ) -> CrawlResult:
        """Start a crawl job on a website."""
        if not url.strip():
            raise ValueError("URL cannot be empty")

        arguments = {
            "url": url,
            "maxDepth": max_depth,
            "limit": limit,
            "allowExternalLinks": allow_external_links,
            "scrapeOptions": {"formats": ["markdown"], "onlyMainContent": True},
        }

        self.logger.info(f"Starting crawl for: {url}")

        async with self._get_session() as session:
            try:
                result = await session.call_tool(
                    "mcp_web_scraping_firecrawl_crawl", arguments
                )

                if result.content:
                    content = result.content[0]
                    if isinstance(content, TextContent):
                        try:
                            data = json.loads(content.text)
                            return CrawlResult(
                                job_id=data.get("id", ""),
                                status=data.get("status", "started"),
                                success=True,
                            )
                        except json.JSONDecodeError:
                            return CrawlResult(
                                job_id="", status=content.text, success=True
                            )

                return CrawlResult(
                    job_id="",
                    status="error",
                    success=False,
                    error="No response received",
                )

            except Exception as e:
                self.logger.error(f"Crawl failed: {e}")
                return CrawlResult(
                    job_id="", status="error", success=False, error=str(e)
                )

    async def check_crawl_status(self, job_id: str) -> CrawlResult:
        """Check the status of a crawl job."""
        if not job_id.strip():
            raise ValueError("Job ID cannot be empty")

        arguments = {"id": job_id}
        self.logger.info(f"Checking crawl status: {job_id}")

        async with self._get_session() as session:
            try:
                result = await session.call_tool(
                    "mcp_web_scraping_firecrawl_check_crawl_status", arguments
                )

                if result.content:
                    content = result.content[0]
                    if isinstance(content, TextContent):
                        try:
                            data = json.loads(content.text)
                            return CrawlResult(
                                job_id=job_id,
                                status=data.get("status", "unknown"),
                                urls_crawled=len(data.get("data", [])),
                                pages=data.get("data", []),
                                success=True,
                            )
                        except json.JSONDecodeError:
                            return CrawlResult(
                                job_id=job_id, status=content.text, success=True
                            )

                return CrawlResult(
                    job_id=job_id,
                    status="error",
                    success=False,
                    error="No status received",
                )

            except Exception as e:
                self.logger.error(f"Status check failed: {e}")
                return CrawlResult(
                    job_id=job_id, status="error", success=False, error=str(e)
                )

    async def search(
        self, query: str, limit: int = 10, scrape_results: bool = True
    ) -> List[ScrapingResult]:
        """Search the web and optionally scrape results."""
        if not query.strip():
            raise ValueError("Query cannot be empty")

        arguments = {"query": query, "limit": limit}

        if scrape_results:
            arguments["scrapeOptions"] = {
                "formats": ["markdown"],
                "onlyMainContent": True,
            }

        self.logger.info(f"Searching for: {query}")

        async with self._get_session() as session:
            try:
                result = await session.call_tool(
                    "mcp_web_scraping_firecrawl_search", arguments
                )

                results = []
                if result.content:
                    content = result.content[0]
                    if isinstance(content, TextContent):
                        try:
                            data = json.loads(content.text)
                            search_results = (
                                data
                                if isinstance(data, list)
                                else data.get("results", [])
                            )

                            for item in search_results:
                                results.append(
                                    ScrapingResult(
                                        url=item.get("url", ""),
                                        content=item.get(
                                            "markdown", item.get("content", "")
                                        ),
                                        success=True,
                                        format="markdown",
                                    )
                                )
                        except json.JSONDecodeError:
                            pass

                return results

            except Exception as e:
                self.logger.error(f"Search failed: {e}")
                return []


# Utility functions
async def quick_scrape(url: str, **kwargs) -> ScrapingResult:
    """Quick scrape a single URL."""
    client = FirecrawlMCPClient()
    return await client.scrape(url, **kwargs)


# Command line interface
async def main():
    """Command line interface for Firecrawl MCP client."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Firecrawl MCP Client - Web Scraping and Crawling",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Scrape a single page
  python firecrawl_mcp_client.py scrape "https://example.com"

  # Map a website's URLs
  python firecrawl_mcp_client.py map "https://example.com" --limit 50

  # Search the web
  python firecrawl_mcp_client.py search "Python tutorial" --limit 3
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Scrape command
    scrape_parser = subparsers.add_parser("scrape", help="Scrape a single URL")
    scrape_parser.add_argument("url", help="URL to scrape")
    scrape_parser.add_argument(
        "--formats", nargs="+", default=["markdown"], help="Output formats"
    )
    scrape_parser.add_argument(
        "--full-content", action="store_true", help="Include all content"
    )

    # Crawl command
    crawl_parser = subparsers.add_parser("crawl", help="Crawl a website")
    crawl_parser.add_argument("url", help="URL to crawl")
    crawl_parser.add_argument(
        "--max-depth", type=int, default=2, help="Maximum crawl depth"
    )
    crawl_parser.add_argument("--limit", type=int, default=20, help="Maximum pages")

    # Search command
    search_parser = subparsers.add_parser("search", help="Search the web")
    search_parser.add_argument("query", help="Search query")
    search_parser.add_argument("--limit", type=int, default=5, help="Number of results")
    search_parser.add_argument(
        "--no-scrape", action="store_true", help="Don't scrape results"
    )

    # Global options
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument("--config", help="Path to mcp.json config file")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    try:
        client = FirecrawlMCPClient(mcp_config_path=args.config, debug=args.debug)

        if args.command == "scrape":
            result = await client.scrape(
                args.url, formats=args.formats, only_main_content=not args.full_content
            )

            if result.success:
                print(f"✅ Scraped: {result.url}")
                print("=" * 50)
                print(
                    result.content[:2000] + "..."
                    if len(result.content) > 2000
                    else result.content
                )
            else:
                print(f"❌ Error: {result.error}")

        elif args.command == "crawl":
            result = await client.crawl(
                args.url, max_depth=args.max_depth, limit=args.limit
            )

            if result.success:
                print(f"✅ Crawl started: {result.job_id}")
                print(f"Status: {result.status}")
            else:
                print(f"❌ Error: {result.error}")

        elif args.command == "search":
            results = await client.search(
                args.query, limit=args.limit, scrape_results=not args.no_scrape
            )

            print(f"✅ Found {len(results)} results for: '{args.query}'")
            for i, result in enumerate(results, 1):
                print(f"\n{i}. {result.url}")
                if result.content:
                    content_preview = (
                        result.content[:200] + "..."
                        if len(result.content) > 200
                        else result.content
                    )
                    print(f"   {content_preview}")

    except KeyboardInterrupt:
        print("\nOperation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

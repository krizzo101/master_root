"""simple_research_script.py

This module provides a SimpleResearcher class for conducting asynchronous
research on a topic using Brave Search and Firecrawl, and saving the results
to a JSON file. It includes an asynchronous main() entry point for
command-line usage.
"""

from src.tools.code_generation.o3_code_generator.o3_logger.logger import (
    LogConfig,
    setup_logger,
)

setup_logger(LogConfig())
import argparse
import asyncio
import time
from pathlib import Path
from typing import Any

try:
    from shared.mcp.brave_mcp_search import BraveMCPSearch, quick_search
    from shared.mcp.firecrawl_mcp_client import FirecrawlMCPClient

    MCP_AVAILABLE: bool = True
except ImportError:
    MCP_AVAILABLE: bool = False
else:
    pass
finally:
    pass
from src.tools.code_generation.o3_code_generator.o3_logger.logger import get_logger
from src.tools.code_generation.o3_code_generator.utils.directory_manager import (
    DirectoryManager,
)
from src.tools.code_generation.o3_code_generator.utils.file_generator import (
    FileGenerator,
)
from src.tools.code_generation.o3_code_generator.utils.output_formatter import (
    OutputFormatter,
)


class SimpleResearcher:
    """
    Represents a basic researcher with methods to conduct and manage research tasks.

    Attributes:
        logger: O3Logger instance for logging.
        brave_search: Instance of BraveMCPSearch if available, else None.
        firecrawl_client: Instance of FirecrawlMCPClient if available, else None.
    """

    def __init__(self) -> None:
        """
        Initialize the SimpleResearcher, setting up MCP tool clients.
        Raises ImportError if MCP tools are not available.
        """
        self.logger = get_logger(__name__)
        if not MCP_AVAILABLE:
            self.logger.log_error("MCP tools not available at initialization")
            raise ImportError("MCP tools not available")
        else:
            pass
        try:
            self.brave_search = BraveMCPSearch()
            self.firecrawl_client = FirecrawlMCPClient()
            self.logger.log_info("MCP tools initialized successfully")
        except Exception as e:
            self.logger.log_error(f"Failed to initialize MCP tools: {e}")
            raise
        else:
            pass
        finally:
            pass

    async def search_topic(
        self, query: str, max_results: int = 5
    ) -> list[dict[str, Any]]:
        """
        Search for information about a topic using Brave Search.

        Args:
            query: Search query.
            max_results: Maximum number of results to return.

        Returns:
            List of search results with title, url, and description.
        """
        assert (
            hasattr(self, "brave_search") and self.brave_search is not None
        ), "BraveMCPSearch is not initialized"
        try:
            self.logger.log_info(f"Searching for: {query}")
            response = await quick_search(query, count=max_results)
            results: list[dict[str, Any]] = [
                {"title": item.title, "url": item.url, "description": item.description}
                for item in response.results
            ]
            self.logger.log_info(f"Found {len(results)} search results")
            return results
        except Exception as e:
            self.logger.log_error(f"Search failed: {e}")
            raise
        else:
            pass
        finally:
            pass

    async def scrape_url(self, url: str) -> str:
        """
        Scrape content from a URL using Firecrawl.

        Args:
            url: URL to scrape.

        Returns:
            Scraped content as string.
        """
        assert (
            hasattr(self, "firecrawl_client") and self.firecrawl_client is not None
        ), "FirecrawlMCPClient is not initialized"
        try:
            self.logger.log_info(f"Scraping URL: {url}")
            response = await self.firecrawl_client.scrape(url, formats=["markdown"])
            return response or ""
        except Exception as e:
            self.logger.log_error(f"Scraping failed for {url}: {e}")
            raise
        else:
            pass
        finally:
            pass

    async def research_topic(self, query: str, max_results: int = 3) -> dict[str, Any]:
        """
        Perform comprehensive research on a topic.

        Args:
            query: Research query.
            max_results: Maximum number of URLs to scrape.

        Returns:
            Research results as dictionary.
        """
        self.logger.log_info(f"Starting research on: {query}")
        try:
            search_results = await self.search_topic(query, max_results)
        except Exception as e:
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            self.logger.log_error(f"Research search failed: {e}")
            return {
                "query": query,
                "search_results": [],
                "scraped_content": {},
                "timestamp": timestamp,
                "error": str(e),
            }
        else:
            pass
        finally:
            pass
        if not search_results:
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            return {
                "query": query,
                "search_results": [],
                "scraped_content": {},
                "timestamp": timestamp,
                "error": "No search results found",
            }
        else:
            pass
        scraped_content: dict[str, dict[str, Any]] = {}
        for index, result in enumerate(search_results[:max_results], start=1):
            url = result["url"]
            self.logger.log_info(
                f"Scraping result {index}/{len(search_results)}: {url}"
            )
            try:
                content = await self.scrape_url(url)
                if content:
                    scraped_content[url] = {
                        "title": result["title"],
                        "content": content[:5000],
                        "scraped_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                    }
                else:
                    pass
            except Exception as e:
                self.logger.log_warning(f"Failed to scrape {url}: {e}")
            else:
                pass
            finally:
                pass
            await asyncio.sleep(1)
        else:
            pass
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        report: dict[str, Any] = {
            "query": query,
            "search_results": search_results,
            "scraped_content": scraped_content,
            "timestamp": timestamp,
            "summary": f"Researched '{query}' with {len(search_results)} results and {len(scraped_content)} scraped pages",
        }
        self.logger.log_info(f"Research completed: {report['summary']}")
        return report

    def save_research_report(self, report: dict[str, Any], output_dir: str) -> str:
        """
        Save research report to a JSON file.

        Args:
            report: Research report dictionary.
            output_dir: Directory to save the report.

        Returns:
            Path to the saved file.
        """
        directory_manager = DirectoryManager()
        file_generator = FileGenerator()
        formatter = OutputFormatter()
        try:
            directory_manager.ensure_directory_exists(output_dir)
            safe_query = "".join(c if c.isalnum() else "_" for c in report["query"])[
                :50
            ]
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"research_{safe_query}_{timestamp}.json"
            filepath = Path(output_dir) / filename
            content = formatter.to_json(report, pretty=True)
            file_generator.save_file(content, filepath)
            self.logger.log_info(f"Research report saved to: {filepath}")
            return str(filepath)
        except Exception as e:
            self.logger.log_error(f"Failed to save report: {e}")
            raise
        else:
            pass
        finally:
            pass


async def main() -> None:
    """
    Main entry point for the research script.
    """
    parser = argparse.ArgumentParser(
        description="Research current APIs and technologies using MCP tools"
    )
    parser.add_argument("--query", type=str, required=True, help="Research query")
    parser.add_argument(
        "--output-dir", type=str, default="research_results", help="Output directory"
    )
    parser.add_argument(
        "--max-results", type=int, default=3, help="Maximum URLs to scrape"
    )
    args = parser.parse_args()
    logger = get_logger(__name__)
    if not MCP_AVAILABLE:
        logger.log_error("MCP tools not available. Please check your installation.")
        raise SystemExit(1)
    else:
        pass
    researcher = SimpleResearcher()
    report = await researcher.research_topic(args.query, args.max_results)
    try:
        filepath = researcher.save_research_report(report, args.output_dir)
    except Exception:
        logger.log_error("Research failed to save report.")
        raise SystemExit(1)
    else:
        pass
    finally:
        pass
    logger.log_info("✅ Research completed successfully!")
    logger.log_info(f"📁 Report saved to: {filepath}")
    logger.log_info(f"🔍 Query: {report['query']}")
    logger.log_info(
        f"📊 Results: {len(report['search_results'])} search results, {len(report['scraped_content'])} scraped pages"
    )
    if report["scraped_content"]:
        logger.log_info("📄 Content Preview:")
        for url, data in list(report["scraped_content"].items())[:2]:
            logger.log_info(f"  • {data['title']}")
            logger.log_info(f"    {data['content'][:200]}...")
        else:
            pass
    else:
        logger.log_warning("No content was scraped.")


if __name__ == "__main__":
    asyncio.run(main())
else:
    pass

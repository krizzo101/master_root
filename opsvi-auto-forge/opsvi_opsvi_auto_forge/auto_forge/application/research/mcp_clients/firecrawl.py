"""Firecrawl client implementation for web scraping."""

import logging

from ..models import SearchResult, SourceType
from .base import BaseMCPClient

logger = logging.getLogger(__name__)


class FirecrawlClient(BaseMCPClient):
    """Firecrawl client for web scraping using MCP."""

    def _get_source_type(self) -> SourceType:
        return SourceType.SCRAPE

    async def search(self, query: str, **kwargs) -> list[SearchResult]:
        """Search using Firecrawl web scraping."""
        if not self.api_key:
            logger.warning("Firecrawl API key not configured, returning empty results")
            return []

        count = kwargs.get("count", self.max_results)
        urls = kwargs.get("urls", [])

        async def _search():
            try:
                results = await self._call_firecrawl_mcp(query, urls, count)
                return results
            except Exception as e:
                logger.error(f"Firecrawl search failed: {e}")
                return []

        return await self._execute_with_timeout(_search())

    async def _call_firecrawl_mcp(
        self, query: str, urls: list[str], count: int
    ) -> list[SearchResult]:
        """Call the Firecrawl MCP server."""
        # This is a placeholder for the actual MCP integration
        # In a real implementation, this would call the MCP server

        # Simulate results for testing
        mock_results = []

        if urls:
            # If specific URLs provided, scrape them
            for i, url in enumerate(urls[:count]):
                mock_results.append(
                    {
                        "title": f"Scraped content from {url}",
                        "url": url,
                        "snippet": f"Content scraped from {url} related to '{query}'",
                        "content": f"Full scraped content from {url} for query '{query}'",
                        "score": 0.9 - (i * 0.1),
                    }
                )
        else:
            # Simulate general scraping results
            mock_results = [
                {
                    "title": f"Scraped Result 1 for: {query}",
                    "url": f"https://example.com/scrape1?q={query}",
                    "snippet": f"Scraped content related to '{query}'",
                    "content": f"Full scraped content for '{query}' from example.com",
                    "score": 0.85,
                },
                {
                    "title": f"Scraped Result 2 for: {query}",
                    "url": f"https://example.com/scrape2?q={query}",
                    "snippet": f"Another scraped content for '{query}'",
                    "content": f"More scraped content for '{query}' from example.com",
                    "score": 0.75,
                },
            ]

        results = []
        for i, result in enumerate(mock_results[:count]):
            search_result = self._create_search_result(
                url=result["url"],
                title=result["title"],
                snippet=result["snippet"],
                content=result.get("content"),
                score=result["score"],
                metadata={"source": "firecrawl", "rank": i + 1},
            )
            results.append(search_result)

        return results

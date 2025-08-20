"""Context7 client implementation for technical documentation."""

import logging

from ..models import SearchResult, SourceType
from .base import BaseMCPClient

logger = logging.getLogger(__name__)


class Context7Client(BaseMCPClient):
    """Context7 client for technical documentation using MCP."""

    def _get_source_type(self) -> SourceType:
        return SourceType.DOCS

    async def search(self, query: str, **kwargs) -> list[SearchResult]:
        """Search using Context7 technical documentation."""
        if not self.api_key:
            logger.warning("Context7 API key not configured, returning empty results")
            return []

        count = kwargs.get("count", self.max_results)
        library_id = kwargs.get("library_id")
        topic = kwargs.get("topic")
        tokens = kwargs.get("tokens", 10000)

        async def _search():
            try:
                results = await self._call_context7_mcp(
                    query, count, library_id, topic, tokens
                )
                return results
            except Exception as e:
                logger.error(f"Context7 search failed: {e}")
                return []

        return await self._execute_with_timeout(_search())

    async def _call_context7_mcp(
        self,
        query: str,
        count: int,
        library_id: str | None,
        topic: str | None,
        tokens: int,
    ) -> list[SearchResult]:
        """Call the Context7 MCP server."""
        # This is a placeholder for the actual MCP integration
        # In a real implementation, this would call the MCP server

        # Simulate results for testing
        mock_results = [
            {
                "title": f"Context7 Documentation: {query} - API Reference",
                "url": f"https://docs.context7.com/api/{query.lower().replace(' ', '-')}",
                "snippet": f"API documentation for {query} including parameters, return types, and examples.",
                "content": f"Complete API reference for {query} with code examples and best practices.",
                "score": 0.92,
                "library": "context7",
                "section": "api-reference",
            },
            {
                "title": f"Context7 Guide: Getting Started with {query}",
                "url": f"https://docs.context7.com/guides/{query.lower().replace(' ', '-')}",
                "snippet": f"Step-by-step guide for implementing {query} in your project.",
                "content": f"Comprehensive guide covering installation, configuration, and usage of {query}.",
                "score": 0.88,
                "library": "context7",
                "section": "guides",
            },
            {
                "title": f"Context7 Tutorial: Advanced {query} Techniques",
                "url": f"https://docs.context7.com/tutorials/{query.lower().replace(' ', '-')}",
                "snippet": f"Advanced techniques and patterns for working with {query}.",
                "content": f"Deep dive into advanced features and optimization techniques for {query}.",
                "score": 0.85,
                "library": "context7",
                "section": "tutorials",
            },
        ]

        # Filter by library_id if specified
        if library_id:
            mock_results = [
                result for result in mock_results if result.get("library") == library_id
            ]

        # Filter by topic if specified
        if topic:
            mock_results = [
                result
                for result in mock_results
                if topic.lower() in result.get("section", "").lower()
            ]

        results = []
        for i, result in enumerate(mock_results[:count]):
            search_result = self._create_search_result(
                url=result["url"],
                title=result["title"],
                snippet=result["snippet"],
                content=result.get("content"),
                score=result["score"],
                metadata={
                    "source": "context7",
                    "rank": i + 1,
                    "library": result.get("library"),
                    "section": result.get("section"),
                    "tokens": tokens,
                },
            )
            results.append(search_result)

        return results

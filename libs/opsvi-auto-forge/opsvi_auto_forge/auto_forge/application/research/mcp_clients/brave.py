"""Brave MCP client for web search."""

import asyncio
import json
import logging
from contextlib import asynccontextmanager
from typing import List, Optional

try:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    from mcp.types import CallToolResult, TextContent
except ImportError:
    print("Warning: MCP Python SDK not installed. Install with: pip install 'mcp[cli]'")
    # Fallback to mock implementation
    MCP_AVAILABLE = False
else:
    MCP_AVAILABLE = True

from ..models import SearchResult, SourceType
from ..errors import ClientError


class BraveClient:
    """Real Brave MCP client for web search."""

    def __init__(self, config=None):
        self.config = config or {}
        self.name = "brave"
        self.timeout = config.get("timeout", 30.0) if config else 30.0
        self.max_results = config.get("max_results", 10) if config else 10
        self.api_key = config.get("api_key") if config else None
        self.logger = logging.getLogger(__name__)

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        pass

    def _get_source_type(self) -> SourceType:
        """Get the source type for this client."""
        return SourceType.WEB

    @asynccontextmanager
    async def _get_mcp_session(self):
        """Create and manage MCP session with Brave server."""
        if not MCP_AVAILABLE:
            raise ClientError("MCP Python SDK not available", self.name)

        # Server parameters for stdio connection
        server_params = StdioServerParameters(
            command="npx",
            args=["-y", "brave-search-mcp"],
            env={"BRAVE_API_KEY": self.api_key} if self.api_key else {},
        )

        try:
            async with stdio_client(server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    # Initialize the connection
                    await session.initialize()
                    self.logger.debug("Brave MCP session initialized successfully")
                    yield session
        except Exception as e:
            self.logger.error(f"Failed to establish Brave MCP session: {e}")
            raise ClientError(f"Failed to connect to Brave MCP server: {e}", self.name)

    def _parse_search_results(
        self, tool_result: CallToolResult, query: str
    ) -> List[SearchResult]:
        """Parse MCP tool result into SearchResult objects."""
        try:
            # Extract content from MCP result
            if not tool_result.content:
                return []

            content = tool_result.content[0]
            if isinstance(content, TextContent):
                # Try to parse as JSON first
                try:
                    data = json.loads(content.text)
                    if isinstance(data, dict) and "web" in data:
                        # Brave API response format
                        web_results = data["web"]["results"]
                        results = []
                        for item in web_results:
                            results.append(
                                SearchResult(
                                    source=self._get_source_type(),
                                    url=item.get("url", ""),
                                    title=item.get("title", ""),
                                    snippet=item.get("description", ""),
                                    score=0.8,  # Default score for web results
                                    metadata={
                                        "source": "brave",
                                        "rank": len(results) + 1,
                                    },
                                )
                            )
                        return results
                except json.JSONDecodeError:
                    # If not JSON, treat as plain text
                    pass

                # Fallback: treat as plain text
                return [
                    SearchResult(
                        source=self._get_source_type(),
                        url="",
                        title="Search Results",
                        snippet=content.text,
                        score=0.5,
                        metadata={"source": "brave", "error": "non-json-response"},
                    )
                ]

        except Exception as e:
            self.logger.error(f"Error parsing Brave search results: {e}")

        return []

    async def search(self, query: str, **kwargs) -> List[SearchResult]:
        """Search using Brave MCP server."""
        if not MCP_AVAILABLE:
            # Fallback to mock implementation
            return self._mock_search(query, **kwargs)

        try:
            async with self._get_mcp_session() as session:
                # Call the Brave search tool
                result = await session.call_tool(
                    "mcp_mcp_web_search_brave_web_search",
                    {
                        "query": query,
                        "count": min(kwargs.get("count", self.max_results), 20),
                    },
                )

                return self._parse_search_results(result, query)

        except Exception as e:
            self.logger.error(f"Brave search failed: {e}")
            raise ClientError(f"Brave search failed: {e}", self.name)

    def _mock_search(self, query: str, **kwargs) -> List[SearchResult]:
        """Mock search implementation for testing."""
        return [
            SearchResult(
                source=self._get_source_type(),
                url="https://example.com/result1",
                title=f"Mock Brave Result 1 for: {query}",
                snippet=f"This is a mock search result for the query: {query}",
                score=0.8,
                metadata={"source": "brave", "mock": True},
            ),
            SearchResult(
                source=self._get_source_type(),
                url="https://example.com/result2",
                title=f"Mock Brave Result 2 for: {query}",
                snippet=f"Another mock result demonstrating Brave search for: {query}",
                score=0.7,
                metadata={"source": "brave", "mock": True},
            ),
        ]

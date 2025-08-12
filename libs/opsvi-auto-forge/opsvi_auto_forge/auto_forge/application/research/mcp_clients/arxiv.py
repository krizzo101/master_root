"""ArXiv MCP client for research papers."""

import json
import logging
from contextlib import asynccontextmanager
from typing import List

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


class ArxivClient:
    """Real ArXiv MCP client for research papers."""

    def __init__(self, config=None):
        self.config = config or {}
        self.name = "arxiv"
        self.timeout = config.get("timeout", 30.0) if config else 30.0
        self.max_results = config.get("max_results", 10) if config else 10
        self.logger = logging.getLogger(__name__)

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        pass

    def _get_source_type(self) -> SourceType:
        """Get the source type for this client."""
        return SourceType.PAPER

    @asynccontextmanager
    async def _get_mcp_session(self):
        """Create and manage MCP session with ArXiv server."""
        if not MCP_AVAILABLE:
            raise ClientError("MCP Python SDK not available", self.name)

        # Server parameters for stdio connection
        server_params = StdioServerParameters(
            command="/home/opsvi/miniconda/bin/python",
            args=["-m", "arxiv_mcp_server"],
            env={},
        )

        try:
            async with stdio_client(server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    # Initialize the connection
                    await session.initialize()
                    self.logger.debug("ArXiv MCP session initialized successfully")
                    yield session
        except Exception as e:
            self.logger.error(f"Failed to establish ArXiv MCP session: {e}")
            raise ClientError(f"Failed to connect to ArXiv MCP server: {e}", self.name)

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
                    if isinstance(data, dict) and "papers" in data:
                        # ArXiv API response format
                        papers = data["papers"]
                        results = []
                        for paper in papers:
                            results.append(
                                SearchResult(
                                    source=self._get_source_type(),
                                    url=paper.get("url", ""),
                                    title=paper.get("title", ""),
                                    snippet=paper.get("summary", "")[:200],
                                    score=0.9,  # Default score for research papers
                                    metadata={
                                        "source": "arxiv",
                                        "authors": paper.get("authors", []),
                                        "paper_id": paper.get("id", ""),
                                        "categories": paper.get("categories", []),
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
                        title="ArXiv Search Results",
                        snippet=content.text,
                        score=0.5,
                        metadata={"source": "arxiv", "error": "non-json-response"},
                    )
                ]

        except Exception as e:
            self.logger.error(f"Error parsing ArXiv search results: {e}")

        return []

    async def search(self, query: str, **kwargs) -> List[SearchResult]:
        """Search using ArXiv MCP server."""
        if not MCP_AVAILABLE:
            # Fallback to mock implementation
            return self._mock_search(query, **kwargs)

        try:
            async with self._get_mcp_session() as session:
                # Call the ArXiv search tool
                result = await session.call_tool(
                    "mcp_research_papers_search_papers",
                    {
                        "query": query,
                        "max_results": min(
                            kwargs.get("max_results", self.max_results), 20
                        ),
                        "categories": kwargs.get("categories", ["cs.AI", "cs.LG"]),
                    },
                )

                return self._parse_search_results(result, query)

        except Exception as e:
            self.logger.error(f"ArXiv search failed: {e}")
            raise ClientError(f"ArXiv search failed: {e}", self.name)

    def _mock_search(self, query: str, **kwargs) -> List[SearchResult]:
        """Mock search implementation for testing."""
        return [
            SearchResult(
                source=self._get_source_type(),
                url="https://arxiv.org/abs/2024.12345",
                title=f"Mock ArXiv Paper 1: {query}",
                snippet=f"This is a mock research paper about {query} with comprehensive analysis and findings.",
                score=0.9,
                metadata={
                    "source": "arxiv",
                    "mock": True,
                    "authors": ["Mock Author 1", "Mock Author 2"],
                },
            ),
            SearchResult(
                source=self._get_source_type(),
                url="https://arxiv.org/abs/2024.67890",
                title=f"Mock ArXiv Paper 2: Advanced {query}",
                snippet=f"Another mock research paper demonstrating advanced techniques in {query}.",
                score=0.8,
                metadata={
                    "source": "arxiv",
                    "mock": True,
                    "authors": ["Mock Author 3"],
                },
            ),
        ]

#!/usr/bin/env python3
"""
Brave MCP Search - Python Web Search via Model Context Protocol

A Python script that leverages the Model Context Protocol (MCP) and Brave MCP server
to perform web searches using the Brave Search API.

## Setup Instructions

### 1. Prerequisites
- Python 3.8+
- Node.js and npm (required for Brave MCP server)
- Brave Search API key (get free key at https://brave.com/search/api/)

### 2. Installation
```bash
# Install Python dependencies
pip install "mcp[cli]" asyncio-subprocess

# Install Brave MCP server (Node.js)
npm install -g brave-search-mcp
```

### 3. Configuration
Set your Brave API key as an environment variable:
```bash
export BRAVE_API_KEY="your_api_key_here"
```

Or create a .env file:
```
BRAVE_API_KEY=your_api_key_here
```

### 4. Usage
```python
# Direct usage
from brave_mcp_search import BraveMCPSearch

async def main():
    searcher = BraveMCPSearch()
    results = await searcher.search("Python programming tutorial")
    print(results)

# Command line usage
python brave_mcp_search.py "search query here"
```

## API Reference

### BraveMCPSearch Class
- `search(query, count=10, freshness=None)`: Perform web search
- `image_search(query, count=1)`: Search for images
- `news_search(query, count=10, freshness=None)`: Search for news
- `video_search(query, count=10, freshness=None)`: Search for videos
- `local_search(query, count=5)`: Search for local businesses (Pro plan required)

### Error Handling
- `BraveMCPError`: Base exception for all Brave MCP related errors
- `ServerNotFoundError`: Brave MCP server not installed or not in PATH
- `AuthenticationError`: Invalid or missing API key
- `ConnectionError`: Network or communication issues
"""

import asyncio
import json
import logging
import os
import subprocess
import sys
from contextlib import asynccontextmanager
from dataclasses import dataclass
from pathlib import Path

# MCP imports
try:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    from mcp.types import CallToolResult, TextContent
except ImportError:
    print("Error: MCP Python SDK not installed. Please run: pip install 'mcp[cli]'")
    sys.exit(1)


# Custom exceptions
class BraveMCPError(Exception):
    """Base exception for Brave MCP related errors."""

    pass


class ServerNotFoundError(BraveMCPError):
    """Raised when Brave MCP server is not found or not installed."""

    pass


class AuthenticationError(BraveMCPError):
    """Raised when API key is invalid or missing."""

    pass


class ConnectionError(BraveMCPError):
    """Raised when connection to MCP server fails."""

    pass


@dataclass
class SearchResult:
    """Represents a single search result."""

    title: str
    url: str
    description: str

    def __str__(self) -> str:
        return f"{self.title}\n{self.url}\n{self.description}\n"


@dataclass
class SearchResponse:
    """Represents a collection of search results."""

    query: str
    results: list[SearchResult]
    total_results: int

    def __str__(self) -> str:
        output = [f"Search results for: {self.query}"]
        output.append(f"Total results: {self.total_results}")
        output.append("-" * 50)

        for i, result in enumerate(self.results, 1):
            output.append(f"{i}. {result}")

        return "\n".join(output)


class BraveMCPSearch:
    """
    A Python client for performing web searches via the Brave MCP server.

    This class provides a high-level interface to interact with the Brave Search API
    through the Model Context Protocol (MCP).
    """

    def __init__(
        self,
        api_key: str | None = None,
        debug: bool = False,
        mcp_config_path: str | None = None,
    ):
        """
        Initialize the Brave MCP Search client.

        Args:
            api_key: Brave Search API key. If None, will try to read from mcp.json or BRAVE_API_KEY env var.
            debug: Enable debug logging.
            mcp_config_path: Path to mcp.json config file. Defaults to .cursor/mcp.json.
        """
        self.debug = debug
        self.mcp_config_path = mcp_config_path or ".cursor/mcp.json"

        # Setup logging
        logging.basicConfig(
            level=logging.DEBUG if debug else logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )
        self.logger = logging.getLogger(__name__)

        # Get API key from various sources
        self.api_key = (
            api_key or self._get_api_key_from_config() or os.getenv("BRAVE_API_KEY")
        )

        if not self.api_key:
            raise AuthenticationError(
                "Brave API key not provided. Please:\n"
                "1. Pass api_key parameter, or\n"
                "2. Set BRAVE_API_KEY environment variable, or\n"
                "3. Configure it in mcp.json under mcpServers.web_search.env.BRAVE_API_KEY"
            )

    def _get_api_key_from_config(self) -> str | None:
        """
        Attempt to read the Brave API key from mcp.json configuration file.

        Returns:
            API key if found in config file, None otherwise.
        """
        try:
            config_path = Path(self.mcp_config_path)
            if not config_path.exists():
                self.logger.debug(f"MCP config file not found at {config_path}")
                return None

            with open(config_path) as f:
                config = json.load(f)

            # Navigate to the mcp_web_search server configuration
            web_search_config = config.get("mcpServers", {}).get("mcp_web_search", {})
            api_key = web_search_config.get("env", {}).get("BRAVE_API_KEY")

            if api_key:
                self.logger.debug(f"Found Brave API key in MCP config at {config_path}")
                return api_key
            else:
                self.logger.debug("Brave API key not found in MCP config")
                return None

        except (json.JSONDecodeError, FileNotFoundError, KeyError) as e:
            self.logger.debug(f"Error reading MCP config: {e}")
            return None

    def _check_brave_server_installed(self) -> bool:
        """Check if Brave MCP server is installed and accessible."""
        # MCP servers use stdio transport and don't support --help
        # We'll assume it's installed and let the connection attempt catch any issues
        return True

    def _ensure_brave_server(self) -> None:
        """Ensure Brave MCP server is installed."""
        if not self._check_brave_server_installed():
            self.logger.info("Brave MCP server not found, attempting to install...")
            try:
                subprocess.run(
                    ["npm", "install", "-g", "brave-search-mcp"],
                    check=True,
                    capture_output=True,
                    text=True,
                )
                self.logger.info("Brave MCP server installed successfully")
            except subprocess.CalledProcessError as e:
                raise ServerNotFoundError(
                    f"Failed to install Brave MCP server. Please install manually:\n"
                    f"npm install -g brave-search-mcp\n"
                    f"Error: {e.stderr}"
                )

    @asynccontextmanager
    async def _get_mcp_session(self):
        """Create and manage MCP session with Brave server."""
        self._ensure_brave_server()

        # Server parameters for stdio connection
        server_params = StdioServerParameters(
            command="npx",
            args=["-y", "brave-search-mcp"],
            env={**os.environ, "BRAVE_API_KEY": self.api_key},
        )

        try:
            async with stdio_client(server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    # Initialize the connection
                    await session.initialize()
                    self.logger.debug("MCP session initialized successfully")
                    yield session
        except Exception as e:
            self.logger.error(f"Failed to establish MCP session: {e}")
            raise ConnectionError(f"Failed to connect to Brave MCP server: {e}")

    def _parse_search_results(
        self, tool_result: CallToolResult, query: str
    ) -> SearchResponse:
        """Parse MCP tool result into SearchResponse object."""
        try:
            # Extract content from MCP result
            if not tool_result.content:
                return SearchResponse(query=query, results=[], total_results=0)

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
                                    title=item.get("title", ""),
                                    url=item.get("url", ""),
                                    description=item.get("description", ""),
                                )
                            )
                        return SearchResponse(
                            query=query, results=results, total_results=len(results)
                        )
                except json.JSONDecodeError:
                    # If not JSON, treat as plain text
                    pass

                # Fallback: treat as plain text
                results = [
                    SearchResult(
                        title="Search Results", url="", description=content.text
                    )
                ]
                return SearchResponse(query=query, results=results, total_results=1)

        except Exception as e:
            self.logger.error(f"Error parsing search results: {e}")

        return SearchResponse(query=query, results=[], total_results=0)

    async def search(
        self, query: str, count: int = 10, freshness: str | None = None
    ) -> SearchResponse:
        """
        Perform a web search using Brave Search API.

        Args:
            query: Search query string
            count: Number of results to return (max 20, default 10)
            freshness: Filter by discovery time:
                - "pd": Past day
                - "pw": Past week
                - "pm": Past month
                - "py": Past year
                - "YYYY-MM-DDtoYYYY-MM-DD": Custom date range

        Returns:
            SearchResponse object containing results

        Raises:
            BraveMCPError: If search fails
        """
        if not query.strip():
            raise ValueError("Search query cannot be empty")

        if count > 20:
            count = 20
            self.logger.warning("Count limited to maximum of 20 results")

        arguments = {"query": query, "count": count}

        if freshness:
            arguments["freshness"] = freshness

        self.logger.info(f"Performing web search: '{query}' (count={count})")

        async with self._get_mcp_session() as session:
            try:
                result = await session.call_tool("brave_web_search", arguments)
                return self._parse_search_results(result, query)
            except Exception as e:
                self.logger.error(f"Web search failed: {e}")
                raise BraveMCPError(f"Search failed: {e}")

    async def image_search(self, query: str, count: int = 1) -> SearchResponse:
        """
        Search for images using Brave Search API.

        Args:
            query: Search query string
            count: Number of images to return (max 3, default 1)

        Returns:
            SearchResponse object containing image results
        """
        if count > 3:
            count = 3
            self.logger.warning("Image count limited to maximum of 3 results")

        arguments = {"query": query, "count": count}

        self.logger.info(f"Performing image search: '{query}' (count={count})")

        async with self._get_mcp_session() as session:
            try:
                result = await session.call_tool("brave_image_search", arguments)
                return self._parse_search_results(result, query)
            except Exception as e:
                self.logger.error(f"Image search failed: {e}")
                raise BraveMCPError(f"Image search failed: {e}")

    async def news_search(
        self, query: str, count: int = 10, freshness: str | None = None
    ) -> SearchResponse:
        """
        Search for news articles using Brave Search API.

        Args:
            query: Search query string
            count: Number of results to return (max 20, default 10)
            freshness: Filter by discovery time (same options as web search)

        Returns:
            SearchResponse object containing news results
        """
        if count > 20:
            count = 20
            self.logger.warning("News count limited to maximum of 20 results")

        arguments = {"query": query, "count": count}

        if freshness:
            arguments["freshness"] = freshness

        self.logger.info(f"Performing news search: '{query}' (count={count})")

        async with self._get_mcp_session() as session:
            try:
                result = await session.call_tool("brave_news_search", arguments)
                return self._parse_search_results(result, query)
            except Exception as e:
                self.logger.error(f"News search failed: {e}")
                raise BraveMCPError(f"News search failed: {e}")

    async def video_search(
        self, query: str, count: int = 10, freshness: str | None = None
    ) -> SearchResponse:
        """
        Search for videos using Brave Search API.

        Args:
            query: Search query string
            count: Number of results to return (max 20, default 10)
            freshness: Filter by discovery time (same options as web search)

        Returns:
            SearchResponse object containing video results
        """
        if count > 20:
            count = 20
            self.logger.warning("Video count limited to maximum of 20 results")

        arguments = {"query": query, "count": count}

        if freshness:
            arguments["freshness"] = freshness

        self.logger.info(f"Performing video search: '{query}' (count={count})")

        async with self._get_mcp_session() as session:
            try:
                result = await session.call_tool("brave_video_search", arguments)
                return self._parse_search_results(result, query)
            except Exception as e:
                self.logger.error(f"Video search failed: {e}")
                raise BraveMCPError(f"Video search failed: {e}")

    async def local_search(self, query: str, count: int = 5) -> SearchResponse:
        """
        Search for local businesses and points of interest.

        Note: Requires Brave Search Pro API plan for location results.
        Falls back to web search if no location results found.

        Args:
            query: Local search query string
            count: Number of results to return (max 20, default 5)

        Returns:
            SearchResponse object containing local results
        """
        if count > 20:
            count = 20
            self.logger.warning("Local count limited to maximum of 20 results")

        arguments = {"query": query, "count": count}

        self.logger.info(f"Performing local search: '{query}' (count={count})")

        async with self._get_mcp_session() as session:
            try:
                result = await session.call_tool("brave_local_search", arguments)
                return self._parse_search_results(result, query)
            except Exception as e:
                self.logger.error(f"Local search failed: {e}")
                raise BraveMCPError(f"Local search failed: {e}")


# Utility functions
async def quick_search(
    query: str,
    search_type: str = "web",
    mcp_config_path: str | None = None,
    **kwargs,
) -> SearchResponse:
    """
    Quick search utility function.

    Args:
        query: Search query
        search_type: Type of search ("web", "image", "news", "video", "local")
        mcp_config_path: Path to mcp.json config file. Defaults to .cursor/mcp.json.
        **kwargs: Additional arguments passed to search method

    Returns:
        SearchResponse object
    """
    searcher = BraveMCPSearch(mcp_config_path=mcp_config_path)

    if search_type == "web":
        return await searcher.search(query, **kwargs)
    elif search_type == "image":
        return await searcher.image_search(query, **kwargs)
    elif search_type == "news":
        return await searcher.news_search(query, **kwargs)
    elif search_type == "video":
        return await searcher.video_search(query, **kwargs)
    elif search_type == "local":
        return await searcher.local_search(query, **kwargs)
    else:
        raise ValueError(f"Unknown search type: {search_type}")


# Command line interface
async def main():
    """Command line interface for Brave MCP Search."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Perform web searches using Brave MCP Server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python brave_mcp_search.py "Python programming tutorial"
  python brave_mcp_search.py "Python tutorial" --type news --count 5
  python brave_mcp_search.py "cat pictures" --type image --count 3
  python brave_mcp_search.py "restaurants near me" --type local
        """,
    )

    parser.add_argument("query", help="Search query string")
    parser.add_argument(
        "--type",
        "-t",
        choices=["web", "image", "news", "video", "local"],
        default="web",
        help="Type of search to perform (default: web)",
    )
    parser.add_argument(
        "--count",
        "-c",
        type=int,
        default=10,
        help="Number of results to return (default: 10)",
    )
    parser.add_argument(
        "--freshness",
        "-f",
        choices=["pd", "pw", "pm", "py"],
        help="Filter by freshness: pd (past day), pw (past week), pm (past month), py (past year)",
    )
    parser.add_argument(
        "--debug", "-d", action="store_true", help="Enable debug logging"
    )
    parser.add_argument(
        "--api-key", help="Brave Search API key (overrides BRAVE_API_KEY env var)"
    )

    args = parser.parse_args()

    try:
        # Perform search
        kwargs = {"count": args.count}
        if args.freshness and args.type in ["web", "news", "video"]:
            kwargs["freshness"] = args.freshness

        searcher = BraveMCPSearch(api_key=args.api_key, debug=args.debug)

        if args.type == "web":
            results = await searcher.search(args.query, **kwargs)
        elif args.type == "image":
            results = await searcher.image_search(args.query, **kwargs)
        elif args.type == "news":
            results = await searcher.news_search(args.query, **kwargs)
        elif args.type == "video":
            results = await searcher.video_search(args.query, **kwargs)
        elif args.type == "local":
            results = await searcher.local_search(args.query, **kwargs)

        print(results)

    except KeyboardInterrupt:
        print("\nSearch interrupted by user")
        sys.exit(1)
    except BraveMCPError as e:
        print(f"Search error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

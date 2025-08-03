#!/usr/bin/env python3
"""
Context7 MCP Client - Technical Documentation Access via MCP

This script provides a Python interface to the Context7 MCP server for accessing
up-to-date technical documentation for libraries and frameworks.

## Official Documentation

- Context7 MCP Server: https://github.com/upstash/context7-mcp
- Context7 Platform: https://context7.upstash.com/
- Upstash Documentation: https://upstash.com/docs

## Prerequisites

```bash
# Install MCP Python SDK
pip install "mcp[cli]"

# Install Context7 MCP server
npm install -g @upstash/context7-mcp
```

## Configuration

Add to mcp.json:
```json
{
  "mcpServers": {
    "tech_docs": {
      "command": "npx",
      "args": ["-y", "@upstash/context7-mcp"]
    }
  }
}
```

## Features

- **Library Resolution**: Convert library names to Context7-compatible IDs
- **Documentation Retrieval**: Get current documentation for specific libraries
- **Topic Filtering**: Focus on specific topics within documentation
- **Token Management**: Control documentation size with token limits
- **Version Support**: Access documentation for specific library versions
"""

import asyncio
from contextlib import asynccontextmanager
from dataclasses import dataclass
import json
import logging
import os
from pathlib import Path
import sys
from typing import List, Optional

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
class Context7Error(Exception):
    """Base exception for Context7-related errors."""

    pass


@dataclass
class LibraryInfo:
    """Information about a library in Context7."""

    library_id: str
    name: str
    description: str
    trust_score: int = 0


@dataclass
class DocumentationResult:
    """Result from documentation retrieval."""

    library_id: str
    topic: str
    content: str
    token_count: int
    success: bool = True
    error: str = ""

    def __str__(self) -> str:
        return f"Documentation for {self.library_id} - {self.token_count} tokens"


class Context7MCPClient:
    """Client for interacting with the Context7 MCP server."""

    def __init__(self, mcp_config_path: Optional[str] = None, debug: bool = False):
        """
        Initialize the Context7 MCP client.

        Args:
            mcp_config_path: Path to MCP configuration file
            debug: Enable debug logging
        """
        self.logger = logging.getLogger(__name__)
        if debug:
            self.logger.setLevel(logging.DEBUG)

        # Default MCP config path
        if mcp_config_path is None:
            # Try to find mcp.json in common locations
            possible_paths = [
                Path.home() / ".cursor" / "mcp.json",
                Path.cwd() / "mcp.json",
                Path.cwd() / ".cursor" / "mcp.json",
            ]

            for path in possible_paths:
                if path.exists():
                    mcp_config_path = str(path)
                    break
            else:
                # Use default location
                mcp_config_path = str(Path.home() / ".cursor" / "mcp.json")

        self.mcp_config_path = mcp_config_path
        self.logger.debug(f"Using MCP config: {mcp_config_path}")

    @asynccontextmanager
    async def _get_session(self):
        """Get an MCP client session."""
        try:
            # Load MCP configuration
            if not os.path.exists(self.mcp_config_path):
                raise Context7Error(f"MCP config not found: {self.mcp_config_path}")

            with open(self.mcp_config_path, "r") as f:
                config = json.load(f)

            # Find Context7 server configuration
            servers = config.get("mcpServers", {})
            context7_config = None

            # Look for tech_docs first (as configured in .cursor/mcp.json)
            if "tech_docs" in servers:
                context7_config = servers["tech_docs"]
            elif "context7" in servers:
                context7_config = servers["context7"]
            else:
                # Fallback to other possible names
                for server_name, server_config in servers.items():
                    if (
                        "context7" in server_name.lower()
                        or "tech_docs" in server_name.lower()
                    ):
                        context7_config = server_config
                        break

            if not context7_config:
                # Try to find any server that might be Context7
                for server_name, server_config in servers.items():
                    if isinstance(server_config, dict) and "command" in server_config:
                        if "context7" in str(
                            server_config
                        ).lower() or "npx" in server_config.get("command", ""):
                            context7_config = server_config
                            break

            if not context7_config:
                raise Context7Error("Context7 MCP server not found in configuration")

            # Create server parameters
            server_params = StdioServerParameters(
                command=context7_config.get("command", "npx"),
                args=context7_config.get("args", ["-y", "@upstash/context7-mcp"]),
                env=context7_config.get("env", {}),
            )

            # Create client session
            async with stdio_client(server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    yield session

        except Exception as exc:
            self.logger.error(f"Failed to create MCP session: {exc}")
            raise Context7Error(f"MCP session creation failed: {exc}") from exc

    def _parse_library_results(self, tool_result: CallToolResult) -> List[LibraryInfo]:
        """Parse library resolution results from MCP tool response."""
        try:
            if not tool_result.content:
                return []

            # Extract content from tool result
            content = ""
            for item in tool_result.content:
                if isinstance(item, TextContent):
                    content += item.text

            # Parse the response
            lines = content.strip().split("\n")
            libraries = []

            current_library = {}
            for line in lines:
                line = line.strip()
                if not line:
                    continue

                if line.startswith("- Title:"):
                    if current_library:
                        libraries.append(LibraryInfo(**current_library))
                    current_library = {}
                    current_library["name"] = line.replace("- Title:", "").strip()
                elif line.startswith("- Context7-compatible library ID:"):
                    current_library["library_id"] = line.replace(
                        "- Context7-compatible library ID:", ""
                    ).strip()
                elif line.startswith("- Description:"):
                    current_library["description"] = line.replace(
                        "- Description:", ""
                    ).strip()
                elif line.startswith("- Trust Score:"):
                    try:
                        current_library["trust_score"] = int(
                            line.replace("- Trust Score:", "").strip()
                        )
                    except ValueError:
                        current_library["trust_score"] = 0

            # Add the last library
            if current_library:
                libraries.append(LibraryInfo(**current_library))

            return libraries

        except Exception as exc:
            self.logger.error(f"Failed to parse library results: {exc}")
            return []

    async def resolve_library_id(self, library_name: str) -> List[LibraryInfo]:
        """
        Resolve a library name to Context7-compatible library IDs.

        Args:
            library_name: Name of the library to resolve

        Returns:
            List of library information
        """
        try:
            async with self._get_session() as session:
                # Call the resolve-library-id tool
                result = await session.call_tool(
                    "resolve-library-id", {"libraryName": library_name}
                )

                if result.is_error:
                    raise Context7Error(f"Tool call failed: {result.error}")

                return self._parse_library_results(result)

        except Exception as exc:
            self.logger.error(f"Library resolution failed: {exc}")
            raise Context7Error(f"Library resolution failed: {exc}") from exc

    async def get_library_docs(
        self, library_id: str, topic: str = None, tokens: int = 10000
    ) -> DocumentationResult:
        """
        Get documentation for a specific library.

        Args:
            library_id: Context7-compatible library ID
            topic: Optional topic to focus on
            tokens: Maximum tokens to retrieve

        Returns:
            Documentation result
        """
        try:
            async with self._get_session() as session:
                # Prepare arguments
                args = {"context7CompatibleLibraryID": library_id, "tokens": tokens}
                if topic:
                    args["topic"] = topic

                # Call the get-library-docs tool
                result = await session.call_tool("get-library-docs", args)

                if result.is_error:
                    return DocumentationResult(
                        library_id=library_id,
                        topic=topic or "",
                        content="",
                        token_count=0,
                        success=False,
                        error=str(result.error),
                    )

                # Extract content
                content = ""
                for item in result.content:
                    if isinstance(item, TextContent):
                        content += item.text

                return DocumentationResult(
                    library_id=library_id,
                    topic=topic or "",
                    content=content,
                    token_count=len(content.split()),
                    success=True,
                )

        except Exception as exc:
            self.logger.error(f"Documentation retrieval failed: {exc}")
            return DocumentationResult(
                library_id=library_id,
                topic=topic or "",
                content="",
                token_count=0,
                success=False,
                error=str(exc),
            )

    async def search_and_get_docs(
        self,
        library_name: str,
        topic: str = None,
        tokens: int = 10000,
        select_best: bool = True,
    ) -> DocumentationResult:
        """
        Search for a library and get its documentation in one step.

        Args:
            library_name: Name of the library to search for
            topic: Optional topic to focus on
            tokens: Maximum tokens to retrieve
            select_best: Whether to select the best match automatically

        Returns:
            Documentation result
        """
        try:
            # First, resolve the library
            libraries = await self.resolve_library_id(library_name)

            if not libraries:
                return DocumentationResult(
                    library_id="",
                    topic=topic or "",
                    content=f"No libraries found for '{library_name}'",
                    token_count=0,
                    success=False,
                    error="No libraries found",
                )

            # Select the best library if requested
            if select_best and len(libraries) > 1:
                # Sort by trust score and select the best
                libraries.sort(key=lambda x: x.trust_score, reverse=True)
                selected_library = libraries[0]
            else:
                selected_library = libraries[0]

            # Get documentation for the selected library
            return await self.get_library_docs(
                library_id=selected_library.library_id, topic=topic, tokens=tokens
            )

        except Exception as exc:
            self.logger.error(f"Search and get docs failed: {exc}")
            return DocumentationResult(
                library_id="",
                topic=topic or "",
                content="",
                token_count=0,
                success=False,
                error=str(exc),
            )

    async def get_implementation_guidance(
        self, library_name: str, feature: str, tokens: int = 5000
    ) -> str:
        """
        Get implementation guidance for a specific library feature.

        Args:
            library_name: Name of the library
            feature: Specific feature to get guidance for
            tokens: Maximum tokens to retrieve

        Returns:
            Implementation guidance text
        """
        try:
            result = await self.search_and_get_docs(
                library_name=library_name,
                topic=feature,
                tokens=tokens,
                select_best=True,
            )

            if result.success:
                return result.content
            else:
                return f"Failed to get implementation guidance: {result.error}"

        except Exception as exc:
            self.logger.error(f"Implementation guidance failed: {exc}")
            return f"Error getting implementation guidance: {exc}"


# Convenience functions for quick access
async def quick_docs(library_name: str, topic: str = None, tokens: int = 10000) -> str:
    """Quick access to library documentation."""
    client = Context7MCPClient()
    result = await client.search_and_get_docs(library_name, topic, tokens)
    return result.content if result.success else f"Error: {result.error}"


async def quick_resolve(library_name: str) -> List[LibraryInfo]:
    """Quick library resolution."""
    client = Context7MCPClient()
    return await client.resolve_library_id(library_name)


# Example usage and testing
async def main():
    """Example usage of the Context7 MCP client."""
    client = Context7MCPClient(debug=True)

    # Example 1: Resolve a library
    print("=== Library Resolution ===")
    libraries = await client.resolve_library_id("openai")
    for lib in libraries[:3]:  # Show first 3 results
        print(f"- {lib.name}: {lib.description[:100]}...")

    # Example 2: Get documentation
    print("\n=== Documentation Retrieval ===")
    if libraries:
        doc = await client.get_library_docs(
            library_id=libraries[0].library_id, topic="authentication", tokens=2000
        )
        print(f"Documentation: {doc.content[:200]}...")

    # Example 3: Search and get docs
    print("\n=== Search and Get Docs ===")
    result = await client.search_and_get_docs("react", topic="hooks", tokens=1000)
    print(f"Result: {result.content[:200]}...")


if __name__ == "__main__":
    asyncio.run(main())

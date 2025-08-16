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
import json
import logging
import os
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
    """
    Client for interacting with Context7 MCP server.

    This client provides high-level methods for resolving library IDs and
    retrieving up-to-date technical documentation.
    """

    def __init__(self, mcp_config_path: str | None = None, debug: bool = False):
        """
        Initialize the Context7 MCP client.

        Args:
            mcp_config_path: Path to mcp.json config file
            debug: Enable debug logging
        """
        # Prefer absolute config path if available
        abs_config = "/home/opsvi/agent_world/.cursor/mcp.json"
        if mcp_config_path is None and os.path.exists(abs_config):
            self.mcp_config_path = abs_config
        else:
            self.mcp_config_path = mcp_config_path or ".cursor/mcp.json"
        # Enable debug logging by default for troubleshooting
        self.debug = True if debug or True else False

        # Setup logging
        logging.basicConfig(
            level=logging.DEBUG,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )
        self.logger = logging.getLogger(__name__)

    @asynccontextmanager
    async def _get_session(self):
        """Create and manage an MCP session with Context7 server."""
        # Load server configuration
        config_path = Path(self.mcp_config_path)
        if not config_path.exists():
            raise FileNotFoundError(f"MCP config file not found: {config_path}")

        with open(config_path) as f:
            config = json.load(f)

        context7_config = config.get("mcpServers", {}).get("tech_docs", {})
        if not context7_config:
            raise ValueError("tech_docs server not found in MCP configuration")

        # Server parameters for stdio connection
        server_params = StdioServerParameters(
            command=context7_config.get("command", "npx"),
            args=context7_config.get("args", ["-y", "@upstash/context7-mcp"]),
            env={**os.environ, **context7_config.get("env", {})},
        )

        try:
            async with stdio_client(server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    self.logger.debug("Context7 MCP session initialized")
                    # List and log all available tools
                    try:
                        tools = await session.list_tools()
                        self.logger.info(f"[DEBUG] Available MCP tools: {tools}")
                        print(f"[DEBUG] Available MCP tools: {tools}")
                    except Exception as tool_list_e:
                        self.logger.error(
                            f"[DEBUG] Failed to list tools: {tool_list_e}"
                        )
                    yield session
        except Exception as e:
            import traceback

            self.logger.error(f"Failed to establish MCP session: {e}")
            self.logger.error(traceback.format_exc())
            # Attempt to print subprocess output if available
            if hasattr(e, "stderr"):
                self.logger.error(f"Subprocess stderr: {e.stderr}")
            if hasattr(e, "stdout"):
                self.logger.error(f"Subprocess stdout: {e.stdout}")
            raise Context7Error(f"Failed to connect to Context7 MCP server: {e}")

    def _parse_library_results(self, tool_result: CallToolResult) -> list[LibraryInfo]:
        """Parse library resolution results."""
        libraries = []

        try:
            import pprint

            self.logger.debug(
                f"[DEBUG] Raw tool_result: {pprint.pformat(tool_result.__dict__ if hasattr(tool_result, '__dict__') else str(tool_result))}"
            )
            print(f"[DEBUG] Raw tool_result: {tool_result}")
            if not tool_result.content:
                return libraries

            content = tool_result.content[0]
            if isinstance(content, TextContent):
                try:
                    self.logger.debug(f"[DEBUG] Raw content.text: {content.text}")
                    print(f"[DEBUG] Raw content.text: {content.text}")
                    data = json.loads(content.text)

                    # Handle different response formats
                    library_list = (
                        data if isinstance(data, list) else data.get("libraries", [])
                    )

                    self.logger.debug(f"[DEBUG] Parsed library_list: {library_list}")
                    print(f"[DEBUG] Parsed library_list: {library_list}")

                    for lib_data in library_list:
                        libraries.append(
                            LibraryInfo(
                                library_id=lib_data.get("id", ""),
                                name=lib_data.get("name", ""),
                                description=lib_data.get("description", ""),
                                trust_score=lib_data.get("trust_score", 0),
                            )
                        )
                except json.JSONDecodeError:
                    # Use LLM to extract libraries from raw text
                    try:
                        agent_prompt = f"""
You are an expert at extracting structured data from technical documentation search results.

Given the following text listing libraries (with name, Context7-compatible ID, description, and trust score), extract a JSON array of objects with the following schema:

[
  {{
    "name": string,           // The library or package name
    "id": string,             // The Context7-compatible library ID
    "description": string,    // Short summary of the library
    "trust_score": number     // Authority indicator (integer or float)
  }},
  ...
]

Text:
{content.text}

Return ONLY the JSON array, with no extra text or explanation.
"""
                        # Use OpenAI or AsyncOpenAI as in the rest of the codebase
                        from openai import OpenAI

                        client = OpenAI()
                        response = client.chat.completions.create(
                            model="gpt-4.1-mini",
                            messages=[
                                {
                                    "role": "system",
                                    "content": "You are a precise assistant that returns only valid JSON arrays of libraries.",
                                },
                                {"role": "user", "content": agent_prompt},
                            ],
                            response_format={"type": "json_object"},
                            temperature=0.1,
                        )
                        import json as _json

                        llm_content = response.choices[0].message.content
                        self.logger.debug(
                            f"[DEBUG] LLM-extracted library JSON: {llm_content}"
                        )
                        print(f"[DEBUG] LLM-extracted library JSON: {llm_content}")
                        # Post-process: extract first valid JSON array if extra text is present
                        import re

                        match = re.search(r"(\[.*?\])", llm_content, re.DOTALL)
                        if match:
                            llm_content = match.group(1)
                        parsed = _json.loads(llm_content)
                        if not isinstance(parsed, list):
                            self.logger.error(
                                f"LLM output is not a list: {type(parsed)}"
                            )
                            print(f"[DEBUG] LLM output is not a list: {type(parsed)}")
                            parsed = []
                        for lib_data in parsed:
                            if isinstance(lib_data, dict):
                                libraries.append(
                                    LibraryInfo(
                                        library_id=lib_data.get("id", ""),
                                        name=lib_data.get("name", ""),
                                        description=lib_data.get("description", ""),
                                        trust_score=lib_data.get("trust_score", 0),
                                    )
                                )
                    except Exception as agent_e:
                        self.logger.error(f"LLM extraction failed: {agent_e}")
                        # Fallback: Try old text parser
                        lines = content.text.strip().split("\n")
                        for line in lines:
                            if line.strip():
                                parts = line.split(" - ")
                                if len(parts) >= 2:
                                    libraries.append(
                                        LibraryInfo(
                                            library_id=parts[0].strip(),
                                            name=(
                                                parts[1].strip()
                                                if len(parts) > 1
                                                else ""
                                            ),
                                            description=(
                                                parts[2].strip()
                                                if len(parts) > 2
                                                else ""
                                            ),
                                            trust_score=0,
                                        )
                                    )
        except Exception as e:
            self.logger.error(f"Error parsing library results: {e}")

        return libraries

    async def resolve_library_id(self, library_name: str) -> list[LibraryInfo]:
        """
        Resolve a library name to Context7-compatible library IDs.

        Args:
            library_name: Name of the library to search for

        Returns:
            List[LibraryInfo]: List of matching libraries with metadata

        Examples:
            # Find React documentation
            libraries = await client.resolve_library_id("react")

            # Find Express.js documentation
            libraries = await client.resolve_library_id("express")
        """
        if not library_name.strip():
            raise ValueError("Library name cannot be empty")

        arguments = {"libraryName": library_name}
        self.logger.info(f"Resolving library ID for: {library_name}")

        async with self._get_session() as session:
            try:
                result = await session.call_tool("resolve-library-id", arguments)
                return self._parse_library_results(result)
            except Exception as e:
                self.logger.error(f"Library ID resolution failed: {e}")
                raise Context7Error(f"Failed to resolve library ID: {e}")

    async def get_library_docs(
        self, library_id: str, topic: str = None, tokens: int = 10000
    ) -> DocumentationResult:
        """
        Retrieve documentation for a specific library.

        Args:
            library_id: Context7-compatible library ID (from resolve_library_id)
            topic: Specific topic to focus on (optional)
            tokens: Maximum number of tokens to retrieve (default: 10000)

        Returns:
            DocumentationResult: Documentation content and metadata

        Examples:
            # Get React documentation
            docs = await client.get_library_docs("/vercel/next.js")

            # Get specific React hooks documentation
            docs = await client.get_library_docs("/vercel/next.js", topic="hooks", tokens=5000)
        """
        if not library_id.strip():
            raise ValueError("Library ID cannot be empty")

        arguments = {"context7CompatibleLibraryID": library_id, "tokens": tokens}

        if topic:
            arguments["topic"] = topic

        self.logger.info(f"Retrieving documentation for: {library_id}")
        if topic:
            self.logger.info(f"Focused on topic: {topic}")

        async with self._get_session() as session:
            try:
                result = await session.call_tool("get-library-docs", arguments)

                if result.content:
                    content = result.content[0]
                    if isinstance(content, TextContent):
                        return DocumentationResult(
                            library_id=library_id,
                            topic=topic or "general",
                            content=content.text,
                            token_count=len(content.text.split()),  # Rough token count
                            success=True,
                        )

                return DocumentationResult(
                    library_id=library_id,
                    topic=topic or "general",
                    content="",
                    token_count=0,
                    success=False,
                    error="No documentation content received",
                )

            except Exception as e:
                self.logger.error(f"Documentation retrieval failed: {e}")
                return DocumentationResult(
                    library_id=library_id,
                    topic=topic or "general",
                    content="",
                    token_count=0,
                    success=False,
                    error=str(e),
                )

    async def search_and_get_docs(
        self,
        library_name: str,
        topic: str = None,
        tokens: int = 10000,
        select_best: bool = True,
    ) -> DocumentationResult:
        """
        Search for a library and retrieve its documentation in one call.

        Args:
            library_name: Name of the library to search for
            topic: Specific topic to focus on (optional)
            tokens: Maximum number of tokens to retrieve
            select_best: Automatically select the best matching library

        Returns:
            DocumentationResult: Documentation content and metadata
        """
        # First, resolve the library ID
        libraries = await self.resolve_library_id(library_name)

        if not libraries:
            return DocumentationResult(
                library_id="",
                topic=topic or "general",
                content="",
                token_count=0,
                success=False,
                error=f"No libraries found for '{library_name}'",
            )

        # Select the best library (highest trust score, most code snippets)
        if select_best:
            best_library = max(
                libraries, key=lambda x: (x.trust_score, x.code_snippets)
            )
            selected_library = best_library
        else:
            # Use the first result
            selected_library = libraries[0]

        self.logger.info(
            f"Selected library: {selected_library.name} ({selected_library.library_id})"
        )

        # Get documentation for the selected library
        return await self.get_library_docs(selected_library.library_id, topic, tokens)

    async def get_implementation_guidance(
        self, library_name: str, feature: str, tokens: int = 5000
    ) -> str:
        """
        Get specific implementation guidance for a library feature.

        Args:
            library_name: Name of the library
            feature: Specific feature or functionality to implement
            tokens: Maximum tokens for the response

        Returns:
            str: Implementation guidance and examples
        """
        docs_result = await self.search_and_get_docs(
            library_name, topic=feature, tokens=tokens
        )

        if docs_result.success:
            return docs_result.content
        else:
            return f"Error retrieving guidance for {library_name} {feature}: {docs_result.error}"


# Utility functions
async def quick_docs(library_name: str, topic: str = None, tokens: int = 10000) -> str:
    """Quick documentation retrieval."""
    client = Context7MCPClient()
    result = await client.search_and_get_docs(library_name, topic, tokens)
    return result.content if result.success else f"Error: {result.error}"


async def quick_resolve(library_name: str) -> list[LibraryInfo]:
    """Quick library ID resolution."""
    client = Context7MCPClient()
    return await client.resolve_library_id(library_name)


# Common library shortcuts
POPULAR_LIBRARIES = {
    "react": "React JavaScript library",
    "nextjs": "Next.js React framework",
    "express": "Express.js Node.js framework",
    "fastapi": "FastAPI Python framework",
    "django": "Django Python framework",
    "flask": "Flask Python framework",
    "vue": "Vue.js JavaScript framework",
    "angular": "Angular TypeScript framework",
    "typescript": "TypeScript language",
    "tailwind": "Tailwind CSS framework",
    "prisma": "Prisma database toolkit",
    "mongodb": "MongoDB database",
    "postgresql": "PostgreSQL database",
    "redis": "Redis data store",
}


# Command line interface
async def main():
    """Command line interface for Context7 MCP client."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Context7 MCP Client - Technical Documentation Access",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Examples:
  # Search for a library
  python context7_mcp_client.py resolve "react"

  # Get documentation for a library
  python context7_mcp_client.py docs "react" --topic "hooks"

  # Search and get docs in one command
  python context7_mcp_client.py search-docs "fastapi" --topic "authentication"

  # Show popular libraries
  python context7_mcp_client.py popular

Popular Libraries: {', '.join(list(POPULAR_LIBRARIES.keys())[:8])}...
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Resolve command
    resolve_parser = subparsers.add_parser("resolve", help="Resolve library name to ID")
    resolve_parser.add_argument("library_name", help="Library name to search for")

    # Docs command
    docs_parser = subparsers.add_parser("docs", help="Get documentation for library ID")
    docs_parser.add_argument("library_id", help="Context7-compatible library ID")
    docs_parser.add_argument("--topic", help="Specific topic to focus on")
    docs_parser.add_argument("--tokens", type=int, default=10000, help="Maximum tokens")

    # Search and docs command
    search_docs_parser = subparsers.add_parser(
        "search-docs", help="Search and get docs"
    )
    search_docs_parser.add_argument("library_name", help="Library name")
    search_docs_parser.add_argument("--topic", help="Specific topic to focus on")
    search_docs_parser.add_argument(
        "--tokens", type=int, default=10000, help="Maximum tokens"
    )
    search_docs_parser.add_argument(
        "--show-all", action="store_true", help="Show all matches"
    )

    # Popular command
    popular_parser = subparsers.add_parser("popular", help="Show popular libraries")

    # Global options
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument("--config", help="Path to mcp.json config file")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    try:
        if args.command == "popular":
            print("Popular Libraries Available in Context7:")
            print("=" * 50)
            for lib, desc in POPULAR_LIBRARIES.items():
                print(f"  {lib:<15} - {desc}")
            return

        client = Context7MCPClient(mcp_config_path=args.config, debug=args.debug)

        if args.command == "resolve":
            libraries = await client.resolve_library_id(args.library_name)

            if libraries:
                print(f"✅ Found {len(libraries)} libraries for '{args.library_name}':")
                for i, lib in enumerate(libraries, 1):
                    print(f"\n{i}. {lib.name}")
                    print(f"   ID: {lib.library_id}")
                    print(f"   Description: {lib.description}")
                    print(f"   Trust Score: {lib.trust_score}/10")
            else:
                print(f"❌ No libraries found for '{args.library_name}'")

        elif args.command == "docs":
            result = await client.get_library_docs(
                args.library_id, topic=args.topic, tokens=args.tokens
            )

            if result.success:
                print(f"✅ Documentation for {result.library_id}")
                if result.topic != "general":
                    print(f"Topic: {result.topic}")
                print(f"Tokens: {result.token_count}")
                print("=" * 50)
                print(
                    result.content[:2000] + "..."
                    if len(result.content) > 2000
                    else result.content
                )
            else:
                print(f"❌ Error: {result.error}")

        elif args.command == "search-docs":
            if args.show_all:
                # Show all library matches first
                libraries = await client.resolve_library_id(args.library_name)
                if libraries:
                    print(f"Found {len(libraries)} libraries:")
                    for i, lib in enumerate(libraries, 1):
                        print(f"  {i}. {lib.name} ({lib.library_id})")
                    print()

            result = await client.search_and_get_docs(
                args.library_name, topic=args.topic, tokens=args.tokens
            )

            if result.success:
                print(f"✅ Documentation for {result.library_id}")
                if result.topic != "general":
                    print(f"Topic: {result.topic}")
                print(f"Tokens: ~{result.token_count}")
                print("=" * 50)

                # Show preview for long content
                if len(result.content) > 2000:
                    print(result.content[:2000])
                    print(
                        f"\n... [Content truncated. Total length: {len(result.content)} characters]"
                    )
                else:
                    print(result.content)
            else:
                print(f"❌ Error: {result.error}")

    except KeyboardInterrupt:
        print("\nOperation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

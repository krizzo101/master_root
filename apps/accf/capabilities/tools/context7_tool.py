"""
Context7 Tool - Technical Documentation Access
=============================================

Simple wrapper around the Context7 MCP tools for accessing up-to-date technical
documentation for libraries and frameworks.
"""

import asyncio
import json
import logging
import os
from pathlib import Path
from typing import List, Optional

# MCP imports
try:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    from mcp.types import CallToolResult, TextContent
except ImportError:
    print("Error: MCP Python SDK not installed. Please run: pip install 'mcp[cli]'")
    import sys

    sys.exit(1)

logger = logging.getLogger(__name__)


class Context7UnavailableError(RuntimeError):
    """Raised when the Context7 infrastructure is not available."""


class Context7Result:
    """Normalized Context7 documentation result."""

    def __init__(
        self,
        library_id: str,
        content: str,
        topic: Optional[str] = None,
        token_count: int = 0,
        success: bool = True,
        error: str = "",
    ):
        self.library_id = library_id
        self.content = content
        self.topic = topic
        self.token_count = token_count
        self.success = success
        self.error = error

    def __str__(self) -> str:
        return f"Context7Result({self.library_id}, {len(self.content)} chars)"


class Context7Tool:
    """Simple wrapper around the Context7 MCP tools."""

    def __init__(self, mcp_config_path: Optional[str] = None):
        self.logger = logger
        # Use the same config path logic as the reference
        abs_config = "/home/opsvi/agent_world/.cursor/mcp.json"
        if mcp_config_path is None and os.path.exists(abs_config):
            self.mcp_config_path = abs_config
        else:
            self.mcp_config_path = mcp_config_path or ".cursor/mcp.json"

    async def _call_context7_tool(self, tool_name: str, arguments: dict):
        """Call a Context7 MCP tool with proper session management."""
        # Load server configuration like the reference
        config_path = Path(self.mcp_config_path)
        if not config_path.exists():
            raise FileNotFoundError(f"MCP config file not found: {config_path}")

        with open(config_path) as f:
            config = json.load(f)

        context7_config = config.get("mcpServers", {}).get("tech_docs", {})
        if not context7_config:
            raise ValueError("tech_docs server not found in MCP configuration")

        # Server parameters for stdio connection - use exact same pattern as reference
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
                    return await session.call_tool(tool_name, arguments)
        except Exception as e:
            self.logger.error(f"Failed to establish MCP session: {e}")
            raise Context7UnavailableError(
                f"Failed to connect to Context7 MCP server: {e}"
            )

    async def run(self, parameters: dict) -> dict:
        """Run the Context7 tool with parameters."""
        try:
            query = parameters.get("query", "")
            result = await self.search_and_get_docs(query, tokens=2000)
            return result.__dict__
        except Exception as exc:
            self.logger.error(f"Context7 run failed: {exc}")
            return {
                "library_id": "",
                "content": "",
                "topic": "",
                "token_count": 0,
                "success": False,
                "error": str(exc),
            }

    async def resolve_library(self, library_name: str) -> List[Context7Result]:
        """Resolve a library name to Context7-compatible library IDs."""
        try:
            # Call the resolve-library-id tool
            result = await self._call_context7_tool(
                "resolve-library-id", {"libraryName": library_name}
            )

            # Parse the result using the actual response format
            results = []
            if result.content:
                content = result.content[0]
                if isinstance(content, TextContent):
                    # Parse the library results from the text content
                    # The format is: blocks separated by "----------"
                    blocks = content.text.strip().split("----------")

                    for block in blocks:
                        block = block.strip()
                        if not block:
                            continue

                        # Parse each block for library info
                        current_library = {}
                        lines = block.split("\n")

                        for line in lines:
                            line = line.strip()
                            if not line:
                                continue

                            if line.startswith("- Title:"):
                                current_library["name"] = line.replace(
                                    "- Title:", ""
                                ).strip()
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
                                    current_library["trust_score"] = float(
                                        line.replace("- Trust Score:", "").strip()
                                    )
                                except ValueError:
                                    current_library["trust_score"] = 0

                        # Add the library if we have the required fields
                        if current_library.get("name") and current_library.get(
                            "library_id"
                        ):
                            results.append(
                                Context7Result(
                                    library_id=current_library["library_id"],
                                    content=f"Library: {current_library['name']}\nDescription: {current_library.get('description', '')}\nTrust Score: {current_library.get('trust_score', 0)}",
                                    token_count=len(
                                        current_library.get("description", "")
                                    ),
                                    success=True,
                                )
                            )

            return results
        except Exception as exc:
            self.logger.error(f"Context7 library resolution failed: {exc}")
            raise Context7UnavailableError(str(exc)) from exc

    async def get_documentation(
        self, library_id: str, topic: Optional[str] = None, tokens: int = 10000
    ) -> Context7Result:
        """Get documentation for a specific library."""
        try:
            # Call the get-library-docs tool
            arguments = {"context7CompatibleLibraryID": library_id, "tokens": tokens}
            if topic:
                arguments["topic"] = topic

            result = await self._call_context7_tool("get-library-docs", arguments)

            # Parse the result
            content = ""
            if result.content:
                for item in result.content:
                    if isinstance(item, TextContent):
                        content += item.text

            return Context7Result(
                library_id=library_id,
                content=content,
                topic=topic,
                token_count=len(content),
                success=True,
                error="",
            )
        except Exception as exc:
            self.logger.error(f"Context7 documentation retrieval failed: {exc}")
            raise Context7UnavailableError(str(exc)) from exc

    async def search_and_get_docs(
        self,
        library_name: str,
        topic: Optional[str] = None,
        tokens: int = 10000,
        select_best: bool = True,
    ) -> Context7Result:
        """Search for a library and get its documentation in one step."""
        try:
            # First, resolve the library
            libraries = await self.resolve_library(library_name)

            if not libraries:
                return Context7Result(
                    library_id="",
                    content="",
                    token_count=0,
                    success=False,
                    error="No libraries found",
                )

            # Select the best library if requested
            if select_best and len(libraries) > 1:
                # Simple heuristic: pick the one with highest trust score
                selected_library = max(
                    libraries,
                    key=lambda x: (
                        float(x.content.split("Trust Score: ")[1].split("\n")[0])
                        if "Trust Score: " in x.content
                        else 0
                    ),
                )
            else:
                selected_library = libraries[0]

            # Get documentation for the selected library
            return await self.get_documentation(
                library_id=selected_library.library_id, topic=topic, tokens=tokens
            )
        except Exception as exc:
            self.logger.error(f"Context7 search and get docs failed: {exc}")
            raise Context7UnavailableError(str(exc)) from exc


# Stand-alone quick-check (invoked via `python -m capabilities.tools.context7_tool LIBRARY_NAME`)
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m capabilities.tools.context7_tool LIBRARY_NAME")
        sys.exit(1)

    library_name = sys.argv[1]

    async def test_context7():
        try:
            tool = Context7Tool()
            result = await tool.search_and_get_docs(library_name, tokens=5000)
            print(f"✅ Success: {result}")
            print(f"Content preview: {result.content[:200]}...")
        except Context7UnavailableError as exc:
            print(f"❌ Context7 unavailable: {exc}")
        except Exception as exc:
            print(f"❌ Error: {exc}")

    asyncio.run(test_context7())

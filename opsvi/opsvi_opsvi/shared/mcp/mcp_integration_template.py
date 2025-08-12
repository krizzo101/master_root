#!/usr/bin/env python3
"""
MCP Server Integration Template for Python

This template demonstrates how to integrate any Model Context Protocol (MCP) server
into a Python application. It provides a complete framework with error handling,
configuration management, and best practices.

## What is Model Context Protocol (MCP)?

MCP is a protocol that enables AI applications to connect to external tools and
data sources. It uses JSON-RPC 2.0 for communication and supports various
transport mechanisms (stdio, HTTP, WebSocket).

## Official Documentation

- MCP Specification: https://modelcontextprotocol.io/
- Python SDK: https://github.com/modelcontextprotocol/python-sdk
- Server Registry: https://github.com/modelcontextprotocol/servers

## Architecture Overview

1. **MCP Client** (This Python script) - Connects to MCP servers
2. **MCP Server** (External process) - Provides tools and capabilities
3. **Transport Layer** - Communication mechanism (stdio, HTTP, etc.)
4. **Protocol Layer** - JSON-RPC 2.0 message format

## Prerequisites

```bash
# Install MCP Python SDK
pip install "mcp[cli]"

# Install specific MCP server (example)
npm install -g your-mcp-server-package
```

## Configuration

MCP servers can be configured in mcp.json:
```json
{
  "mcpServers": {
    "your_server": {
      "command": "npx",
      "args": ["-y", "your-mcp-server-package"],
      "env": {
        "API_KEY": "your_api_key_here"
      }
    }
  }
}
```
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
from typing import Any

# MCP imports - Core components for MCP integration
try:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    from mcp.types import CallToolResult, TextContent
except ImportError:
    print("Error: MCP Python SDK not installed.")
    print("Install with: pip install 'mcp[cli]'")
    sys.exit(1)


# Custom exceptions for better error handling
class MCPError(Exception):
    """Base exception for MCP-related errors."""

    pass


class ServerNotFoundError(MCPError):
    """Raised when MCP server is not found or not installed."""

    pass


class AuthenticationError(MCPError):
    """Raised when API key is invalid or missing."""

    pass


class ConnectionError(MCPError):
    """Raised when connection to MCP server fails."""

    pass


class ToolNotFoundError(MCPError):
    """Raised when requested tool is not available on server."""

    pass


@dataclass
class MCPServerConfig:
    """Configuration for an MCP server."""

    command: str
    args: list[str]
    env: dict[str, str]
    name: str
    description: str = ""


@dataclass
class ToolResult:
    """Represents the result of an MCP tool call."""

    tool_name: str
    success: bool
    content: str
    raw_result: Any = None
    error_message: str = ""


class MCPServerClient:
    """
    Generic MCP server client that can connect to any MCP server.

    This class provides a reusable framework for MCP server integration
    with automatic server management, error handling, and result parsing.
    """

    def __init__(
        self,
        server_name: str,
        mcp_config_path: str | None = None,
        debug: bool = False,
        **server_overrides,
    ):
        """
        Initialize the MCP client.

        Args:
            server_name: Name of the server in mcp.json config
            mcp_config_path: Path to mcp.json file (default: .cursor/mcp.json)
            debug: Enable debug logging
            **server_overrides: Override server configuration parameters
        """
        self.server_name = server_name
        self.mcp_config_path = mcp_config_path or ".cursor/mcp.json"
        self.debug = debug
        self.server_overrides = server_overrides

        # Setup logging
        logging.basicConfig(
            level=logging.DEBUG if debug else logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )
        self.logger = logging.getLogger(__name__)

        # Load server configuration
        self.server_config = self._load_server_config()

        if not self.server_config:
            raise ValueError(f"Server '{server_name}' not found in MCP configuration")

    def _load_server_config(self) -> MCPServerConfig | None:
        """
        Load server configuration from mcp.json file.

        Returns:
            MCPServerConfig object if found, None otherwise
        """
        try:
            config_path = Path(self.mcp_config_path)
            if not config_path.exists():
                self.logger.error(f"MCP config file not found: {config_path}")
                return None

            with open(config_path) as f:
                config = json.load(f)

            servers = config.get("mcpServers", {})
            server_data = servers.get(self.server_name)

            if not server_data:
                self.logger.error(f"Server '{self.server_name}' not found in config")
                return None

            # Apply any overrides
            server_data.update(self.server_overrides)

            return MCPServerConfig(
                name=self.server_name,
                command=server_data.get("command", ""),
                args=server_data.get("args", []),
                env=server_data.get("env", {}),
                description=f"MCP server: {self.server_name}",
            )

        except (json.JSONDecodeError, FileNotFoundError, KeyError) as e:
            self.logger.error(f"Error loading MCP config: {e}")
            return None

    def _check_server_installed(self) -> bool:
        """
        Check if the MCP server is installed and accessible.

        Returns:
            True if server is accessible, False otherwise
        """
        try:
            # Try to run the server with --help to check availability
            cmd = [self.server_config.command] + self.server_config.args + ["--help"]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10,
                env={**os.environ, **self.server_config.env},
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            return False

    def _ensure_server_available(self) -> None:
        """
        Ensure the MCP server is available, with helpful error messages.

        Raises:
            ServerNotFoundError: If server cannot be found or accessed
        """
        if not self._check_server_installed():
            error_msg = (
                f"MCP server '{self.server_name}' not found or not accessible.\n"
                f"Command: {self.server_config.command} {' '.join(self.server_config.args)}\n"
                f"Please ensure the server is properly installed.\n"
                f"For npm packages: npm install -g <package-name>\n"
                f"For Python packages: pip install <package-name>"
            )
            raise ServerNotFoundError(error_msg)

    @asynccontextmanager
    async def _get_session(self):
        """
        Create and manage an MCP session.

        This context manager handles:
        - Server availability checking
        - Session initialization
        - Proper cleanup on exit
        - Error handling and logging

        Yields:
            ClientSession: Active MCP session
        """
        self._ensure_server_available()

        # Create server parameters for stdio transport
        server_params = StdioServerParameters(
            command=self.server_config.command,
            args=self.server_config.args,
            env={**os.environ, **self.server_config.env},
        )

        self.logger.debug(f"Starting MCP server: {self.server_config.command}")

        try:
            # Establish stdio communication with the server
            async with stdio_client(server_params) as (read, write):
                # Create and initialize the client session
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    self.logger.debug("MCP session initialized successfully")

                    # Log available tools for debugging
                    if self.debug:
                        try:
                            tools = await session.list_tools()
                            tool_names = [tool.name for tool in tools.tools]
                            self.logger.debug(f"Available tools: {tool_names}")
                        except Exception as e:
                            self.logger.debug(f"Could not list tools: {e}")

                    yield session

        except Exception as e:
            self.logger.error(f"Failed to establish MCP session: {e}")
            raise ConnectionError(f"Failed to connect to MCP server: {e}")

    def _parse_tool_result(self, result: CallToolResult, tool_name: str) -> ToolResult:
        """
        Parse the result from an MCP tool call.

        Args:
            result: Raw result from MCP tool call
            tool_name: Name of the tool that was called

        Returns:
            ToolResult: Parsed result object
        """
        try:
            if not result.content:
                return ToolResult(
                    tool_name=tool_name,
                    success=False,
                    content="",
                    error_message="No content in tool result",
                )

            # Extract content from the result
            content_parts = []
            for content in result.content:
                if isinstance(content, TextContent):
                    content_parts.append(content.text)
                else:
                    content_parts.append(str(content))

            full_content = "\n".join(content_parts)

            return ToolResult(
                tool_name=tool_name,
                success=True,
                content=full_content,
                raw_result=result,
            )

        except Exception as e:
            self.logger.error(f"Error parsing tool result: {e}")
            return ToolResult(
                tool_name=tool_name,
                success=False,
                content="",
                error_message=str(e),
                raw_result=result,
            )

    async def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> ToolResult:
        """
        Call a tool on the MCP server.

        Args:
            tool_name: Name of the tool to call
            arguments: Arguments to pass to the tool

        Returns:
            ToolResult: Result from the tool call

        Raises:
            MCPError: If tool call fails
        """
        self.logger.info(f"Calling tool '{tool_name}' with args: {arguments}")

        async with self._get_session() as session:
            try:
                result = await session.call_tool(tool_name, arguments)
                parsed_result = self._parse_tool_result(result, tool_name)

                if parsed_result.success:
                    self.logger.debug(f"Tool '{tool_name}' completed successfully")
                else:
                    self.logger.warning(f"Tool '{tool_name}' returned no content")

                return parsed_result

            except Exception as e:
                error_msg = f"Tool call failed: {e}"
                self.logger.error(error_msg)

                # Check if it's a tool not found error
                if "not found" in str(e).lower() or "unknown" in str(e).lower():
                    raise ToolNotFoundError(f"Tool '{tool_name}' not found on server")
                else:
                    raise MCPError(error_msg)

    async def list_available_tools(self) -> list[str]:
        """
        Get a list of tools available on the server.

        Returns:
            List of available tool names
        """
        async with self._get_session() as session:
            try:
                tools = await session.list_tools()
                return [tool.name for tool in tools.tools]
            except Exception as e:
                self.logger.error(f"Failed to list tools: {e}")
                return []

    async def get_tool_info(self, tool_name: str) -> dict[str, Any] | None:
        """
        Get detailed information about a specific tool.

        Args:
            tool_name: Name of the tool

        Returns:
            Tool information dictionary or None if not found
        """
        async with self._get_session() as session:
            try:
                tools = await session.list_tools()
                for tool in tools.tools:
                    if tool.name == tool_name:
                        return {
                            "name": tool.name,
                            "description": tool.description,
                            "input_schema": tool.inputSchema,
                        }
                return None
            except Exception as e:
                self.logger.error(f"Failed to get tool info: {e}")
                return None


# Utility functions for common MCP operations


async def quick_tool_call(
    server_name: str,
    tool_name: str,
    arguments: dict[str, Any],
    mcp_config_path: str | None = None,
) -> ToolResult:
    """
    Perform a quick tool call without creating a persistent client.

    Args:
        server_name: Name of the MCP server
        tool_name: Name of the tool to call
        arguments: Tool arguments
        mcp_config_path: Path to mcp.json config file

    Returns:
        ToolResult: Result from the tool call
    """
    client = MCPServerClient(server_name, mcp_config_path)
    return await client.call_tool(tool_name, arguments)


async def list_server_tools(
    server_name: str, mcp_config_path: str | None = None
) -> list[str]:
    """
    List all available tools on an MCP server.

    Args:
        server_name: Name of the MCP server
        mcp_config_path: Path to mcp.json config file

    Returns:
        List of available tool names
    """
    client = MCPServerClient(server_name, mcp_config_path)
    return await client.list_available_tools()


# Example usage and testing
async def example_usage():
    """
    Example showing how to use the MCP integration template.

    This example demonstrates:
    1. Creating an MCP client
    2. Listing available tools
    3. Calling a tool with arguments
    4. Handling results and errors
    """
    print("🔧 MCP Integration Example")
    print("=" * 50)

    # Replace 'your_server' with an actual server name from mcp.json
    server_name = "web_search"  # Example: using brave search

    try:
        # Create MCP client
        client = MCPServerClient(server_name, debug=True)
        print(f"✅ Connected to MCP server: {server_name}")

        # List available tools
        tools = await client.list_available_tools()
        print(f"📋 Available tools: {tools}")

        # Example tool call (adjust based on your server's tools)
        if tools:
            example_tool = tools[0]
            print(f"🔍 Testing tool: {example_tool}")

            # Get tool information
            tool_info = await client.get_tool_info(example_tool)
            if tool_info:
                print(f"📖 Tool info: {tool_info}")

            # Example tool call (you'll need to adjust arguments)
            # result = await client.call_tool(example_tool, {"query": "test"})
            # print(f"📊 Result: {result.content}")

        print("🎉 MCP integration example completed successfully!")

    except Exception as e:
        print(f"❌ Error: {e}")


# Command line interface for testing and demonstration
async def main():
    """
    Command line interface for MCP server interaction.

    Usage examples:
        python mcp_integration_template.py list-tools web_search
        python mcp_integration_template.py call-tool web_search brave_web_search '{"query": "test"}'
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="MCP Server Integration Template",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List available tools on a server
  python mcp_integration_template.py list-tools web_search

  # Call a tool with arguments (JSON format)
  python mcp_integration_template.py call-tool web_search brave_web_search '{"query": "hello"}'

  # Run example usage
  python mcp_integration_template.py example
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # List tools command
    list_parser = subparsers.add_parser("list-tools", help="List available tools")
    list_parser.add_argument("server", help="MCP server name")
    list_parser.add_argument("--config", help="Path to mcp.json config file")

    # Call tool command
    call_parser = subparsers.add_parser("call-tool", help="Call a specific tool")
    call_parser.add_argument("server", help="MCP server name")
    call_parser.add_argument("tool", help="Tool name to call")
    call_parser.add_argument("arguments", help="Tool arguments as JSON string")
    call_parser.add_argument("--config", help="Path to mcp.json config file")
    call_parser.add_argument(
        "--debug", action="store_true", help="Enable debug logging"
    )

    # Example command
    example_parser = subparsers.add_parser("example", help="Run example usage")

    args = parser.parse_args()

    try:
        if args.command == "list-tools":
            tools = await list_server_tools(args.server, args.config)
            print(f"Available tools on '{args.server}':")
            for tool in tools:
                print(f"  - {tool}")

        elif args.command == "call-tool":
            try:
                arguments = json.loads(args.arguments)
            except json.JSONDecodeError:
                print("Error: Arguments must be valid JSON")
                sys.exit(1)

            result = await quick_tool_call(
                args.server, args.tool, arguments, args.config
            )

            print("Tool call result:")
            print(f"Success: {result.success}")
            print(f"Content: {result.content}")
            if result.error_message:
                print(f"Error: {result.error_message}")

        elif args.command == "example":
            await example_usage()

        else:
            parser.print_help()

    except KeyboardInterrupt:
        print("\nOperation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

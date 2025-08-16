"""
mcp_server_template.py

A robust, extensible MCP server template for Cursor IDE.

Key Features:
- Strict PEP 8 compliance and full type hinting
- Detailed, clear docstrings throughout
- Modular tool system with runtime registration/removal
- Async best practices and robust error handling
- Input schema stubs for type safety and future validation
- CLI and environment-based configuration
- Cursor IDE compatibility (stdio transport, tool schemas)
"""

import asyncio
import logging
import os
from typing import Any

from mcp.server import Server
from mcp.types import TextContent, Tool

# --- Configuration Utilities ---


def configure_logging(level: int = logging.INFO) -> None:
    """
    Configure logging for the MCP server.

    Args:
        level: Logging level (default: logging.INFO).
    """
    logging.basicConfig(
        level=level, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )


logger = logging.getLogger(__name__)

# --- Tool System ---


class ToolExecutionError(Exception):
    """Custom exception for tool execution errors."""


class BaseTool:
    """
    Base class for MCP tools. Extend this for each tool.

    Attributes:
        name: Tool name (unique).
        description: Tool description.
        input_schema: JSON schema for tool input.
    """

    name: str
    description: str
    input_schema: dict[str, Any]

    def __init__(
        self, name: str, description: str, input_schema: dict[str, Any]
    ) -> None:
        self.name = name
        self.description = description
        self.input_schema = input_schema

    async def execute(self, arguments: dict[str, Any]) -> list[TextContent]:
        """
        Execute the tool logic. Override in subclasses.

        Args:
            arguments: Tool arguments.

        Returns:
            List of TextContent objects.

        Raises:
            ToolExecutionError: If execution fails.
        """
        raise NotImplementedError("Tool logic not implemented.")

    def validate_input(self, arguments: dict[str, Any]) -> None:
        """
        Validate input arguments against the input schema.
        (Stub for future JSON Schema validation.)

        Args:
            arguments: Tool arguments.

        Raises:
            ValueError: If validation fails.
        """
        # TODO: Implement JSON Schema validation if needed.
        pass


# --- Example Tool ---


class EchoTool(BaseTool):
    """
    Example tool that echoes the input message.
    """

    def __init__(self) -> None:
        super().__init__(
            name="echo",
            description="Echoes the input arguments.",
            input_schema={
                "type": "object",
                "properties": {
                    "message": {"type": "string", "description": "Message to echo."}
                },
                "required": ["message"],
            },
        )

    async def execute(self, arguments: dict[str, Any]) -> list[TextContent]:
        self.validate_input(arguments)
        message = arguments.get("message", "")
        return [TextContent(type="text", text=message)]


# --- MCP Server Template ---


class MCPServerTemplate:
    """
    Generic MCP server for Cursor IDE.

    Methods:
        register_tool: Add a tool at runtime.
        unregister_tool: Remove a tool at runtime.
        load_plugins: Stub for plugin loading.
        run: Start the server (stdio transport).
    """

    def __init__(
        self,
        name: str,
        tools: list[BaseTool] | None = None,
        log_level: int = logging.INFO,
    ) -> None:
        """
        Initialize the MCP server.

        Args:
            name: Server name.
            tools: List of BaseTool instances.
            log_level: Logging level.
        """
        configure_logging(log_level)
        self.server = Server(name)
        self.tools: dict[str, BaseTool] = {}
        if tools:
            for tool in tools:
                self.register_tool(tool)
        self._register_server_handlers()

    def register_tool(self, tool: BaseTool) -> None:
        """
        Register a tool at runtime.

        Args:
            tool: Instance of BaseTool.
        """
        if tool.name in self.tools:
            logger.warning("Tool '%s' already registered. Overwriting.", tool.name)
        self.tools[tool.name] = tool
        logger.info("Registered tool: %s", tool.name)

    def unregister_tool(self, tool_name: str) -> None:
        """
        Unregister a tool at runtime.

        Args:
            tool_name: Name of the tool to remove.
        """
        if tool_name in self.tools:
            del self.tools[tool_name]
            logger.info("Unregistered tool: %s", tool_name)
        else:
            logger.warning("Tool '%s' not found for removal.", tool_name)

    def load_plugins(self, plugin_dir: str | None = None) -> None:
        """
        Stub for plugin loading. Extend to support dynamic tool discovery.

        Args:
            plugin_dir: Directory to load plugins from.
        """
        # TODO: Implement plugin loading if needed.
        pass

    def _register_server_handlers(self) -> None:
        """
        Register tool listing and invocation handlers with the MCP server.
        """

        @self.server.list_tools()
        async def list_tools() -> list[Tool]:
            logger.info("Listing registered tools.")
            return [
                Tool(
                    name=tool.name,
                    description=tool.description,
                    inputSchema=tool.input_schema,
                )
                for tool in self.tools.values()
            ]

        @self.server.call_tool()
        async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
            logger.info("Tool call requested: %s with arguments: %s", name, arguments)
            tool = self.tools.get(name)
            if not tool:
                logger.error("Unknown tool: %s", name)
                return [
                    TextContent(
                        type="text",
                        text=f"Error: Unknown tool '{name}'. Available tools: {list(self.tools.keys())}",
                    )
                ]
            try:
                tool.validate_input(arguments)
                result = await tool.execute(arguments)
                return result
            except Exception as exc:
                logger.exception("Tool '%s' execution failed: %s", name, exc)
                return [
                    TextContent(
                        type="text",
                        text=f"Error executing tool '{name}': {exc}",
                    )
                ]

    async def run(self) -> None:
        """
        Run the MCP server using stdio transport (Cursor IDE compatible).
        """
        from mcp.server.stdio import stdio_server

        logger.info("Starting MCP server (stdio transport)")
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream, write_stream, self.server.create_initialization_options()
            )


# --- CLI Entrypoint ---


def main() -> None:
    """
    CLI entrypoint for the MCP server template.
    Supports environment variables and CLI args for configuration.
    """
    import argparse

    parser = argparse.ArgumentParser(description="Generic MCP Server for Cursor IDE")
    parser.add_argument(
        "--name",
        type=str,
        default=os.getenv("MCP_SERVER_NAME", "generic_mcp_server"),
        help="Server name (default: generic_mcp_server or $MCP_SERVER_NAME)",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default=os.getenv("MCP_LOG_LEVEL", "INFO"),
        help="Logging level (default: INFO or $MCP_LOG_LEVEL)",
    )
    args = parser.parse_args()

    log_level = getattr(logging, args.log_level.upper(), logging.INFO)
    tools = [EchoTool()]
    server = MCPServerTemplate(name=args.name, tools=tools, log_level=log_level)
    asyncio.run(server.run())


if __name__ == "__main__":
    main()

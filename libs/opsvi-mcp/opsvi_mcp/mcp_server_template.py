"""
mcp_server_template.py

A robust, extensible MCP server template for Cursor IDE.

Key Features:
- Strict PEP 8 compliance and full type hinting
- Detailed, clear docstrings throughout
- Modular tool system with runtime registration/removal
- Async best practices and robust error handling
- JSON Schema validation for tool inputs using jsonschema library
- Dynamic plugin loading system for extending functionality
- CLI and environment-based configuration
- Cursor IDE compatibility (stdio transport, tool schemas)
- Backward compatible with existing tools

Usage:
    # Basic usage with built-in tools
    python -m mcp_server_template
    
    # Load plugins from custom directory
    python -m mcp_server_template --plugin-dir ./my_plugins
    
    # Set via environment variables
    export MCP_SERVER_NAME=my_server
    export MCP_PLUGIN_DIR=/path/to/plugins
    export MCP_LOG_LEVEL=DEBUG
    python -m mcp_server_template

Plugin Development:
    See plugins/README.md for detailed plugin development guide.
    Example plugins are provided in the plugins/ directory.
"""

import asyncio
import importlib.util
import inspect
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Type

import jsonschema
from jsonschema import ValidationError
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
    input_schema: Dict[str, Any]

    def __init__(
        self, name: str, description: str, input_schema: Dict[str, Any]
    ) -> None:
        self.name = name
        self.description = description
        self.input_schema = input_schema

    async def execute(self, arguments: Dict[str, Any]) -> List[TextContent]:
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

    def validate_input(self, arguments: Dict[str, Any]) -> None:
        """
        Validate input arguments against the input schema using JSON Schema.

        Args:
            arguments: Tool arguments.

        Raises:
            ValueError: If validation fails.
        """
        try:
            jsonschema.validate(instance=arguments, schema=self.input_schema)
        except ValidationError as e:
            raise ValueError(f"Input validation failed: {e.message}")


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

    async def execute(self, arguments: Dict[str, Any]) -> List[TextContent]:
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
        tools: Optional[List[BaseTool]] = None,
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
        self.tools: Dict[str, BaseTool] = {}
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

    def load_plugins(self, plugin_dir: Optional[str] = None) -> None:
        """
        Dynamically load plugin tools from a directory.

        Plugins should be Python files containing classes that inherit from BaseTool.
        The plugin directory structure:
            plugins/
                my_tool.py  (contains one or more BaseTool subclasses)
                another_tool.py

        Args:
            plugin_dir: Directory to load plugins from. Defaults to './plugins'.
        """
        if plugin_dir is None:
            plugin_dir = os.getenv("MCP_PLUGIN_DIR", "./plugins")
        
        plugin_path = Path(plugin_dir)
        if not plugin_path.exists():
            logger.info("Plugin directory '%s' does not exist. Skipping plugin loading.", plugin_dir)
            return
        
        if not plugin_path.is_dir():
            logger.warning("Plugin path '%s' is not a directory. Skipping plugin loading.", plugin_dir)
            return
        
        # Add plugin directory to sys.path temporarily
        original_path = sys.path.copy()
        sys.path.insert(0, str(plugin_path.absolute()))
        
        try:
            for plugin_file in plugin_path.glob("*.py"):
                if plugin_file.name.startswith("_"):
                    continue  # Skip private modules
                
                try:
                    # Load the module dynamically
                    module_name = plugin_file.stem
                    spec = importlib.util.spec_from_file_location(
                        module_name, plugin_file
                    )
                    if spec is None or spec.loader is None:
                        logger.warning("Could not load spec for plugin: %s", plugin_file)
                        continue
                    
                    module = importlib.util.module_from_spec(spec)
                    sys.modules[module_name] = module
                    spec.loader.exec_module(module)
                    
                    # Find and register all BaseTool subclasses
                    for name, obj in inspect.getmembers(module):
                        if (
                            inspect.isclass(obj)
                            and issubclass(obj, BaseTool)
                            and obj is not BaseTool
                        ):
                            try:
                                # Instantiate and register the tool
                                tool_instance = obj()
                                self.register_tool(tool_instance)
                                logger.info(
                                    "Loaded plugin tool '%s' from %s",
                                    tool_instance.name,
                                    plugin_file.name,
                                )
                            except Exception as e:
                                logger.error(
                                    "Failed to instantiate tool '%s' from %s: %s",
                                    name,
                                    plugin_file.name,
                                    e,
                                )
                except Exception as e:
                    logger.error("Failed to load plugin from %s: %s", plugin_file, e)
        finally:
            # Restore original sys.path
            sys.path = original_path

    def _register_server_handlers(self) -> None:
        """
        Register tool listing and invocation handlers with the MCP server.
        """

        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
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
        async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
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

    parser.add_argument(
        "--plugin-dir",
        type=str,
        default=os.getenv("MCP_PLUGIN_DIR", "./plugins"),
        help="Plugin directory path (default: ./plugins or $MCP_PLUGIN_DIR)",
    )
    args = parser.parse_args()

    log_level = getattr(logging, args.log_level.upper(), logging.INFO)
    tools = [EchoTool()]
    server = MCPServerTemplate(name=args.name, tools=tools, log_level=log_level)
    
    # Load plugins after server initialization
    server.load_plugins(args.plugin_dir)
    
    asyncio.run(server.run())


if __name__ == "__main__":
    main()

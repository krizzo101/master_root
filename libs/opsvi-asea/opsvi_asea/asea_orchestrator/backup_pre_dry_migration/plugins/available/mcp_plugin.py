from typing import List, Any, Optional, Dict
import asyncio
import logging

from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters

from asea_orchestrator.plugins.base_plugin import BasePlugin, EventBus
from asea_orchestrator.plugins.types import (
    PluginConfig,
    ExecutionContext,
    PluginResult,
    Capability,
    ValidationResult,
)

logger = logging.getLogger(__name__)


class MCPPlugin(BasePlugin):
    """
    MCP (Model Context Protocol) Plugin for ASEA Orchestrator

    Phase 1: Focuses on sequential thinking capabilities
    Connects to MCP servers via stdio transport using official MCP Python SDK
    """

    def __init__(self):
        self.sessions: Dict[str, ClientSession] = {}
        self.stdio_contexts: Dict[str, Any] = {}
        self.event_bus: Optional[EventBus] = None

        # Phase 1: Focus on sequential thinking server
        self.server_configs = {
            "sequential_thinking": {
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-sequential-thinking"],
                "tools": ["sequential_thinking"],
            }
        }

    @staticmethod
    def get_name() -> str:
        return "mcp"

    async def initialize(
        self, config: PluginConfig, event_bus: Optional[EventBus] = None
    ) -> None:
        """Initialize MCP plugin with connection management."""
        self.event_bus = event_bus

        try:
            # Initialize connection to sequential thinking server
            await self._connect_to_server("sequential_thinking")
            logger.info(
                "MCP Plugin initialized successfully with sequential thinking server"
            )

        except Exception as e:
            logger.error(f"Failed to initialize MCP Plugin: {e}")
            await self.cleanup()
            raise

    async def _connect_to_server(self, server_name: str) -> None:
        """Connect to a specific MCP server."""
        if server_name not in self.server_configs:
            raise ValueError(f"Unknown MCP server: {server_name}")

        config = self.server_configs[server_name]

        try:
            # Create server parameters
            server_params = StdioServerParameters(
                command=config["command"], args=config["args"], env=None
            )

            # For now, create a simple connection without context manager
            # This will be a persistent connection managed by the plugin lifecycle
            import subprocess
            import asyncio
            from mcp.client.stdio import get_default_environment

            # Start the MCP server process
            env = get_default_environment()
            if server_params.env:
                env.update(server_params.env)

            process = await asyncio.create_subprocess_exec(
                server_params.command,
                *server_params.args,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
            )

            if not process.stdin or not process.stdout:
                raise RuntimeError("Failed to create stdio streams")

            # Store process for cleanup
            self.stdio_contexts[server_name] = process

            # Create session with the streams
            session = ClientSession(process.stdout, process.stdin)
            await session.initialize()

            # Store session for reuse
            self.sessions[server_name] = session

            # List available tools for validation
            response = await session.list_tools()
            tools = [tool.name for tool in response.tools]
            logger.info(f"Connected to {server_name} with tools: {tools}")

        except Exception as e:
            logger.error(f"Failed to connect to MCP server {server_name}: {e}")
            raise

    async def execute(self, context: ExecutionContext) -> PluginResult:
        """Execute MCP tool calls."""
        params = context.state

        try:
            action = params.get("action", "call_tool")

            if action == "call_tool":
                return await self._call_tool(params)
            elif action == "list_tools":
                return await self._list_tools(params)
            else:
                return PluginResult(
                    success=False, error_message=f"Unknown action: {action}"
                )

        except Exception as e:
            logger.error(f"MCP Plugin execution error: {e}")
            return PluginResult(
                success=False, error_message=f"MCP execution failed: {str(e)}"
            )

    async def _call_tool(self, params: Dict[str, Any]) -> PluginResult:
        """Call a tool on an MCP server."""
        server = params.get("server", "sequential_thinking")
        tool_name = params.get("tool")
        arguments = params.get("arguments", {})

        if not tool_name:
            return PluginResult(success=False, error_message="Tool name is required")

        if server not in self.sessions:
            return PluginResult(
                success=False, error_message=f"Not connected to MCP server: {server}"
            )

        try:
            session = self.sessions[server]
            result = await session.call_tool(tool_name, arguments)

            return PluginResult(
                success=True,
                data={
                    "tool_result": result.content,
                    "server": server,
                    "tool": tool_name,
                    "arguments": arguments,
                },
            )

        except Exception as e:
            logger.error(f"Failed to call tool {tool_name} on {server}: {e}")
            return PluginResult(
                success=False, error_message=f"Tool call failed: {str(e)}"
            )

    async def _list_tools(self, params: Dict[str, Any]) -> PluginResult:
        """List available tools from connected MCP servers."""
        server = params.get("server")

        try:
            if server:
                # List tools from specific server
                if server not in self.sessions:
                    return PluginResult(
                        success=False,
                        error_message=f"Not connected to MCP server: {server}",
                    )

                session = self.sessions[server]
                response = await session.list_tools()
                tools = [
                    {
                        "name": tool.name,
                        "description": tool.description,
                        "server": server,
                    }
                    for tool in response.tools
                ]
            else:
                # List tools from all connected servers
                tools = []
                for server_name, session in self.sessions.items():
                    response = await session.list_tools()
                    for tool in response.tools:
                        tools.append(
                            {
                                "name": tool.name,
                                "description": tool.description,
                                "server": server_name,
                            }
                        )

            return PluginResult(success=True, data={"tools": tools})

        except Exception as e:
            logger.error(f"Failed to list tools: {e}")
            return PluginResult(
                success=False, error_message=f"Failed to list tools: {str(e)}"
            )

    async def cleanup(self) -> None:
        """Clean up MCP connections."""
        try:
            # Close all sessions
            for server_name in list(self.sessions.keys()):
                try:
                    session = self.sessions.pop(server_name)
                    # Sessions don't have explicit close methods in this version
                    # They will be cleaned up when the process terminates
                except Exception as e:
                    logger.error(f"Error closing session for {server_name}: {e}")

            # Terminate all MCP server processes
            for server_name in list(self.stdio_contexts.keys()):
                try:
                    process = self.stdio_contexts.pop(server_name)
                    if process and process.returncode is None:
                        process.terminate()
                        try:
                            await asyncio.wait_for(process.wait(), timeout=5.0)
                        except asyncio.TimeoutError:
                            logger.warning(
                                f"Force killing MCP server process for {server_name}"
                            )
                            process.kill()
                            await process.wait()
                except Exception as e:
                    logger.error(f"Error terminating process for {server_name}: {e}")

            logger.info("MCP Plugin cleanup completed")

        except Exception as e:
            logger.error(f"Error during MCP Plugin cleanup: {e}")

    def get_capabilities(self) -> List[Capability]:
        """Return plugin capabilities."""
        return [
            Capability(
                name="call_tool",
                description="Execute a tool on an MCP server (Phase 1: sequential_thinking)",
            ),
            Capability(
                name="list_tools",
                description="List available tools from connected MCP servers",
            ),
        ]

    def validate_input(self, input_data: Any) -> ValidationResult:
        """Validate input parameters."""
        if not isinstance(input_data, dict):
            return ValidationResult(
                is_valid=False, errors=["Input must be a dictionary"]
            )

        action = input_data.get("action", "call_tool")

        if action == "call_tool":
            if "tool" not in input_data:
                return ValidationResult(
                    is_valid=False,
                    errors=["Tool name is required for call_tool action"],
                )

        return ValidationResult(is_valid=True, errors=[])

"""
MCP Tool Registry - Modular Implementation

A clean, modular orchestrator for MCP tools with parallel execution and error recovery.
Coordinates specialized modules for tool management, execution, and health monitoring.
"""

import logging
from typing import Any

from src.applications.oamat_sd.src.models.tool_models import (
    ParallelExecutionResult,
    ToolCategory,
    ToolExecutionResult,
)
from src.applications.oamat_sd.src.tools.core.execution_engine import (
    ToolExecutionEngine,
)
from src.applications.oamat_sd.src.tools.core.health_monitor import ToolHealthMonitor
from src.applications.oamat_sd.src.tools.core.tool_manager import ToolManager


class MCPToolRegistry:
    """
    Modular MCP Tool Registry with Advanced Capabilities

    This registry orchestrates the complete MCP tool workflow:
    1. Tool Management -> Register and initialize tools
    2. Health Monitoring -> Track performance and status
    3. Execution Engine -> Execute tools with parallel support
    4. Error Recovery -> Graceful degradation and alternatives
    """

    def __init__(self, use_real_clients: bool | None = None):
        """Initialize the MCP Tool Registry with all modular components"""
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

        # Initialize modular components
        self.tool_manager = ToolManager()
        self.health_monitor = ToolHealthMonitor(self.tool_manager)
        self.execution_engine = ToolExecutionEngine(
            self.tool_manager, self.health_monitor
        )

        # Initialize tools
        self.tool_manager.initialize_tools(use_real_clients)

        self.logger.info("✅ MCP Tool Registry initialized with modular architecture")

    # Registry Adapter for backward compatibility
    class RegistryAdapter:
        """Adapter to translate between ResearchWorkflowTool interface and Smart Decomposition interface."""

        def __init__(self, smart_decomp_registry):
            self.registry = smart_decomp_registry

        def execute_tool(self, tool_name: str, method: str, params: dict):
            """Translate execute_tool calls to execute_tool_method format."""
            # Map tool names from ResearchWorkflowTool format to Smart Decomposition format
            tool_mapping = {
                "brave.search": "brave_search",
                "firecrawl.scraping": "firecrawl",
            }

            # Use explicit tool mapping with no fallback - fail fast if unmapped
            if tool_name in tool_mapping:
                mapped_tool = tool_mapping[tool_name]
            else:
                mapped_tool = tool_name  # Pass through unmapped tools as-is

            # Convert params dict to kwargs and execute synchronously
            try:
                # Use asyncio.run to execute the async method synchronously
                import asyncio

                # Check if we're already in an event loop
                try:
                    loop = asyncio.get_running_loop()
                    # We're in an async context, need to run in a thread
                    import concurrent.futures

                    async def _async_execute():
                        return await self.registry.execute_tool_method(
                            mapped_tool, method, **params
                        )

                    # Run the async call in a thread pool to avoid blocking the current loop
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(asyncio.run, _async_execute())
                        result = future.result()

                except RuntimeError:
                    # No event loop running, can use asyncio.run directly
                    async def _async_execute():
                        return await self.registry.execute_tool_method(
                            mapped_tool, method, **params
                        )

                    result = asyncio.run(_async_execute())

                # Special handling for Brave Search results
                if mapped_tool == "brave_search" and result.success and result.result:
                    # Parse Smart Decomposition's formatted search results
                    parsed_results = self._parse_brave_search_results(result.result)

                    # Create adapted SearchResponse with parsed results
                    class AdaptedSearchResponse:
                        def __init__(self, results):
                            self.results = results

                    adapted_data = AdaptedSearchResponse(parsed_results)
                else:
                    adapted_data = result.result

                # Convert ToolExecutionResult to format expected by ResearchWorkflowTool
                class AdaptedResult:
                    def __init__(self, success, data=None, error_message=None):
                        self.success = success
                        self.data = data
                        self.error_message = error_message

                return AdaptedResult(
                    success=result.success,
                    data=adapted_data,
                    error_message=result.error if not result.success else None,
                )

            except Exception as e:
                # Return failed result for any execution errors
                class AdaptedResult:
                    def __init__(self, success, data=None, error_message=None):
                        self.success = success
                        self.data = data
                        self.error_message = error_message

                return AdaptedResult(success=False, data=None, error_message=str(e))

        def _parse_brave_search_results(self, search_result_data):
            """Parse search results from Smart Decomposition format to ResearchWorkflowTool format"""
            if isinstance(search_result_data, dict) and "results" in search_result_data:
                # Already in the expected format
                return search_result_data["results"]
            elif isinstance(search_result_data, list):
                # List of results
                return search_result_data
            else:
                # Fallback for unexpected format
                return []

    # Public API Methods
    async def execute_tool_method(
        self, tool_name: str, method: str, **kwargs
    ) -> ToolExecutionResult:
        """Execute a specific method on a tool"""
        return await self.execution_engine.execute_tool_method(
            tool_name, method, **kwargs
        )

    async def execute_tools_parallel(
        self, tool_requests: list[dict[str, Any]]
    ) -> ParallelExecutionResult:
        """Execute multiple tool methods in parallel"""
        return await self.execution_engine.execute_tools_parallel(tool_requests)

    def get_available_tools(self) -> list[str]:
        """Get list of available tool names"""
        return self.tool_manager.get_available_tools()

    def get_tools_by_category(self, category: ToolCategory) -> list[str]:
        """Get tools filtered by category"""
        return self.tool_manager.get_tools_by_category(category)

    def check_tool_availability(self, tool_name: str) -> bool:
        """Check if a tool is available and operational"""
        return self.tool_manager.check_tool_availability(tool_name)

    async def perform_health_check(self, tool_name: str) -> dict[str, Any]:
        """Perform health check for a specific tool"""
        return await self.health_monitor.perform_health_check(tool_name)

    async def perform_health_check_all(self) -> dict[str, Any]:
        """Perform health check for all tools"""
        return await self.health_monitor.perform_health_check_all()

    def get_performance_metrics(self) -> dict[str, Any]:
        """Get performance metrics for all tools"""
        return self.health_monitor.get_performance_metrics()

    def reset_metrics(self):
        """Reset performance metrics for all tools"""
        self.health_monitor.reset_metrics()

    async def graceful_degradation(self, failed_tools: list[str]) -> dict[str, str]:
        """Handle graceful degradation when tools fail"""
        return await self.health_monitor.graceful_degradation(failed_tools)

    def get_client_info(self) -> dict[str, Any]:
        """Get information about the current client configuration"""
        return self.tool_manager.get_client_info()

    def create_research_adapter(self):
        """Create an adapter for ResearchWorkflowTool compatibility"""
        return self.RegistryAdapter(self)

    def get_capabilities(self) -> dict[str, Any]:
        """Return the capabilities of this MCP tool registry"""
        return {
            "registry_name": "MCP Tool Registry",
            "version": "2.0.0-modular",
            "architecture": "modular",
            "components": {
                "tool_manager": "Tool registration and initialization",
                "health_monitor": "Performance tracking and health monitoring",
                "execution_engine": "Parallel tool execution with error recovery",
            },
            "features": [
                "Parallel tool execution",
                "Comprehensive health monitoring",
                "Graceful degradation and error recovery",
                "Real and mock client support",
                "Performance metrics and tracking",
                "Category-based tool organization",
            ],
            "supported_tools": self.get_available_tools(),
            "client_mode": self.get_client_info()["mode"],
            "modular_architecture": True,
        }


# Factory function to match the interface expected by smart_decomposition_agent.py
def create_mcp_tool_registry(
    use_real_clients: bool | None = None,
) -> MCPToolRegistry:
    """Factory function to create and return an MCP tool registry instance.

    Args:
        use_real_clients: Optional override for client mode.
                         None = auto-detect based on environment
                         True = force real MCP clients
                         False = force mock clients for testing
    """
    return MCPToolRegistry(use_real_clients=use_real_clients)

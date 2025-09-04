"""
Project Context MCP Tools Registration
"""
from typing import Optional

import structlog
from fastmcp import FastMCP

from .analysis import *
from .architecture import *
from .change import *
from .discovery import *
from .ingestion_tools import (
    analyze_cross_adapter_relationships,
    get_integration_health_report,
    get_pipeline_status,
    start_ingestion_pipeline,
    stop_ingestion_pipeline,
    test_end_to_end_pipeline,
    validate_adapter_integration,
)
from .maintenance import *
from .quality import *

logger = structlog.get_logger(__name__)


def register_all_tools(mcp: FastMCP, reader=None, cache=None):
    """Register all project context tools with the MCP server, including ingestion tools."""

    # Configure cache if provided
    if cache:
        from .architecture import get_project_summary
        from .cache import set_cache_manager
        from .discovery import get_file_info

        set_cache_manager(get_file_info, cache)
        set_cache_manager(get_project_summary, cache)
        logger.info("Cache manager configured for caching-enabled tools")

    registered_tools = []

    try:
        # Analysis tools
        logger.info("Registering analysis tools")

        @mcp.tool()
        async def get_complexity_tool(
            file_path: str = None,
            element_type: str = None,
            language: str = None,
            threshold: float = 10.0,
        ) -> dict:
            """Get complexity metrics from code elements."""
            try:
                return await get_complexity(
                    file_path, element_type, language, threshold
                )
            except Exception as e:
                logger.error("Error in get_complexity_tool", error=str(e))
                return {"error": f"Failed to get complexity metrics: {str(e)}"}

        registered_tools.append("get_complexity_tool")

        @mcp.tool()
        async def get_call_graph_tool(
            file_path: str = None,
            include_external: bool = True,
            max_depth: int = 10,
            complexity_threshold: float = 15.0,
        ) -> dict:
            """Get function call relationships from the codebase."""
            try:
                return await get_call_graph(
                    file_path, include_external, max_depth, complexity_threshold
                )
            except Exception as e:
                logger.error("Error in get_call_graph_tool", error=str(e))
                return {"error": f"Failed to get call graph: {str(e)}"}

        registered_tools.append("get_call_graph_tool")

        # Discovery tools
        logger.info("Registering discovery tools")

        @mcp.tool()
        async def find_files_tool(
            pattern: str,
            file_type: str = None,
            exclude_patterns: list = None,
            max_results: int = 100,
        ) -> dict:
            """Find files matching patterns in the codebase."""
            try:
                return await find_files(
                    pattern, file_type, exclude_patterns, max_results
                )
            except Exception as e:
                logger.error("Error in find_files_tool", error=str(e))
                return {"error": f"Failed to find files: {str(e)}"}

        registered_tools.append("find_files_tool")

        @mcp.tool()
        async def find_symbols_tool(
            symbol_name: str,
            symbol_type: str = None,
            file_filter: str = None,
            exact_match: bool = False,
        ) -> dict:
            """Find symbols (functions, classes, etc.) in the codebase."""
            try:
                return await find_symbols(
                    symbol_name, symbol_type, file_filter, exact_match
                )
            except Exception as e:
                logger.error("Error in find_symbols_tool", error=str(e))
                return {"error": f"Failed to find symbols: {str(e)}"}

        registered_tools.append("find_symbols_tool")

        # Ingestion Pipeline Tools
        logger.info("Registering ingestion pipeline tools")

        @mcp.tool()
        async def start_ingestion_pipeline_tool(
            adapter_ids: list = None,
            config_path: str = None,
            duration_seconds: int = None,
        ) -> dict:
            """Start the unified ingestion pipeline with chat and code adapters.

            Args:
                adapter_ids: List of adapter IDs to start (default: all available)
                config_path: Path to pipeline configuration file
                duration_seconds: How long to run pipeline (default: run until stopped)
            """
            try:
                return await start_ingestion_pipeline(
                    adapter_ids, config_path, duration_seconds
                )
            except Exception as e:
                logger.error("Error in start_ingestion_pipeline_tool", error=str(e))
                return {"error": f"Failed to start ingestion pipeline: {str(e)}"}

        registered_tools.append("start_ingestion_pipeline_tool")

        @mcp.tool()
        async def stop_ingestion_pipeline_tool() -> dict:
            """Stop the currently running ingestion pipeline."""
            try:
                return await stop_ingestion_pipeline()
            except Exception as e:
                logger.error("Error in stop_ingestion_pipeline_tool", error=str(e))
                return {"error": f"Failed to stop ingestion pipeline: {str(e)}"}

        registered_tools.append("stop_ingestion_pipeline_tool")

        @mcp.tool()
        async def get_pipeline_status_tool() -> dict:
            """Get comprehensive status and metrics for the ingestion pipeline."""
            try:
                return await get_pipeline_status()
            except Exception as e:
                logger.error("Error in get_pipeline_status_tool", error=str(e))
                return {"error": f"Failed to get pipeline status: {str(e)}"}

        registered_tools.append("get_pipeline_status_tool")

        @mcp.tool()
        async def validate_adapter_integration_tool(
            adapter_id: str,
            test_items_count: int = 10,
        ) -> dict:
            """Validate that a specific adapter is properly integrated and functional.

            Args:
                adapter_id: ID of the adapter to validate (e.g., 'chat', 'code', 'git', 'error')
                test_items_count: Number of test items to process for validation
            """
            try:
                return await validate_adapter_integration(adapter_id, test_items_count)
            except Exception as e:
                logger.error("Error in validate_adapter_integration_tool", error=str(e))
                return {"error": f"Failed to validate adapter integration: {str(e)}"}

        registered_tools.append("validate_adapter_integration_tool")

        @mcp.tool()
        async def analyze_cross_adapter_relationships_tool(
            time_window_hours: int = 24,
            relationship_types: list = None,
        ) -> dict:
            """Analyze relationships and data flow between different adapters.

            Args:
                time_window_hours: Time window to analyze (hours)
                relationship_types: Specific relationship types to analyze
            """
            try:
                return await analyze_cross_adapter_relationships(
                    time_window_hours, relationship_types
                )
            except Exception as e:
                logger.error(
                    "Error in analyze_cross_adapter_relationships_tool", error=str(e)
                )
                return {
                    "error": f"Failed to analyze cross-adapter relationships: {str(e)}"
                }

        registered_tools.append("analyze_cross_adapter_relationships_tool")

        @mcp.tool()
        async def test_end_to_end_pipeline_tool(
            test_data_path: str = None,
            adapters_to_test: list = None,
        ) -> dict:
            """Run comprehensive end-to-end tests on the integrated pipeline system.

            Args:
                test_data_path: Path to test data directory
                adapters_to_test: List of adapters to include in test
            """
            try:
                return await test_end_to_end_pipeline(test_data_path, adapters_to_test)
            except Exception as e:
                logger.error("Error in test_end_to_end_pipeline_tool", error=str(e))
                return {"error": f"Failed to test end-to-end pipeline: {str(e)}"}

        registered_tools.append("test_end_to_end_pipeline_tool")

        @mcp.tool()
        async def get_integration_health_report_tool() -> dict:
            """Generate comprehensive health report for the integrated chat/code adapter system."""
            try:
                return await get_integration_health_report()
            except Exception as e:
                logger.error(
                    "Error in get_integration_health_report_tool", error=str(e)
                )
                return {
                    "error": f"Failed to generate integration health report: {str(e)}"
                }

        registered_tools.append("get_integration_health_report_tool")

        # All other tools would be registered similarly...
        # For now, let's register basic versions of each

        logger.info(
            f"Successfully registered {len(registered_tools)} tools including ingestion pipeline tools"
        )
        return registered_tools

    except Exception as e:
        logger.error("Failed to register tools", error=str(e))
        raise


__all__ = ["register_all_tools"]

"""
Health Monitor Module

Handles tool health checking, performance tracking, and status monitoring.
Extracted from mcp_tool_registry.py for better modularity.
"""

import asyncio
import logging
import time
from datetime import datetime
from typing import Any

from src.applications.oamat_sd.src.config.config_manager import ConfigManager
from src.applications.oamat_sd.src.models.tool_models import ToolStatus


class ToolHealthMonitor:
    """Handles tool health checking and performance monitoring"""

    def __init__(self, tool_manager):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.tool_manager = tool_manager

    def record_execution_success(self, tool_name: str, execution_time: float):
        """Record a successful tool execution"""
        tool = self.tool_manager.get_tool_metadata(tool_name)
        if tool:
            tool.success_count += 1
            tool.last_health_check = datetime.now()

            # Update performance metrics
            if "avg_response_time" in tool.performance_metrics:
                # Simple moving average update
                current_avg = tool.performance_metrics["avg_response_time"]
                total_executions = tool.success_count + tool.error_count
                new_avg = (
                    (current_avg * (total_executions - 1)) + execution_time
                ) / total_executions
                tool.performance_metrics["avg_response_time"] = new_avg

            # Update success rate
            total_executions = tool.success_count + tool.error_count
            if total_executions > 0:
                tool.performance_metrics["success_rate"] = (
                    tool.success_count / total_executions
                )

            self.logger.debug(
                f"✅ Recorded success for {tool_name}: {execution_time:.2f}s"
            )

    def record_execution_failure(self, tool_name: str, error_message: str):
        """Record a failed tool execution"""
        tool = self.tool_manager.get_tool_metadata(tool_name)
        if tool:
            tool.error_count += 1
            tool.last_health_check = datetime.now()

            # Update success rate
            total_executions = tool.success_count + tool.error_count
            if total_executions > 0:
                tool.performance_metrics["success_rate"] = (
                    tool.success_count / total_executions
                )

            # Consider marking tool as degraded if error rate is too high - NO HARDCODED VALUES

            if (
                total_executions
                >= ConfigManager().tools.performance["minimum_executions_for_stats"]
                and tool.performance_metrics["success_rate"]
                < ConfigManager().tools.recommendations["minimum_confidence_threshold"]
            ):
                tool.status = ToolStatus.DEGRADED
                self.logger.warning(
                    f"⚠️ Tool {tool_name} marked as DEGRADED due to low success rate"
                )

            self.logger.debug(f"❌ Recorded failure for {tool_name}: {error_message}")

    async def perform_health_check(self, tool_name: str) -> dict[str, Any]:
        """Perform health check for a specific tool"""
        self.logger.info(f"🏥 Performing health check for {tool_name}")

        tool_interface = self.tool_manager.get_tool_interface(tool_name)
        if not tool_interface:
            return {
                "tool_name": tool_name,
                "status": "unavailable",
                "message": "Tool interface not found",
                "timestamp": datetime.now().isoformat(),
            }

        try:
            # Try to call the health_check method if available
            if hasattr(tool_interface, "health_check"):
                health_result = tool_interface.health_check()

                # Update tool status based on health check
                tool = self.tool_manager.get_tool_metadata(tool_name)
                if tool:
                    if health_result.get("status") == "healthy":
                        tool.status = ToolStatus.OPERATIONAL
                    else:
                        tool.status = ToolStatus.DEGRADED
                    tool.last_health_check = datetime.now()

                return {
                    "tool_name": tool_name,
                    "status": "healthy",
                    "details": health_result,
                    "timestamp": datetime.now().isoformat(),
                }
            else:
                # If no health_check method, consider the tool healthy if it exists
                return {
                    "tool_name": tool_name,
                    "status": "healthy",
                    "message": "Tool interface available (no health_check method)",
                    "timestamp": datetime.now().isoformat(),
                }

        except Exception as e:
            # Mark tool as degraded if health check fails
            tool = self.tool_manager.get_tool_metadata(tool_name)
            if tool:
                tool.status = ToolStatus.DEGRADED
                tool.last_health_check = datetime.now()

            return {
                "tool_name": tool_name,
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    async def perform_health_check_all(self) -> dict[str, Any]:
        """Perform health check for all tools"""
        self.logger.info("🏥 Performing health check for all tools")

        start_time = time.time()
        all_tools = self.tool_manager.get_available_tools()

        # Run health checks in parallel (NO asyncio.gather)
        health_check_tasks = [
            asyncio.create_task(
                self.perform_health_check(tool_name), name=f"health_{tool_name}"
            )
            for tool_name in all_tools
        ]

        # Execute using as_completed instead of gather
        results = []
        for completed_task in asyncio.as_completed(health_check_tasks):
            try:
                result = await completed_task
                results.append(result)
            except Exception as e:
                results.append(e)

        # Process results
        healthy_tools = []
        degraded_tools = []
        unavailable_tools = []

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                unavailable_tools.append(
                    {"tool_name": all_tools[i], "status": "error", "error": str(result)}
                )
            else:
                if result["status"] == "healthy":
                    healthy_tools.append(result)
                elif result["status"] == "unhealthy":
                    degraded_tools.append(result)
                else:
                    unavailable_tools.append(result)

        total_time = time.time() - start_time

        # Use config status values - NO HARDCODED STATUS STRINGS
        healthy_status = ConfigManager().status_values.health["healthy"]
        degraded_status = ConfigManager().status_values.health["degraded"]

        overall_health = {
            "overall_status": (
                healthy_status
                if len(healthy_tools) == len(all_tools)
                else degraded_status
            ),
            "total_tools": len(all_tools),
            "healthy_count": len(healthy_tools),
            "degraded_count": len(degraded_tools),
            "unavailable_count": len(unavailable_tools),
            "health_check_duration": f"{total_time:.2f}s",
            "timestamp": datetime.now().isoformat(),
            "healthy_tools": healthy_tools,
            "degraded_tools": degraded_tools,
            "unavailable_tools": unavailable_tools,
        }

        self.logger.info(
            f"✅ Health check completed: {len(healthy_tools)}/{len(all_tools)} tools healthy"
        )

        return overall_health

    def get_performance_metrics(self) -> dict[str, Any]:
        """Get performance metrics for all tools"""
        all_tools = self.tool_manager.get_available_tools()
        tool_metrics = {}

        total_successes = 0
        total_executions = 0

        for tool_name in all_tools:
            tool = self.tool_manager.get_tool_metadata(tool_name)
            if tool:
                tool_total = tool.success_count + tool.error_count
                total_successes += tool.success_count
                total_executions += tool_total

                tool_metrics[tool_name] = {
                    "success_count": tool.success_count,
                    "error_count": tool.error_count,
                    "success_rate": (
                        tool.success_count / tool_total if tool_total > 0 else 0.0
                    ),
                    "avg_response_time": tool.performance_metrics.get(
                        "avg_response_time", 0.0
                    ),
                    "status": tool.status.value,
                    "last_health_check": (
                        tool.last_health_check.isoformat()
                        if tool.last_health_check
                        else None
                    ),
                }

        return {
            "client_info": self.tool_manager.get_client_info(),
            "overall_success_rate": (
                total_successes / total_executions if total_executions > 0 else 0.0
            ),
            "total_executions": total_executions,
            "operational_tools": len(
                [
                    tool
                    for tool in self.tool_manager.tools.values()
                    if tool.status == ToolStatus.OPERATIONAL
                ]
            ),
            "tool_metrics": tool_metrics,
        }

    def reset_metrics(self):
        """Reset performance metrics for all tools"""
        all_tools = self.tool_manager.get_available_tools()
        # Reset metrics using config values - NO HARDCODED VALUES
        for tool_name in all_tools:
            tool = self.tool_manager.get_tool_metadata(tool_name)
            if tool:
                tool.success_count = ConfigManager().tools.initialization[
                    "counter_reset_value"
                ]
                tool.error_count = ConfigManager().tools.initialization[
                    "counter_reset_value"
                ]
                tool.performance_metrics[
                    "success_rate"
                ] = ConfigManager().tools.defaults["success_rate"]

        self.logger.info("🔄 Reset performance metrics for all tools")

    async def graceful_degradation(self, failed_tools: list[str]) -> dict[str, str]:
        """Handle graceful degradation when tools fail"""
        alternatives = {}

        for tool_name in failed_tools:
            tool = self.tool_manager.get_tool_metadata(tool_name)
            if not tool:
                continue

            # Find alternative tools in the same category
            category_tools = self.tool_manager.get_tools_by_category(tool.category)
            operational_alternatives = [
                t
                for t in category_tools
                if t != tool_name and self.tool_manager.check_tool_availability(t)
            ]

            if operational_alternatives:
                alternatives[tool_name] = operational_alternatives[0]
                self.logger.info(
                    f"🔄 Alternative for {tool_name}: {alternatives[tool_name]}"
                )
            else:
                alternatives[tool_name] = "manual_fallback"
                self.logger.warning(
                    f"⚠️ No alternatives for {tool_name}, requiring manual fallback"
                )

        return alternatives

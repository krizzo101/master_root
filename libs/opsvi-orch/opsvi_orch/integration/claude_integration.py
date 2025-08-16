"""
Claude Code Integration Module
-------------------------------
Integrates orchestration library with the Claude Code MCP server.

This module enhances the single Claude Code server with parallel and
recursive execution capabilities using LangGraph orchestration.

Configuration flags control which features are enabled:
- enable_parallel: Enable parallel batch spawning
- enable_recursive: Enable recursive execution
- max_concurrent: Maximum concurrent executions
- max_depth: Maximum recursion depth
"""

from typing import List, Optional, Dict, Any, Callable
import json
import logging
import os

from ..managers.job_manager import JobManager, JobConfig
from ..executors.claude_executor import ClaudeJobExecutor, ClaudeBatchExecutor
from ..executors.recursive_executor import RecursiveClaudeExecutor, RecursionConfig

logger = logging.getLogger(__name__)


class ClaudeOrchestrationConfig:
    """Configuration for Claude Code orchestration features."""

    def __init__(
        self,
        enable_parallel: bool = True,
        enable_recursive: bool = True,
        enable_send_api: bool = True,
        max_concurrent: int = 10,
        max_depth: int = 5,
        enable_checkpointing: bool = True,
        enable_metrics: bool = True,
    ):
        """
        Initialize orchestration configuration.

        Args:
            enable_parallel: Enable parallel batch execution
            enable_recursive: Enable recursive spawning
            enable_send_api: Use LangGraph Send API
            max_concurrent: Maximum concurrent jobs
            max_depth: Maximum recursion depth
            enable_checkpointing: Enable job checkpointing
            enable_metrics: Enable performance metrics
        """
        self.enable_parallel = enable_parallel
        self.enable_recursive = enable_recursive
        self.enable_send_api = enable_send_api
        self.max_concurrent = max_concurrent
        self.max_depth = max_depth
        self.enable_checkpointing = enable_checkpointing
        self.enable_metrics = enable_metrics

    @classmethod
    def from_env(cls) -> "ClaudeOrchestrationConfig":
        """Create config from environment variables."""
        return cls(
            enable_parallel=os.getenv("CLAUDE_ENABLE_PARALLEL", "true").lower()
            == "true",
            enable_recursive=os.getenv("CLAUDE_ENABLE_RECURSIVE", "true").lower()
            == "true",
            enable_send_api=os.getenv("CLAUDE_ENABLE_SEND_API", "true").lower()
            == "true",
            max_concurrent=int(os.getenv("CLAUDE_MAX_CONCURRENT", "10")),
            max_depth=int(os.getenv("CLAUDE_MAX_DEPTH", "5")),
            enable_checkpointing=os.getenv(
                "CLAUDE_ENABLE_CHECKPOINTING", "true"
            ).lower()
            == "true",
            enable_metrics=os.getenv("CLAUDE_ENABLE_METRICS", "true").lower() == "true",
        )


class ClaudeOrchestrationIntegration:
    """
    Integration layer for Claude Code MCP server.
    Adds orchestration capabilities to the single server.
    """

    def __init__(
        self,
        config: Optional[ClaudeOrchestrationConfig] = None,
        existing_job_manager: Any = None,
        claude_token: Optional[str] = None,
    ):
        """
        Initialize orchestration integration.

        Args:
            config: Orchestration configuration
            existing_job_manager: Claude Code's existing JobManager
            claude_token: CLAUDE_CODE_TOKEN
        """
        self.config = config or ClaudeOrchestrationConfig.from_env()
        self.existing_job_manager = existing_job_manager

        # Only create components for enabled features
        if self.config.enable_parallel or self.config.enable_recursive:
            self.job_manager = JobManager(
                config=JobConfig(
                    max_concurrent=self.config.max_concurrent,
                    enable_recursion=self.config.enable_recursive,
                    enable_checkpointing=self.config.enable_checkpointing,
                )
            )

            self.claude_executor = ClaudeJobExecutor(claude_token=claude_token)

        if self.config.enable_parallel:
            self.batch_executor = ClaudeBatchExecutor(
                job_executor=self.claude_executor,
                max_concurrent=self.config.max_concurrent,
            )

        if self.config.enable_recursive:
            self.recursive_executor = RecursiveClaudeExecutor(
                config=RecursionConfig(
                    max_depth=self.config.max_depth,
                    max_children_per_parent=self.config.max_concurrent,
                )
            )

    def create_orchestration_tools(self) -> Dict[str, Callable]:
        """
        Create MCP tools based on enabled features.

        Returns:
            Dict of tool_name -> tool_function
        """
        tools = {}

        # Always include the base tool
        tools["claude_run"] = self._create_claude_run_tool()
        tools["claude_run_async"] = self._create_claude_run_async_tool()

        # Add parallel tools if enabled
        if self.config.enable_parallel:
            tools["claude_run_batch"] = self._create_batch_tool()
            tools["claude_collect_batch"] = self._create_collect_tool()

        # Add recursive tools if enabled
        if self.config.enable_recursive:
            tools["claude_spawn_recursive"] = self._create_recursive_tool()

        # Add monitoring tools if metrics enabled
        if self.config.enable_metrics:
            tools["claude_metrics"] = self._create_metrics_tool()

        return tools

    def _create_claude_run_tool(self) -> Callable:
        """Create enhanced claude_run tool."""

        async def claude_run(
            task: str,
            cwd: Optional[str] = None,
            outputFormat: str = "json",
            permissionMode: str = "bypassPermissions",
            verbose: bool = False,
            parentJobId: Optional[str] = None,
        ) -> str:
            """
            Enhanced claude_run with orchestration support.
            Backward compatible with original tool.
            """
            # If parallel is disabled, fall back to original behavior
            if not self.config.enable_parallel:
                # Would call original implementation
                return json.dumps({"message": "Original claude_run behavior"})

            # Use orchestrated execution
            result = await self.claude_executor.execute_claude_job(
                task=task,
                parent_job_id=parentJobId,
                cwd=cwd,
                output_format=outputFormat,
            )

            return json.dumps(result[1], indent=2)

        return claude_run

    def _create_claude_run_async_tool(self) -> Callable:
        """Create enhanced claude_run_async tool."""

        async def claude_run_async(
            task: str,
            cwd: Optional[str] = None,
            outputFormat: str = "json",
            permissionMode: str = "bypassPermissions",
            verbose: bool = False,
            parentJobId: Optional[str] = None,
        ) -> str:
            """
            Enhanced claude_run_async with orchestration support.
            Backward compatible with original tool.
            """
            # Implementation similar to claude_run but async
            return json.dumps(
                {"jobId": f"job_{os.urandom(4).hex()}", "status": "started"}, indent=2
            )

        return claude_run_async

    def _create_batch_tool(self) -> Callable:
        """Create batch execution tool."""

        async def claude_run_batch(
            tasks: List[str],
            parentJobId: Optional[str] = None,
            cwd: Optional[str] = None,
            outputFormat: str = "json",
            permissionMode: str = "bypassPermissions",
            verbose: bool = False,
        ) -> str:
            """
            Execute multiple tasks in parallel.
            Only available when parallel execution is enabled.

            Args:
                tasks: List of task descriptions
                parentJobId: Parent job ID for recursion
                cwd: Working directory
                outputFormat: Output format
                permissionMode: Permission mode
                verbose: Verbose output

            Returns:
                JSON with job IDs and batch info
            """
            if not self.config.enable_parallel:
                return json.dumps(
                    {
                        "error": "Parallel execution is disabled",
                        "hint": "Set CLAUDE_ENABLE_PARALLEL=true",
                    },
                    indent=2,
                )

            batch_result = await self.job_manager.execute_batch_async(
                tasks=tasks, parent_job_id=parentJobId, cwd=cwd
            )

            return json.dumps(
                {
                    "jobIds": batch_result.job_ids,
                    "batchId": batch_result.batch_id,
                    "count": batch_result.total_jobs,
                    "status": batch_result.status,
                    "parallel": True,
                    "maxConcurrent": self.config.max_concurrent,
                },
                indent=2,
            )

        return claude_run_batch

    def _create_collect_tool(self) -> Callable:
        """Create batch collection tool."""

        async def claude_collect_batch(
            batchId: Optional[str] = None,
            jobIds: Optional[List[str]] = None,
            wait: bool = True,
            timeout: int = 300,
        ) -> str:
            """
            Collect results from parallel execution.
            """
            if not self.config.enable_parallel:
                return json.dumps({"error": "Parallel execution is disabled"}, indent=2)

            # Implementation here
            return json.dumps({"batchId": batchId, "results": []}, indent=2)

        return claude_collect_batch

    def _create_recursive_tool(self) -> Callable:
        """Create recursive spawning tool."""

        async def claude_spawn_recursive(
            task: str,
            maxDepth: Optional[int] = None,
            childrenPerLevel: int = 3,
            parentJobId: Optional[str] = None,
        ) -> str:
            """
            Spawn recursive tree of Claude instances.
            Only available when recursive execution is enabled.
            """
            if not self.config.enable_recursive:
                return json.dumps(
                    {
                        "error": "Recursive execution is disabled",
                        "hint": "Set CLAUDE_ENABLE_RECURSIVE=true",
                    },
                    indent=2,
                )

            # Use configured max depth or override
            depth = maxDepth or self.config.max_depth

            result = await self.recursive_executor.execute_claude_recursive(
                task=task, parent_job_id=parentJobId
            )

            return json.dumps(
                {
                    "jobId": result.job_id,
                    "depth": result.depth,
                    "childrenSpawned": result.children_spawned,
                    "totalDescendants": result.total_descendants,
                },
                indent=2,
            )

        return claude_spawn_recursive

    def _create_metrics_tool(self) -> Callable:
        """Create metrics reporting tool."""

        async def claude_metrics() -> str:
            """
            Get orchestration metrics.
            """
            if not self.config.enable_metrics:
                return json.dumps(
                    {
                        "error": "Metrics are disabled",
                        "hint": "Set CLAUDE_ENABLE_METRICS=true",
                    },
                    indent=2,
                )

            metrics = {
                "parallel": {
                    "enabled": self.config.enable_parallel,
                    "maxConcurrent": self.config.max_concurrent,
                },
                "recursive": {
                    "enabled": self.config.enable_recursive,
                    "maxDepth": self.config.max_depth,
                },
                "sendApi": {"enabled": self.config.enable_send_api},
            }

            if hasattr(self, "claude_executor"):
                metrics["execution"] = {
                    "totalSpawned": self.claude_executor.metrics.total_spawned,
                    "successful": self.claude_executor.metrics.successful,
                    "failed": self.claude_executor.metrics.failed,
                    "averageTimeMs": self.claude_executor.metrics.average_time_ms,
                }

            return json.dumps(metrics, indent=2)

        return claude_metrics


def enhance_claude_code_server(
    mcp_server: Any,
    job_manager: Any = None,
    config: Optional[ClaudeOrchestrationConfig] = None,
) -> None:
    """
    Enhance the Claude Code server with orchestration capabilities.

    This function should be called from the single claude_code server
    to add orchestration features based on configuration.

    Args:
        mcp_server: The MCP server instance
        job_manager: The server's JobManager instance
        config: Orchestration configuration (uses env if not provided)

    Example usage in claude_code server:

    ```python
    # In libs/opsvi-mcp/opsvi_mcp/servers/claude_code/server.py

    from opsvi_orch.integration.claude_integration import enhance_claude_code_server

    # After basic server setup
    if os.getenv("CLAUDE_ENABLE_ORCHESTRATION", "false").lower() == "true":
        enhance_claude_code_server(mcp, job_manager)
    ```
    """
    config = config or ClaudeOrchestrationConfig.from_env()

    logger.info(f"Enhancing Claude Code server with orchestration:")
    logger.info(f"  - Parallel execution: {config.enable_parallel}")
    logger.info(f"  - Recursive execution: {config.enable_recursive}")
    logger.info(f"  - Send API: {config.enable_send_api}")

    integration = ClaudeOrchestrationIntegration(
        config=config,
        existing_job_manager=job_manager,
        claude_token=os.environ.get("CLAUDE_CODE_TOKEN"),
    )

    tools = integration.create_orchestration_tools()

    for name, func in tools.items():
        if hasattr(mcp_server, "tool"):
            mcp_server.tool()(func)
            logger.info(f"  - Added tool: {name}")

    logger.info(f"Claude Code server enhanced with {len(tools)} orchestration tools")

"""
Claude Executor
---------------
Specialized executors for Claude Code integration.
Handles actual Claude process spawning and management.

Integrates with V1 server for:
- Job creation and tracking
- Process spawning
- Result collection
"""

from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import logging
import subprocess
import json
import os
import uuid

from ..patterns.send_api import SendBuilder, ParallelSendExecutor
from ..patterns.recursive_orch import RecursionContext

logger = logging.getLogger(__name__)


@dataclass
class ClaudeExecutionMetrics:
    """Metrics for Claude execution."""

    total_spawned: int = 0
    successful: int = 0
    failed: int = 0
    total_time_ms: float = 0
    average_time_ms: float = 0
    recursion_depths: Dict[int, int] = field(default_factory=dict)


class ClaudeJobExecutor:
    """
    Executes individual Claude jobs.
    Interfaces with actual Claude CLI.
    """

    def __init__(
        self,
        claude_command: str = "claude",
        claude_token: Optional[str] = None,
        base_timeout_ms: int = 30000,
    ):
        """
        Initialize Claude job executor.

        Args:
            claude_command: Claude CLI command path
            claude_token: Optional CLAUDE_CODE_TOKEN
            base_timeout_ms: Base timeout for execution
        """
        self.claude_command = claude_command
        self.claude_token = claude_token or os.environ.get("CLAUDE_CODE_TOKEN")
        self.base_timeout_ms = base_timeout_ms
        self.metrics = ClaudeExecutionMetrics()

    def prepare_claude_command(
        self,
        task: str,
        output_format: str = "json",
        permission_mode: str = "bypassPermissions",
        verbose: bool = False,
        mcp_config: Optional[str] = None,
    ) -> List[str]:
        """
        Prepare Claude CLI command.

        Args:
            task: Task description
            output_format: Output format (json, text)
            permission_mode: Permission mode
            verbose: Enable verbose output
            mcp_config: Optional MCP configuration path

        Returns:
            Command list for subprocess
        """
        cmd = [self.claude_command]

        # Add MCP config if provided
        if mcp_config:
            cmd.extend(["--mcp-config", mcp_config])
            cmd.append("--strict-mcp-config")

        # Always skip permissions for automation
        cmd.append("--dangerously-skip-permissions")

        # Output format
        if output_format in ("json", "stream-json"):
            cmd.extend(["--output-format", output_format])

        # Verbose flag
        if verbose:
            cmd.append("--verbose")

        # Add task
        cmd.extend(["-p", task])

        return cmd

    def prepare_environment(
        self,
        job_id: str,
        parent_job_id: Optional[str] = None,
        recursion_context: Optional[RecursionContext] = None,
    ) -> Dict[str, str]:
        """
        Prepare environment variables for Claude execution.

        CRITICAL: Nullifies ANTHROPIC_API_KEY to force token auth.

        Args:
            job_id: Job identifier
            parent_job_id: Parent job ID for recursion
            recursion_context: Recursion context

        Returns:
            Environment variables dict
        """
        env = os.environ.copy()

        # Set Claude token
        if self.claude_token:
            env["CLAUDE_CODE_TOKEN"] = self.claude_token

        # CRITICAL: Remove ANTHROPIC_API_KEY to prevent API usage
        if "ANTHROPIC_API_KEY" in env:
            del env["ANTHROPIC_API_KEY"]
        env["ANTHROPIC_API_KEY"] = ""  # Explicitly set to empty

        # Add job tracking
        env["CLAUDE_JOB_ID"] = job_id
        if parent_job_id:
            env["CLAUDE_PARENT_JOB_ID"] = parent_job_id

        # Add recursion context
        if recursion_context:
            env["CLAUDE_RECURSION_DEPTH"] = str(recursion_context.depth)
            env["CLAUDE_ROOT_JOB_ID"] = recursion_context.root_job_id

        # Clean other conflicting variables
        for key in list(env.keys()):
            if key.startswith("ANTHROPIC_") and key != "ANTHROPIC_API_KEY":
                del env[key]

        return env

    async def execute_claude_job(
        self,
        task: str,
        job_id: Optional[str] = None,
        parent_job_id: Optional[str] = None,
        cwd: Optional[str] = None,
        output_format: str = "json",
        permission_mode: str = "bypassPermissions",
        timeout_ms: Optional[int] = None,
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Execute a single Claude job.

        Args:
            task: Task to execute
            job_id: Optional job ID
            parent_job_id: Parent job ID
            cwd: Working directory
            output_format: Output format
            permission_mode: Permission mode
            timeout_ms: Timeout override

        Returns:
            Tuple of (success, result_dict)
        """
        job_id = job_id or f"claude_{uuid.uuid4().hex[:8]}"
        start_time = datetime.now()

        try:
            # Prepare command
            cmd = self.prepare_claude_command(
                task=task, output_format=output_format, permission_mode=permission_mode
            )

            # Prepare environment
            env = self.prepare_environment(job_id, parent_job_id)

            # Execute
            logger.info(f"Spawning Claude job {job_id}: {task[:50]}...")

            process = subprocess.Popen(
                cmd,
                cwd=cwd,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                text=True,
            )

            # Wait for completion with timeout
            timeout_sec = (timeout_ms or self.base_timeout_ms) / 1000
            stdout, stderr = process.communicate(timeout=timeout_sec)

            # Parse result
            success = process.returncode == 0
            execution_time = (datetime.now() - start_time).total_seconds() * 1000

            # Update metrics
            self.metrics.total_spawned += 1
            if success:
                self.metrics.successful += 1
            else:
                self.metrics.failed += 1
            self.metrics.total_time_ms += execution_time
            self.metrics.average_time_ms = (
                self.metrics.total_time_ms / self.metrics.total_spawned
            )

            result = {
                "job_id": job_id,
                "success": success,
                "stdout": stdout,
                "stderr": stderr,
                "return_code": process.returncode,
                "execution_time_ms": execution_time,
            }

            if output_format == "json" and stdout:
                try:
                    result["parsed_output"] = json.loads(stdout)
                except json.JSONDecodeError:
                    result["parsed_output"] = None

            logger.info(
                f"Claude job {job_id} completed: success={success}, time={execution_time:.0f}ms"
            )
            return success, result

        except subprocess.TimeoutExpired:
            logger.error(f"Claude job {job_id} timed out after {timeout_sec}s")
            return False, {
                "job_id": job_id,
                "success": False,
                "error": "timeout",
                "timeout_ms": timeout_ms or self.base_timeout_ms,
            }

        except Exception as e:
            logger.error(f"Claude job {job_id} failed: {e}")
            return False, {
                "job_id": job_id,
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__,
            }


class ClaudeBatchExecutor:
    """
    Executes batches of Claude jobs in parallel.
    Uses Send API patterns for true parallelism.
    """

    def __init__(
        self, job_executor: Optional[ClaudeJobExecutor] = None, max_concurrent: int = 10
    ):
        """
        Initialize batch executor.

        Args:
            job_executor: Claude job executor
            max_concurrent: Maximum concurrent jobs
        """
        self.job_executor = job_executor or ClaudeJobExecutor()
        self.max_concurrent = max_concurrent
        self.send_executor = ParallelSendExecutor(
            max_concurrent=max_concurrent, timeout_ms=30000
        )

    def create_claude_sends(
        self,
        tasks: List[str],
        parent_job_id: Optional[str] = None,
        recursion_depth: int = 0,
    ) -> List[Any]:
        """
        Create Send objects for parallel Claude execution.

        Args:
            tasks: List of tasks
            parent_job_id: Parent job ID
            recursion_depth: Current recursion depth

        Returns:
            List of Send objects
        """
        sends = []
        batch_id = f"batch_{datetime.now().timestamp()}"

        for i, task in enumerate(tasks):
            job_id = f"{batch_id}_{i}_{uuid.uuid4().hex[:8]}"

            send = (
                SendBuilder("claude_executor")
                .with_task(task)
                .with_custom("job_id", job_id)
                .with_batch_info(batch_id, i, len(tasks))
                .with_timeout(self.job_executor.base_timeout_ms)
                .build()
            )

            if parent_job_id:
                send = (
                    SendBuilder("claude_executor")
                    .with_task(task)
                    .with_custom("job_id", job_id)
                    .with_parent(parent_job_id, recursion_depth)
                    .with_batch_info(batch_id, i, len(tasks))
                    .build()
                )

            sends.append(send)

        logger.info(f"Created {len(sends)} Claude Send objects for batch {batch_id}")
        return sends

    async def execute_batch(
        self,
        tasks: List[str],
        parent_job_id: Optional[str] = None,
        cwd: Optional[str] = None,
        output_format: str = "json",
    ) -> Dict[str, Any]:
        """
        Execute batch of Claude tasks in parallel.

        Args:
            tasks: Tasks to execute
            parent_job_id: Parent job ID
            cwd: Working directory
            output_format: Output format

        Returns:
            Dict with batch results
        """
        batch_id = f"batch_{uuid.uuid4().hex[:8]}"
        start_time = datetime.now()

        logger.info(f"Starting Claude batch {batch_id}: {len(tasks)} tasks")

        # Create job configurations
        job_configs = []
        for i, task in enumerate(tasks):
            job_id = f"{batch_id}_{i}"
            job_configs.append(
                {
                    "job_id": job_id,
                    "task": task,
                    "parent_job_id": parent_job_id,
                    "cwd": cwd,
                    "output_format": output_format,
                }
            )

        # Execute in parallel (would use Send API in full implementation)
        results = []
        errors = []

        import asyncio

        # Create tasks for parallel execution
        async_tasks = []
        for config in job_configs:
            async_task = self.job_executor.execute_claude_job(
                task=config["task"],
                job_id=config["job_id"],
                parent_job_id=config["parent_job_id"],
                cwd=config["cwd"],
                output_format=config["output_format"],
            )
            async_tasks.append(async_task)

        # Execute all in parallel
        # NOTE: In production, this would use Send API, not gather
        task_results = await asyncio.gather(*async_tasks, return_exceptions=True)

        # Process results
        for i, result in enumerate(task_results):
            if isinstance(result, Exception):
                errors.append(
                    {"job_id": job_configs[i]["job_id"], "error": str(result)}
                )
            else:
                success, job_result = result
                if success:
                    results.append(job_result)
                else:
                    errors.append(job_result)

        execution_time = (datetime.now() - start_time).total_seconds() * 1000

        return {
            "batch_id": batch_id,
            "total_tasks": len(tasks),
            "successful": len(results),
            "failed": len(errors),
            "results": results,
            "errors": errors,
            "execution_time_ms": execution_time,
            "metrics": {
                "average_time_ms": execution_time / len(tasks) if tasks else 0,
                "success_rate": len(results) / len(tasks) if tasks else 0,
            },
        }

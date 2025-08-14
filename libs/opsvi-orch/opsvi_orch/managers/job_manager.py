"""
Job Manager
-----------
Job management with LangGraph orchestration.
Integrates with Claude Code servers for parallel execution.

Provides:
- Batch job spawning via Send API
- Recursive job management
- Result collection and aggregation
"""

from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import logging
import json
import uuid

from ..patterns.langgraph_patterns import ParallelOrchestrationPattern
from ..patterns.send_api import ParallelSendExecutor, SendBuilder
from ..patterns.recursive_orch import RecursiveOrchestrationPattern, RecursionConfig
from ..executors.parallel_executor import ParallelExecutor, ExecutionResult

logger = logging.getLogger(__name__)


@dataclass
class JobConfig:
    """Configuration for job execution."""

    output_format: str = "json"
    permission_mode: str = "bypassPermissions"
    verbose: bool = False
    timeout_ms: int = 30000
    max_concurrent: int = 10
    enable_recursion: bool = True
    enable_checkpointing: bool = True


@dataclass
class BatchJobResult:
    """Result of batch job execution."""

    job_ids: List[str]
    parent_job_id: Optional[str]
    batch_id: str
    total_jobs: int
    status: str
    created_at: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)


class JobManager:
    """
    Job manager with LangGraph orchestration.
    Integrates with Claude Code servers for parallel recursive execution.
    """

    def __init__(
        self,
        config: Optional[JobConfig] = None,
        recursion_config: Optional[RecursionConfig] = None,
    ):
        """
        Initialize enhanced job manager.

        Args:
            config: Job execution configuration
            recursion_config: Recursion configuration
        """
        self.config = config or JobConfig()
        self.recursion_config = recursion_config or RecursionConfig()

        # Initialize orchestration components
        self.parallel_executor = ParallelExecutor()
        self.send_executor = ParallelSendExecutor(
            max_concurrent=self.config.max_concurrent, timeout_ms=self.config.timeout_ms
        )
        self.recursive_pattern = RecursiveOrchestrationPattern(self.recursion_config)

        # Job tracking
        self.active_jobs: Dict[str, Any] = {}
        self.completed_jobs: Dict[str, Any] = {}
        self.batch_jobs: Dict[str, BatchJobResult] = {}

    async def execute_batch_async(
        self,
        tasks: List[str],
        parent_job_id: Optional[str] = None,
        cwd: Optional[str] = None,
    ) -> BatchJobResult:
        """
        Execute multiple tasks in parallel using LangGraph Send API.

        This is the KEY METHOD that enables parallel spawning in V1.

        Args:
            tasks: List of task descriptions
            parent_job_id: Optional parent job ID for recursion
            cwd: Working directory

        Returns:
            BatchJobResult with all job IDs
        """
        batch_id = f"batch_{uuid.uuid4().hex[:8]}_{datetime.now().timestamp()}"

        logger.info(
            f"Starting batch execution: {len(tasks)} tasks, batch_id={batch_id}"
        )

        # Prepare job configurations
        job_configs = []
        job_ids = []

        for i, task in enumerate(tasks):
            job_id = f"{batch_id}_{i}_{uuid.uuid4().hex[:8]}"
            job_ids.append(job_id)

            job_config = {
                "job_id": job_id,
                "task": task,
                "parent_job_id": parent_job_id,
                "cwd": cwd,
                "output_format": self.config.output_format,
                "permission_mode": self.config.permission_mode,
                "verbose": self.config.verbose,
                "batch_id": batch_id,
                "batch_index": i,
                "batch_total": len(tasks),
            }

            job_configs.append(job_config)
            self.active_jobs[job_id] = job_config

        # Create Send objects for parallel execution
        if self.config.enable_recursion and parent_job_id:
            # Get parent context for recursion tracking
            parent_context = self._get_recursion_context(parent_job_id)
            sends, contexts = self.recursive_pattern.create_recursive_sends(
                "claude_executor", job_configs, parent_context  # Target node
            )
        else:
            # Non-recursive parallel sends
            sends = self.send_executor.create_parallel_sends(
                "claude_executor", job_configs, batch_id
            )

        # Store batch info
        batch_result = BatchJobResult(
            job_ids=job_ids,
            parent_job_id=parent_job_id,
            batch_id=batch_id,
            total_jobs=len(tasks),
            status="spawned",
            created_at=datetime.now(),
            metadata={
                "tasks": tasks,
                "cwd": cwd,
                "parallel": True,
                "send_count": len(sends),
            },
        )

        self.batch_jobs[batch_id] = batch_result

        # Execute through parallel executor
        # This would integrate with actual Claude spawning
        result = await self._execute_sends(sends)

        if result.success:
            batch_result.status = "running"
            logger.info(f"Batch {batch_id} spawned successfully: {len(job_ids)} jobs")
        else:
            batch_result.status = "failed"
            logger.error(f"Batch {batch_id} spawn failed: {result.errors}")

        return batch_result

    async def collect_batch_results(
        self, batch_id: str, wait: bool = True, timeout_ms: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Collect results from a batch execution.

        Args:
            batch_id: Batch identifier
            wait: Wait for all jobs to complete
            timeout_ms: Optional timeout override

        Returns:
            Dict with job results
        """
        batch = self.batch_jobs.get(batch_id)
        if not batch:
            raise ValueError(f"Batch {batch_id} not found")

        results = {}
        errors = {}

        for job_id in batch.job_ids:
            if job_id in self.completed_jobs:
                results[job_id] = self.completed_jobs[job_id]
            elif job_id in self.active_jobs:
                if wait:
                    # Would wait for completion in real implementation
                    pass
                else:
                    results[job_id] = {"status": "running"}
            else:
                errors[job_id] = {"error": "Job not found"}

        return {
            "batch_id": batch_id,
            "results": results,
            "errors": errors,
            "completed": len(results),
            "failed": len(errors),
            "total": batch.total_jobs,
        }

    def create_batch_spawn_tools(self) -> Dict[str, Callable]:
        """
        Create MCP tool functions for V1 integration.

        Returns:
            Dict of tool name -> function
        """

        async def claude_run_batch_async(
            tasks: List[str],
            parentJobId: Optional[str] = None,
            outputFormat: str = "json",
            permissionMode: str = "bypassPermissions",
        ) -> str:
            """
            MCP tool: Spawn multiple Claude instances in parallel.
            Uses LangGraph Send API for true parallelism.
            """
            # Override config for this batch
            self.config.output_format = outputFormat
            self.config.permission_mode = permissionMode

            # Execute batch
            batch_result = await self.execute_batch_async(
                tasks=tasks, parent_job_id=parentJobId
            )

            # Return MCP-compatible response
            return json.dumps(
                {
                    "jobIds": batch_result.job_ids,
                    "batchId": batch_result.batch_id,
                    "count": batch_result.total_jobs,
                    "status": batch_result.status,
                    "parentJobId": batch_result.parent_job_id,
                },
                indent=2,
            )

        async def claude_results_batch(
            jobIds: List[str], wait: bool = True, timeout: int = 300
        ) -> str:
            """
            MCP tool: Collect results from multiple jobs.
            """
            # Find batch ID from job IDs
            batch_id = None
            for bid, batch in self.batch_jobs.items():
                if set(jobIds).issubset(set(batch.job_ids)):
                    batch_id = bid
                    break

            if not batch_id:
                # Create ad-hoc batch
                batch_id = f"adhoc_{datetime.now().timestamp()}"

            results = await self.collect_batch_results(
                batch_id=batch_id, wait=wait, timeout_ms=timeout * 1000
            )

            return json.dumps(results, indent=2)

        return {
            "claude_run_batch_async": claude_run_batch_async,
            "claude_results_batch": claude_results_batch,
        }

    def _get_recursion_context(self, job_id: str) -> Optional[Any]:
        """Get recursion context for a job."""
        # Would integrate with V1's RecursionManager
        job = self.active_jobs.get(job_id) or self.completed_jobs.get(job_id)
        if job:
            return job.get("recursion_context")
        return None

    async def _execute_sends(self, sends: List[Any]) -> ExecutionResult:
        """
        Execute Send objects.
        In real implementation, this would spawn Claude processes.
        """
        # Placeholder for actual Claude spawning
        # Would integrate with V1's subprocess spawning

        return ExecutionResult(
            success=True,
            results=[{"job_id": s.state.get("job_id")} for s in sends],
            errors=[],
            execution_time_ms=100,
            tasks_completed=len(sends),
            tasks_failed=0,
        )

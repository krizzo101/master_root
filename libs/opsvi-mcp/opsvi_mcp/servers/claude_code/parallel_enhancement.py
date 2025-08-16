"""
Parallel execution enhancement for Claude Code MCP server

This module adds true parallel spawning capability at the same recursion depth.
"""

import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid
import os

from .models import ClaudeJob, JobStatus
from .parallel_logger import logger


class MultiTokenManager:
    """Manages multiple Claude tokens for true parallel execution"""

    def __init__(self):
        self.tokens = self._load_tokens()
        self.token_index = 0
        logger.log(
            "TOKEN_MANAGER",
            "init",
            f"Loaded {len(self.tokens)} tokens for parallel execution",
        )

    def _load_tokens(self) -> List[str]:
        """Load all available Claude tokens from environment"""
        tokens = []

        # Primary token
        primary = os.getenv("CLAUDE_CODE_TOKEN")
        if primary:
            tokens.append(primary)

        # Additional numbered tokens - try both formats for compatibility
        # Format 1: CLAUDE_CODE_TOKEN1, CLAUDE_CODE_TOKEN2 (as in .mcp.json)
        # Format 2: CLAUDE_CODE_TOKEN_1, CLAUDE_CODE_TOKEN_2 (legacy)
        for i in range(1, 11):  # Support up to 10 additional tokens
            # Try format without underscore first (matches .mcp.json)
            token_key = f"CLAUDE_CODE_TOKEN{i}"
            token = os.getenv(token_key)
            if token:
                tokens.append(token)
                logger.log("TOKEN_MANAGER", "load", f"Found token: {token_key}")
            else:
                # Try format with underscore (legacy support)
                token_key_alt = f"CLAUDE_CODE_TOKEN_{i}"
                token = os.getenv(token_key_alt)
                if token:
                    tokens.append(token)
                    logger.log("TOKEN_MANAGER", "load", f"Found token: {token_key_alt}")

        if not tokens:
            # Try loading from .env file if not in environment
            try:
                with open(".env", "r") as f:
                    for line in f:
                        if "=" in line and "CLAUDE_CODE_TOKEN" in line:
                            key, value = line.strip().split("=", 1)
                            value = value.strip('"').strip("'")
                            if key == "CLAUDE_CODE_TOKEN":
                                tokens.append(value)
                            elif key.startswith("CLAUDE_CODE_TOKEN"):
                                tokens.append(value)
                                logger.log(
                                    "TOKEN_MANAGER",
                                    "load",
                                    f"Found token in .env: {key}",
                                )
            except FileNotFoundError:
                pass

        if not tokens:
            raise ValueError(
                "No Claude tokens found. Set CLAUDE_CODE_TOKEN or CLAUDE_CODE_TOKEN1, etc."
            )

        return tokens

    def get_token_for_job(self, job_id: str, retry_count: int = 0) -> str:
        """Get a token for a specific job using round-robin distribution

        Args:
            job_id: The job ID
            retry_count: Number of retry attempts (used to get different token)

        Returns:
            A token from the available pool
        """
        # For retries, offset the index to get a different token
        effective_index = (self.token_index + retry_count) % len(self.tokens)
        token = self.tokens[effective_index]

        # Only advance the main index on the first attempt
        if retry_count == 0:
            self.token_index = (self.token_index + 1) % len(self.tokens)

        return token

    def has_multiple_tokens(self) -> bool:
        """Check if multiple tokens are available for parallel execution"""
        return len(self.tokens) > 1

    def get_token_count(self) -> int:
        """Get the number of available tokens"""
        return len(self.tokens)


class ParallelBatchExecutor:
    """Handles parallel execution of multiple Claude jobs at the same depth"""

    def __init__(self, job_manager):
        self.job_manager = job_manager
        self.batch_executions = {}
        self.token_manager = MultiTokenManager()

    async def execute_batch(
        self,
        tasks: List[Dict[str, Any]],
        parent_job_id: Optional[str] = None,
        max_concurrent: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Execute multiple tasks in parallel at the same recursion depth

        Args:
            tasks: List of task configurations, each containing:
                - task: The task description
                - cwd: Working directory (optional)
                - output_format: Output format (optional)
                - permission_mode: Permission mode (optional)
            parent_job_id: Parent job ID for recursion tracking
            max_concurrent: Maximum concurrent executions (default from config)

        Returns:
            Dictionary with batch_id and individual job_ids
        """
        batch_id = str(uuid.uuid4())
        start_time = datetime.now()

        logger.log(
            "BATCH",
            batch_id,
            f"Starting parallel batch execution of {len(tasks)} tasks",
            {"parent_job_id": parent_job_id, "max_concurrent": max_concurrent},
        )

        # Create jobs for all tasks
        jobs = []
        job_ids = []

        for i, task_config in enumerate(tasks):
            try:
                # Create job with same parent (ensuring same depth)
                job = self.job_manager.create_job(
                    task=task_config.get("task", ""),
                    cwd=task_config.get("cwd"),
                    output_format=task_config.get("output_format", "json"),
                    permission_mode=task_config.get(
                        "permission_mode", "bypassPermissions"
                    ),
                    verbose=task_config.get("verbose", False),
                    parent_job_id=parent_job_id,
                    model=task_config.get(
                        "model", "sonnet"
                    ),  # Default to sonnet for cost savings
                )
                jobs.append(job)
                job_ids.append(job.id)

                logger.log(
                    "BATCH",
                    batch_id,
                    f"Created job {i+1}/{len(tasks)}: {job.job_id}",
                    {"task_preview": task_config.get("task", "")[:100]},
                )

            except Exception as e:
                logger.log_error(
                    "BATCH",
                    f"Failed to create job {i+1}/{len(tasks)}",
                    e,
                    {"task_config": task_config},
                )
                # Continue with other jobs

        if not jobs:
            raise ValueError("No valid jobs could be created from the batch")

        # Store batch info
        self.batch_executions[batch_id] = {
            "job_ids": job_ids,
            "start_time": start_time,
            "status": "running",
            "parent_job_id": parent_job_id,
        }

        # Execute all jobs in parallel
        if max_concurrent:
            # Limited concurrent execution
            results = await self._execute_with_semaphore(jobs, max_concurrent)
        else:
            # Unlimited parallel execution (up to config limits)
            results = await asyncio.gather(
                *[self._execute_single_job(job) for job in jobs], return_exceptions=True
            )

        # Update batch status
        self.batch_executions[batch_id]["status"] = "completed"
        self.batch_executions[batch_id]["end_time"] = datetime.now()
        self.batch_executions[batch_id]["duration_ms"] = (
            datetime.now() - start_time
        ).total_seconds() * 1000

        logger.log(
            "BATCH",
            batch_id,
            f"Completed parallel batch execution in {self.batch_executions[batch_id]['duration_ms']:.2f}ms",
            {
                "successful": sum(1 for r in results if not isinstance(r, Exception)),
                "failed": sum(1 for r in results if isinstance(r, Exception)),
                "total": len(results),
            },
        )

        return {
            "batch_id": batch_id,
            "job_ids": job_ids,
            "parent_job_id": parent_job_id,
            "execution_time_ms": self.batch_executions[batch_id]["duration_ms"],
            "results_summary": {
                "total": len(results),
                "successful": sum(1 for r in results if not isinstance(r, Exception)),
                "failed": sum(1 for r in results if isinstance(r, Exception)),
            },
        }

    async def _execute_single_job(self, job: ClaudeJob, retry_count: int = 0) -> Any:
        """Execute a single job asynchronously with its own token

        Args:
            job: The job to execute
            retry_count: Number of retry attempts

        Returns:
            Job result or exception
        """
        max_retries = min(
            2, self.token_manager.get_token_count() - 1
        )  # Retry with different tokens if available

        try:
            # Get a dedicated token for this job (different token on retry)
            token = self.token_manager.get_token_for_job(job.id, retry_count)

            # Set the token in the job's environment
            if not hasattr(job, "env") or job.env is None:
                job.env = {}
            job.env["CLAUDE_CODE_TOKEN"] = token

            logger.log(
                "BATCH",
                job.id,
                f"Executing job with dedicated token (token #{self.token_manager.tokens.index(token) + 1} of {len(self.token_manager.tokens)})",
                {"retry_count": retry_count},
            )

            # Use the job manager's async execution
            await self.job_manager.execute_job_async(job)

            # Check if job failed due to token issues
            if job.status == JobStatus.FAILED and job.error:
                error_lower = job.error.lower()
                if any(
                    msg in error_lower
                    for msg in [
                        "credit balance",
                        "rate limit",
                        "unauthorized",
                        "authentication",
                    ]
                ):
                    if (
                        retry_count < max_retries
                        and self.token_manager.has_multiple_tokens()
                    ):
                        logger.log(
                            "BATCH",
                            job.id,
                            f"Token-related failure detected, retrying with different token (attempt {retry_count + 2}/{max_retries + 1})",
                            {"error": job.error[:200]},
                        )
                        # Reset job status for retry
                        job.status = JobStatus.RUNNING
                        job.error = None
                        return await self._execute_single_job(job, retry_count + 1)

            return {"job_id": job.id, "status": job.status.value}

        except Exception as e:
            if retry_count < max_retries and self.token_manager.has_multiple_tokens():
                logger.log(
                    "BATCH",
                    job.id,
                    f"Job failed, retrying with different token (attempt {retry_count + 2}/{max_retries + 1})",
                    {"error": str(e)},
                )
                return await self._execute_single_job(job, retry_count + 1)

            logger.log_error(
                "BATCH", f"Job {job.id} failed after {retry_count + 1} attempts", e
            )
            return e

    async def _execute_with_semaphore(
        self, jobs: List[ClaudeJob], max_concurrent: int
    ) -> List[Any]:
        """Execute jobs with limited concurrency using a semaphore"""
        semaphore = asyncio.Semaphore(max_concurrent)

        async def execute_with_limit(job):
            async with semaphore:
                return await self._execute_single_job(job)

        return await asyncio.gather(
            *[execute_with_limit(job) for job in jobs], return_exceptions=True
        )

    def get_batch_status(self, batch_id: str) -> Optional[Dict[str, Any]]:
        """Get the status of a batch execution"""
        return self.batch_executions.get(batch_id)

    def get_all_batches(self) -> Dict[str, Any]:
        """Get status of all batch executions"""
        return {
            "active": [
                bid
                for bid, info in self.batch_executions.items()
                if info["status"] == "running"
            ],
            "completed": [
                bid
                for bid, info in self.batch_executions.items()
                if info["status"] == "completed"
            ],
            "total": len(self.batch_executions),
            "batches": self.batch_executions,
        }


def enhance_job_manager_with_parallel(job_manager_class):
    """
    Decorator to enhance JobManager with parallel batch execution

    Usage:
        @enhance_job_manager_with_parallel
        class JobManager:
            ...
    """

    # Add batch executor as class attribute
    original_init = job_manager_class.__init__

    def new_init(self, *args, **kwargs):
        original_init(self, *args, **kwargs)
        self.batch_executor = ParallelBatchExecutor(self)

    job_manager_class.__init__ = new_init

    # Add batch execution method
    async def execute_parallel_batch(
        self,
        tasks: List[Dict[str, Any]],
        parent_job_id: Optional[str] = None,
        max_concurrent: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Execute multiple tasks in parallel"""
        return await self.batch_executor.execute_batch(
            tasks, parent_job_id, max_concurrent
        )

    job_manager_class.execute_parallel_batch = execute_parallel_batch

    # Add batch status methods
    def get_batch_status(self, batch_id: str) -> Optional[Dict[str, Any]]:
        """Get batch execution status"""
        return self.batch_executor.get_batch_status(batch_id)

    job_manager_class.get_batch_status = get_batch_status

    def get_all_batches(self) -> Dict[str, Any]:
        """Get all batch execution statuses"""
        return self.batch_executor.get_all_batches()

    job_manager_class.get_all_batches = get_all_batches

    return job_manager_class

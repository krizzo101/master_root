"""
Enhanced orchestrator with error handling and retry logic.
Created by Agent-2 during Phase 1 self-amplification.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional

from ..resources.token_pool import TokenPool
from ..resources.worktree import WorktreeManager
from .error_handler import ErrorHandler, RetryConfig

logger = logging.getLogger(__name__)


class EnhancedOrchestrator:
    """Orchestrator with Phase 1 enhancements: error handling and retry logic."""

    def __init__(
        self,
        token_pool: Optional[TokenPool] = None,
        worktree_manager: Optional[WorktreeManager] = None,
        retry_config: Optional[RetryConfig] = None,
    ):
        self.token_pool = token_pool or TokenPool()
        self.worktree_manager = worktree_manager or WorktreeManager()
        self.error_handler = ErrorHandler(retry_config or RetryConfig())
        self.execution_stats = {
            "total_tasks": 0,
            "successful_tasks": 0,
            "failed_tasks": 0,
            "retried_tasks": 0,
        }

    async def execute_task_with_retry(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a task with automatic retry on failure."""

        self.execution_stats["total_tasks"] += 1

        async def _execute():
            # Acquire resources
            token, token_idx = self.token_pool.acquire()
            worktree = self.worktree_manager.create(task["id"])

            try:
                # Simulate task execution
                logger.info(f"Executing task {task['id']} with token {token_idx}")

                # Here would be the actual task execution
                await asyncio.sleep(0.1)  # Simulate work

                # Simulate occasional failures for testing
                import random

                if random.random() < 0.1:  # 10% failure rate for demo
                    raise RuntimeError(f"Simulated failure for task {task['id']}")

                result = {
                    "task_id": task["id"],
                    "status": "completed",
                    "token_used": token_idx,
                    "worktree": str(worktree),
                }

                self.execution_stats["successful_tasks"] += 1
                return result

            finally:
                # Always cleanup
                self.worktree_manager.cleanup(task["id"], force=True)

        try:
            # Execute with retry
            result = await self.error_handler.execute_with_retry(_execute, task_id=task["id"])

            # Check if task was retried
            if task["id"] in self.error_handler.error_history:
                self.execution_stats["retried_tasks"] += 1

            return result

        except Exception as e:
            self.execution_stats["failed_tasks"] += 1
            logger.error(f"Task {task['id']} failed after all retries: {e}")

            # Handle the failure
            await self.error_handler.handle_agent_failure(
                task["id"],
                e,
                cleanup_func=lambda: self.worktree_manager.cleanup(task["id"], force=True),
            )

            return {"task_id": task["id"], "status": "failed", "error": str(e)}

    async def execute_parallel_with_retry(
        self, tasks: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Execute multiple tasks in parallel with retry logic."""

        logger.info(f"Starting parallel execution of {len(tasks)} tasks with retry support")

        # Execute all tasks with retry
        results = await asyncio.gather(
            *[self.execute_task_with_retry(task) for task in tasks],
            return_exceptions=False,  # Let error handler manage exceptions
        )

        # Log statistics
        logger.info(f"Execution complete. Stats: {self.execution_stats}")

        # Get error summary
        error_summary = self.error_handler.get_error_summary()
        if error_summary["total_errors"] > 0:
            logger.warning(f"Errors encountered: {error_summary}")

        return results

    def get_statistics(self) -> Dict[str, Any]:
        """Get execution statistics."""
        return {**self.execution_stats, "error_summary": self.error_handler.get_error_summary()}

"""
Core orchestration engine for Tetra.
"""

import asyncio
import logging
import time
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from ..ai.hybrid_controller import HybridController
from .config import get_config
from .token_pool import SecureTokenPool
from .worktree_manager import WorktreeManager

logger = logging.getLogger(__name__)


class Orchestrator:
    """Core orchestration engine managing hybrid AI execution."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize orchestrator.

        Args:
            config: Optional configuration overrides
        """
        self.config = config or get_config()
        self.sessions = {}
        self.metrics = {
            "total_tasks": 0,
            "successful_tasks": 0,
            "failed_tasks": 0,
            "total_time": 0.0,
        }

        # Initialize components
        self.token_pool = SecureTokenPool(pool_size=self.config.tokens.pool_size)

        self.worktree_manager = WorktreeManager(
            base_path=self.config.git.worktree_base,
            cleanup_on_exit=self.config.git.cleanup_on_exit,
        )

        self.ai_controller = HybridController(config=self.config)

        logger.info("Orchestrator initialized")

    async def execute(
        self,
        prompt: str,
        session_id: Optional[str] = None,
        quality_check: bool = True,
    ) -> Dict[str, Any]:
        """
        Execute a task through the orchestration pipeline.

        Args:
            prompt: Task prompt
            session_id: Optional session ID for tracking
            quality_check: Whether to run quality checks

        Returns:
            Execution result dictionary
        """
        session_id = session_id or str(uuid.uuid4())
        start_time = time.time()

        # Initialize session
        self.sessions[session_id] = {
            "id": session_id,
            "prompt": prompt,
            "status": "running",
            "start_time": datetime.now().isoformat(),
            "tasks": [],
        }

        try:
            # Analyze and execute task
            result = await self.ai_controller.execute_task(
                task_id=session_id,
                prompt=prompt,
                context={"session_id": session_id},
            )

            # Update metrics
            self.metrics["total_tasks"] += 1
            if result.get("status") in ["completed", "completed_with_fallback"]:
                self.metrics["successful_tasks"] += 1
            else:
                self.metrics["failed_tasks"] += 1

            elapsed = time.time() - start_time
            self.metrics["total_time"] += elapsed

            # Update session
            self.sessions[session_id].update(
                {
                    "status": "completed",
                    "result": result,
                    "end_time": datetime.now().isoformat(),
                    "elapsed_time": elapsed,
                }
            )

            # Quality check if requested
            if quality_check and result.get("status") == "completed":
                quality_result = await self._run_quality_checks(result)
                self.sessions[session_id]["quality"] = quality_result

            return {
                "session_id": session_id,
                "status": "success",
                "result": result,
                "elapsed_time": elapsed,
            }

        except Exception as e:
            logger.error(f"Orchestration failed for {session_id}: {e}")

            self.sessions[session_id].update(
                {
                    "status": "failed",
                    "error": str(e),
                    "end_time": datetime.now().isoformat(),
                }
            )

            self.metrics["failed_tasks"] += 1

            return {
                "session_id": session_id,
                "status": "error",
                "error": str(e),
                "elapsed_time": time.time() - start_time,
            }

    async def execute_batch(
        self,
        tasks: List[Dict[str, Any]],
        batch_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Execute multiple tasks in parallel.

        Args:
            tasks: List of task dictionaries
            batch_id: Optional batch identifier

        Returns:
            Batch execution results
        """
        batch_id = batch_id or str(uuid.uuid4())
        start_time = time.time()

        logger.info(f"Starting batch {batch_id} with {len(tasks)} tasks")

        # Execute tasks in parallel
        results = await self.ai_controller.execute_parallel_tasks(tasks)

        # Aggregate results
        successful = sum(1 for r in results if r.get("status") == "completed")
        failed = len(results) - successful

        return {
            "batch_id": batch_id,
            "total_tasks": len(tasks),
            "successful": successful,
            "failed": failed,
            "results": results,
            "elapsed_time": time.time() - start_time,
        }

    async def _run_quality_checks(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run quality checks on execution result.

        Args:
            result: Execution result

        Returns:
            Quality check results
        """
        # Placeholder for quality checks
        # In production, integrate with quality gates module
        return {
            "passed": True,
            "checks": {
                "syntax": "passed",
                "tests": "not_run",
                "linting": "not_run",
            },
        }

    def get_session_status(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get status of a session.

        Args:
            session_id: Session identifier

        Returns:
            Session status dictionary or None
        """
        return self.sessions.get(session_id)

    def get_metrics(self) -> Dict[str, Any]:
        """
        Get orchestrator metrics.

        Returns:
            Metrics dictionary
        """
        avg_time = (
            self.metrics["total_time"] / self.metrics["total_tasks"]
            if self.metrics["total_tasks"] > 0
            else 0
        )

        return {
            **self.metrics,
            "average_time": avg_time,
            "success_rate": (
                self.metrics["successful_tasks"] / self.metrics["total_tasks"]
                if self.metrics["total_tasks"] > 0
                else 0
            ),
        }

    def cleanup(self):
        """Clean up resources."""
        logger.info("Cleaning up orchestrator resources")
        self.ai_controller.cleanup()
        self.worktree_manager.cleanup_all()

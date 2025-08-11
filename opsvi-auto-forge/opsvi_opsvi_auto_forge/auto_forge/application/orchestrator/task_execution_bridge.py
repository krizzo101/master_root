"""Task execution bridge for asynchronous Celery task management."""

import asyncio
import logging
from typing import Dict, Any, Optional
from celery.result import AsyncResult
from opsvi_auto_forge.infrastructure.workers.agent_tasks import submit_agent_task

from .dependency_container import get_service, has_service

logger = logging.getLogger(__name__)


class TaskExecutionBridge:
    """Bridge between orchestration and Celery task execution.

    This class provides asynchronous task execution capabilities,
    fixing the critical issue where celery_task.get() was called
    immediately after task submission, making it synchronous.

    Enhanced to work with the new TaskExecutionEngine and dependency injection.
    """

    def __init__(self):
        self.active_tasks: Dict[str, AsyncResult] = {}
        self.task_results: Dict[str, Dict[str, Any]] = {}
        self._execution_engine = None

    @property
    def execution_engine(self):
        """Get the task execution engine with lazy loading."""
        if self._execution_engine is None:
            try:
                if has_service("task_execution_engine"):
                    engine = get_service("task_execution_engine")
                    if engine is not None:
                        self._execution_engine = engine
                    else:
                        logger.warning(
                            "Task execution engine is None in dependency container"
                        )
                else:
                    logger.warning(
                        "Task execution engine not available in dependency container"
                    )
            except Exception as e:
                logger.warning(f"Could not get task execution engine: {e}")
        return self._execution_engine

    async def submit_task_async(
        self,
        agent_type: str,
        task_execution_data: Dict[str, Any],
        project_id: str,
        run_id: str,
        node_id: str,
        timeout: int = 300,
    ) -> str:
        """Submit task asynchronously and return task ID.

        Args:
            agent_type: Type of agent to execute
            task_execution_data: Task execution data
            project_id: Project ID
            run_id: Run ID
            node_id: Node ID
            timeout: Task timeout in seconds

        Returns:
            Celery task ID
        """
        try:
            logger.info(f"Submitting async task for agent {agent_type}, node {node_id}")

            # Submit task to Celery
            celery_task = submit_agent_task(
                agent_type=agent_type,
                task_execution_data=task_execution_data,
                project_id=project_id,
                run_id=run_id,
                node_id=node_id,
            )

            # Store task reference
            self.active_tasks[node_id] = celery_task

            logger.info(f"Task submitted successfully: {celery_task.id}")
            return celery_task.id

        except Exception as e:
            logger.error(f"Failed to submit task for node {node_id}: {e}")
            raise

    async def execute_task_with_engine(
        self, task_id: str, task_type: str, parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a task using the TaskExecutionEngine.

        Args:
            task_id: Unique task identifier
            task_type: Type of task to execute
            parameters: Task execution parameters

        Returns:
            Task result data
        """
        try:
            if self.execution_engine is None:
                # Fallback to direct Celery execution
                logger.warning(
                    "Using fallback Celery execution - TaskExecutionEngine not available"
                )
                return await self._execute_task_fallback(task_id, task_type, parameters)

            # Use the TaskExecutionEngine
            result = await self.execution_engine.execute_task(
                task_id, task_type, parameters
            )

            # Convert to dictionary format for compatibility
            return {
                "task_id": str(result.task_id),
                "status": result.status.value
                if hasattr(result.status, "value")
                else str(result.status),
                "score": result.score,
                "errors": result.errors,
                "warnings": result.warnings,
                "artifacts": result.artifacts,
                "metadata": result.metadata,
            }

        except Exception as e:
            logger.error(f"Task execution failed for {task_id}: {e}")
            return {
                "task_id": task_id,
                "status": "failed",
                "score": 0.0,
                "errors": [str(e)],
                "warnings": [],
                "artifacts": [],
                "metadata": {"error": str(e)},
            }

    async def _execute_task_fallback(
        self, task_id: str, task_type: str, parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Fallback task execution using direct Celery submission."""
        try:
            # Extract parameters
            agent_type = parameters.get("agent_type", "default")
            project_id = parameters.get("project_id", "default")
            run_id = parameters.get("run_id", "default")

            # Prepare task execution data
            task_execution_data = {
                "task_id": task_id,
                "task_type": task_type,
                "agent_type": agent_type,
                "inputs": parameters.get("inputs", {}),
                "metadata": parameters.get("metadata", {}),
                "timeout_seconds": parameters.get("timeout_seconds", 300),
            }

            # Submit and wait for completion
            result = await self.submit_and_wait(
                agent_type=agent_type,
                task_data=task_execution_data,
                project_id=project_id,
                run_id=run_id,
                node_id=task_id,
                timeout=parameters.get("timeout_seconds", 300),
            )

            return result

        except Exception as e:
            logger.error(f"Fallback task execution failed for {task_id}: {e}")
            return {
                "task_id": task_id,
                "status": "failed",
                "score": 0.0,
                "errors": [str(e)],
                "warnings": [],
                "artifacts": [],
                "metadata": {"error": str(e)},
            }

    async def wait_for_task_completion(
        self, node_id: str, timeout: int = 300
    ) -> Dict[str, Any]:
        """Wait for task completion with timeout.

        Args:
            node_id: Node ID to wait for
            timeout: Timeout in seconds

        Returns:
            Task result data

        Raises:
            TimeoutError: If task doesn't complete within timeout
            Exception: If task fails
        """
        if node_id not in self.active_tasks:
            raise ValueError(f"Task {node_id} not found in active tasks")

        celery_task = self.active_tasks[node_id]

        try:
            logger.info(f"Waiting for task completion: {node_id}")

            # Wait for completion with timeout
            result = await asyncio.wait_for(
                self._wait_for_celery_result(celery_task), timeout=timeout
            )

            # Store result
            self.task_results[node_id] = result

            # Clean up
            del self.active_tasks[node_id]

            logger.info(f"Task completed successfully: {node_id}")
            return result

        except asyncio.TimeoutError:
            logger.error(f"Task {node_id} timed out after {timeout} seconds")
            del self.active_tasks[node_id]
            raise TimeoutError(f"Task {node_id} timed out")
        except Exception as e:
            logger.error(f"Task {node_id} failed: {e}")
            del self.active_tasks[node_id]
            raise

    async def _wait_for_celery_result(self, celery_task: AsyncResult) -> Dict[str, Any]:
        """Convert Celery result to async.

        Args:
            celery_task: Celery task result

        Returns:
            Task result data

        Raises:
            Exception: If task fails
        """
        while not celery_task.ready():
            await asyncio.sleep(1)

        if celery_task.successful():
            return celery_task.get()
        else:
            error_msg = f"Task failed: {celery_task.result}"
            logger.error(error_msg)
            raise Exception(error_msg)

    async def submit_and_wait(
        self,
        agent_type: str,
        task_data: Dict[str, Any],
        project_id: str,
        run_id: str,
        node_id: str,
        timeout: int = 300,
    ) -> Dict[str, Any]:
        """Submit task and wait for completion in one operation.

        This method provides a convenient way to submit a task and
        wait for its completion, while still maintaining asynchronous
        execution capabilities.

        Args:
            agent_type: Type of agent to execute
            task_data: Task execution data
            project_id: Project ID
            run_id: Run ID
            node_id: Node ID
            timeout: Task timeout in seconds

        Returns:
            Task result data
        """
        # Submit task
        task_id = await self.submit_task_async(
            agent_type=agent_type,
            task_execution_data=task_data,
            project_id=project_id,
            run_id=run_id,
            node_id=node_id,
            timeout=timeout,
        )

        # Wait for completion
        result = await self.wait_for_task_completion(node_id, timeout)

        return result

    def get_task_status(self, node_id: str) -> Optional[str]:
        """Get status of a task.

        Args:
            node_id: Node ID

        Returns:
            Task status or None if not found
        """
        if node_id not in self.active_tasks:
            return None

        celery_task = self.active_tasks[node_id]
        return celery_task.status

    def cancel_task(self, node_id: str) -> bool:
        """Cancel a running task.

        Args:
            node_id: Node ID to cancel

        Returns:
            True if cancelled successfully
        """
        if node_id not in self.active_tasks:
            return False

        celery_task = self.active_tasks[node_id]
        celery_task.revoke(terminate=True)
        del self.active_tasks[node_id]

        logger.info(f"Task cancelled: {node_id}")
        return True

    def get_active_tasks(self) -> Dict[str, str]:
        """Get all active task IDs and their statuses.

        Returns:
            Dictionary mapping node_id to task status
        """
        return {node_id: task.status for node_id, task in self.active_tasks.items()}

    def cleanup_completed_tasks(self):
        """Clean up completed tasks from memory."""
        completed_nodes = []

        for node_id, task in self.active_tasks.items():
            if task.ready():
                completed_nodes.append(node_id)

        for node_id in completed_nodes:
            del self.active_tasks[node_id]

        if completed_nodes:
            logger.info(f"Cleaned up {len(completed_nodes)} completed tasks")

    async def get_task_status_from_engine(self, task_id: str) -> Optional[str]:
        """Get task status from the TaskExecutionEngine.

        Args:
            task_id: Task ID

        Returns:
            Task status or None if not found
        """
        try:
            if self.execution_engine is None:
                return None

            status = await self.execution_engine.get_task_status(task_id)
            return status.value if hasattr(status, "value") else str(status)

        except Exception as e:
            logger.error(f"Failed to get task status for {task_id}: {e}")
            return None

    async def cancel_task_with_engine(self, task_id: str) -> bool:
        """Cancel a task using the TaskExecutionEngine.

        Args:
            task_id: Task ID to cancel

        Returns:
            True if cancelled successfully
        """
        try:
            if self.execution_engine is None:
                return False

            return await self.execution_engine.cancel_task(task_id)

        except Exception as e:
            logger.error(f"Failed to cancel task {task_id}: {e}")
            return False

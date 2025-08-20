"""Agent coordination for multi-agent workflow management."""

import asyncio
import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

from .task_execution_bridge import TaskExecutionBridge

logger = logging.getLogger(__name__)


class AgentStatus(Enum):
    """Status of agent task execution."""

    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class AgentTask:
    """Represents a task to be executed by an agent."""

    task_id: str
    agent_type: str
    inputs: Dict[str, Any]
    dependencies: List[str]
    status: AgentStatus = AgentStatus.IDLE
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    timeout: int = 300
    retries: int = 0
    max_retries: int = 3


class AgentCoordinator:
    """Coordinates multi-agent workflow execution.

    This class manages the execution of multiple agents in a coordinated
    manner, handling dependencies, parallel execution, and result collection.
    """

    def __init__(self, task_bridge: Optional[TaskExecutionBridge] = None):
        self.task_bridge = task_bridge or TaskExecutionBridge()
        self.agent_tasks: Dict[str, AgentTask] = {}
        self.execution_order: List[str] = []
        self.completed_tasks: List[str] = []
        self.failed_tasks: List[str] = []
        self.execution_phases: Dict[str, int] = {}

    def add_task(self, task: AgentTask) -> None:
        """Add a task to the coordination queue.

        Args:
            task: Agent task to add
        """
        self.agent_tasks[task.task_id] = task
        logger.info(f"Added task {task.task_id} for agent {task.agent_type}")

    def add_tasks(self, tasks: List[AgentTask]) -> None:
        """Add multiple tasks to the coordination queue.

        Args:
            tasks: List of agent tasks to add
        """
        for task in tasks:
            self.add_task(task)

    def calculate_execution_order(self) -> List[str]:
        """Calculate execution order based on dependencies.

        Uses topological sort to determine the correct execution order
        based on task dependencies.

        Returns:
            List of task IDs in execution order
        """
        logger.info("Calculating execution order...")

        # Initialize in-degree count
        in_degree = {
            task_id: len(task.dependencies)
            for task_id, task in self.agent_tasks.items()
        }

        # Find tasks with no dependencies
        queue = [task_id for task_id, degree in in_degree.items() if degree == 0]
        order = []

        while queue:
            task_id = queue.pop(0)
            order.append(task_id)

            # Update in-degree for dependent tasks
            for other_task_id, other_task in self.agent_tasks.items():
                if task_id in other_task.dependencies:
                    in_degree[other_task_id] -= 1
                    if in_degree[other_task_id] == 0:
                        queue.append(other_task_id)

        # Check for cycles
        if len(order) != len(self.agent_tasks):
            remaining = set(self.agent_tasks.keys()) - set(order)
            raise ValueError(f"Circular dependency detected in tasks: {remaining}")

        self.execution_order = order
        logger.info(f"Execution order calculated: {order}")
        return order

    def calculate_execution_phases(self) -> Dict[str, int]:
        """Calculate execution phases for parallel execution.

        Groups tasks into phases where tasks in the same phase
        can be executed in parallel.

        Returns:
            Dictionary mapping task_id to phase number
        """
        logger.info("Calculating execution phases...")

        phases = {}
        phase = 0

        for task_id in self.execution_order:
            task = self.agent_tasks[task_id]

            # Find the maximum phase of dependencies
            max_dep_phase = -1
            for dep_id in task.dependencies:
                if dep_id in phases:
                    max_dep_phase = max(max_dep_phase, phases[dep_id])

            # This task goes in the next phase after its dependencies
            phases[task_id] = max_dep_phase + 1
            phase = max(phase, max_dep_phase + 1)

        self.execution_phases = phases
        logger.info(f"Execution phases calculated: {phases}")
        return phases

    async def execute_workflow(
        self, project_id: str, run_id: str, max_parallel: int = 4
    ) -> Dict[str, Any]:
        """Execute the complete agent workflow.

        Args:
            project_id: Project ID
            run_id: Run ID
            max_parallel: Maximum number of parallel tasks

        Returns:
            Dictionary containing execution results and metrics
        """
        logger.info(
            f"Starting workflow execution for project {project_id}, run {run_id}"
        )

        # Calculate execution order and phases
        execution_order = self.calculate_execution_order()
        phases = self.calculate_execution_phases()

        if not execution_order:
            logger.warning("No tasks to execute")
            return {"status": "completed", "total_tasks": 0, "results": {}}

        # Execute tasks by phase
        results = {}
        total_tasks = len(execution_order)
        completed_tasks = 0
        failed_tasks = 0

        max_phase = max(phases.values()) if phases else 0

        for phase in range(max_phase + 1):
            phase_tasks = [
                task_id for task_id, phase_num in phases.items() if phase_num == phase
            ]

            logger.info(f"Executing phase {phase} with {len(phase_tasks)} tasks")

            # Execute tasks in parallel within the phase
            semaphore = asyncio.Semaphore(max_parallel)

            async def execute_task_with_semaphore(task_id: str):
                async with semaphore:
                    return await self._execute_single_task(task_id, project_id, run_id)

            # Create tasks for parallel execution
            tasks = [execute_task_with_semaphore(task_id) for task_id in phase_tasks]

            # Wait for all tasks in phase to complete
            phase_results = await asyncio.gather(*tasks, return_exceptions=True)

            # Process phase results
            for i, result in enumerate(phase_results):
                task_id = phase_tasks[i]

                if isinstance(result, Exception):
                    logger.error(f"Task {task_id} failed: {result}")
                    self.agent_tasks[task_id].status = AgentStatus.FAILED
                    self.agent_tasks[task_id].error = str(result)
                    self.failed_tasks.append(task_id)
                    failed_tasks += 1
                    results[task_id] = {"status": "failed", "error": str(result)}
                else:
                    self.agent_tasks[task_id].status = AgentStatus.COMPLETED
                    self.agent_tasks[task_id].result = result
                    self.completed_tasks.append(task_id)
                    completed_tasks += 1
                    results[task_id] = result

            # Check if we should continue after phase failures
            if failed_tasks > 0:
                critical_failures = sum(
                    1
                    for task_id in phase_tasks
                    if task_id in self.failed_tasks
                    and self.agent_tasks[task_id].agent_type in ["planner", "architect"]
                )

                if critical_failures > 0:
                    logger.error(
                        f"Critical failures in phase {phase}, stopping execution"
                    )
                    break

        # Prepare final results
        workflow_result = {
            "status": "completed" if failed_tasks == 0 else "failed",
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "failed_tasks": failed_tasks,
            "results": results,
            "execution_order": execution_order,
            "phases": phases,
            "completed_task_ids": self.completed_tasks,
            "failed_task_ids": self.failed_tasks,
        }

        logger.info(f"Workflow execution completed: {workflow_result['status']}")
        return workflow_result

    async def _execute_single_task(
        self, task_id: str, project_id: str, run_id: str
    ) -> Dict[str, Any]:
        """Execute a single agent task.

        Args:
            task_id: Task ID to execute
            project_id: Project ID
            run_id: Run ID

        Returns:
            Task execution result
        """
        task = self.agent_tasks[task_id]

        # Wait for dependencies
        for dep_id in task.dependencies:
            if dep_id not in self.completed_tasks:
                raise Exception(f"Dependency {dep_id} not completed for task {task_id}")

        # Update task status
        task.status = AgentStatus.RUNNING
        task.started_at = asyncio.get_event_loop().time()

        logger.info(f"Executing task {task_id} with agent {task.agent_type}")

        try:
            # Execute task using task bridge
            result = await self.task_bridge.submit_and_wait(
                agent_type=task.agent_type,
                task_data=task.inputs,
                project_id=project_id,
                run_id=run_id,
                node_id=task_id,
                timeout=task.timeout,
            )

            task.completed_at = asyncio.get_event_loop().time()
            task.result = result

            logger.info(f"Task {task_id} completed successfully")
            return result

        except Exception as e:
            task.completed_at = asyncio.get_event_loop().time()
            task.error = str(e)

            # Handle retries
            if task.retries < task.max_retries:
                task.retries += 1
                task.status = AgentStatus.IDLE
                logger.warning(
                    f"Task {task_id} failed, retrying ({task.retries}/{task.max_retries})"
                )
                return await self._execute_single_task(task_id, project_id, run_id)
            else:
                task.status = AgentStatus.FAILED
                logger.error(
                    f"Task {task_id} failed after {task.max_retries} retries: {e}"
                )
                raise

    def get_task_status(self, task_id: str) -> Optional[AgentStatus]:
        """Get status of a specific task.

        Args:
            task_id: Task ID

        Returns:
            Task status or None if not found
        """
        if task_id not in self.agent_tasks:
            return None
        return self.agent_tasks[task_id].status

    def get_workflow_status(self) -> Dict[str, Any]:
        """Get overall workflow status.

        Returns:
            Dictionary containing workflow status information
        """
        total_tasks = len(self.agent_tasks)
        completed_tasks = len(self.completed_tasks)
        failed_tasks = len(self.failed_tasks)
        running_tasks = sum(
            1
            for task in self.agent_tasks.values()
            if task.status == AgentStatus.RUNNING
        )

        return {
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "failed_tasks": failed_tasks,
            "running_tasks": running_tasks,
            "pending_tasks": total_tasks
            - completed_tasks
            - failed_tasks
            - running_tasks,
            "completion_percentage": (completed_tasks / total_tasks * 100)
            if total_tasks > 0
            else 0,
            "status": "completed"
            if completed_tasks == total_tasks
            else "running"
            if running_tasks > 0
            else "failed",
        }

    def cancel_workflow(self) -> bool:
        """Cancel all running tasks in the workflow.

        Returns:
            True if cancellation was successful
        """
        logger.info("Cancelling workflow execution")

        cancelled_count = 0
        for task_id, task in self.agent_tasks.items():
            if task.status == AgentStatus.RUNNING:
                if self.task_bridge.cancel_task(task_id):
                    task.status = AgentStatus.CANCELLED
                    cancelled_count += 1

        logger.info(f"Cancelled {cancelled_count} running tasks")
        return cancelled_count > 0

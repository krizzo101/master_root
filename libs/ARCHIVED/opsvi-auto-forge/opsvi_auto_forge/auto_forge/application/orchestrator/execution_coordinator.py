"""Execution Coordinator - Coordinate parallel and sequential task execution."""

import asyncio
import logging
from typing import Any, Dict, List
from uuid import UUID

from opsvi_auto_forge.application.orchestrator.task_execution_engine import (
    TaskExecutionEngine,
)
from opsvi_auto_forge.application.orchestrator.task_models import (
    TaskExecution,
    TaskResult,
    TaskStatus,
)

logger = logging.getLogger(__name__)


class ExecutionCoordinator:
    """Coordinate parallel and sequential task execution.

    This component provides the missing coordination functionality for
    parallel and sequential task execution identified in the gap analysis.
    """

    def __init__(self, max_concurrent_tasks: int = 10):
        """Initialize the Execution Coordinator.

        Args:
            max_concurrent_tasks: Maximum number of concurrent tasks
        """
        self.max_concurrent_tasks = max_concurrent_tasks
        self.active_tasks: Dict[UUID, asyncio.Task] = {}
        self.task_semaphore = asyncio.Semaphore(max_concurrent_tasks)

        logger.info(
            f"ExecutionCoordinator initialized with max {max_concurrent_tasks} concurrent tasks"
        )

    async def execute_parallel_tasks(
        self,
        tasks: List[TaskExecution],
        execution_engine: TaskExecutionEngine,
        context: Any,  # OrchestrationContext
    ) -> List[TaskResult]:
        """Execute multiple tasks in parallel with coordination.

        Args:
            tasks: List of tasks to execute in parallel
            execution_engine: Task execution engine
            context: Orchestration context

        Returns:
            List of task results
        """
        try:
            logger.info(f"Executing {len(tasks)} tasks in parallel")

            async def execute_single_task(task: TaskExecution) -> TaskResult:
                """Execute a single task with semaphore control."""
                async with self.task_semaphore:
                    try:
                        # Create a mock DAG node for the task
                        dag_node = self._create_dag_node_from_task(task)
                        return await execution_engine.execute_dag_node(
                            context, dag_node
                        )
                    except Exception as e:
                        logger.error(f"Task {task.id} execution failed: {e}")
                        # Return error result
                        return TaskResult(
                            task_id=task.id,
                            status=TaskStatus.FAILED,
                            score=0.0,
                            errors=[str(e)],
                            warnings=[],
                            artifacts=[],
                            metadata={"error": str(e)},
                        )

            # Execute tasks in parallel
            tasks_futures = [execute_single_task(task) for task in tasks]
            results = await asyncio.gather(*tasks_futures, return_exceptions=True)

            # Process results and handle exceptions
            processed_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    # Handle task failure
                    logger.error(f"Task {tasks[i].id} failed with exception: {result}")
                    error_result = TaskResult(
                        task_id=tasks[i].id,
                        status=TaskStatus.FAILED,
                        score=0.0,
                        errors=[str(result)],
                        warnings=[],
                        artifacts=[],
                        metadata={"exception": str(result)},
                    )
                    processed_results.append(error_result)
                else:
                    processed_results.append(result)

            logger.info(f"Completed parallel execution of {len(tasks)} tasks")
            return processed_results

        except Exception as e:
            logger.error(f"Parallel task execution failed: {e}")
            raise

    async def execute_sequential_tasks(
        self,
        tasks: List[TaskExecution],
        execution_engine: TaskExecutionEngine,
        context: Any,  # OrchestrationContext
    ) -> List[TaskResult]:
        """Execute tasks sequentially with dependency checking.

        Args:
            tasks: List of tasks to execute sequentially
            execution_engine: Task execution engine
            context: Orchestration context

        Returns:
            List of task results
        """
        try:
            logger.info(f"Executing {len(tasks)} tasks sequentially")

            results = []
            for i, task in enumerate(tasks):
                logger.info(f"Executing task {i+1}/{len(tasks)}: {task.id}")

                # Check dependencies
                if not await self._check_dependencies(task, results):
                    raise DependencyError(f"Dependencies not met for task {task.id}")

                # Execute task
                try:
                    dag_node = self._create_dag_node_from_task(task)
                    result = await execution_engine.execute_dag_node(context, dag_node)
                    results.append(result)

                    # Check for critical failures
                    if result.status == TaskStatus.FAILED and task.definition.required:
                        logger.error(
                            f"Critical task {task.id} failed, stopping sequential execution"
                        )
                        raise CriticalTaskFailure(f"Critical task {task.id} failed")

                except Exception as e:
                    logger.error(f"Task {task.id} execution failed: {e}")
                    error_result = TaskResult(
                        task_id=task.id,
                        status=TaskStatus.FAILED,
                        score=0.0,
                        errors=[str(e)],
                        warnings=[],
                        artifacts=[],
                        metadata={"error": str(e)},
                    )
                    results.append(error_result)

                    # If this is a required task, stop execution
                    if task.definition.required:
                        raise CriticalTaskFailure(f"Required task {task.id} failed")

            logger.info(f"Completed sequential execution of {len(tasks)} tasks")
            return results

        except Exception as e:
            logger.error(f"Sequential task execution failed: {e}")
            raise

    async def execute_mixed_tasks(
        self,
        parallel_tasks: List[TaskExecution],
        sequential_tasks: List[TaskExecution],
        execution_engine: TaskExecutionEngine,
        context: Any,  # OrchestrationContext
    ) -> Dict[str, List[TaskResult]]:
        """Execute a mix of parallel and sequential tasks.

        Args:
            parallel_tasks: Tasks to execute in parallel
            sequential_tasks: Tasks to execute sequentially
            execution_engine: Task execution engine
            context: Orchestration context

        Returns:
            Dictionary with 'parallel' and 'sequential' results
        """
        try:
            logger.info(
                f"Executing mixed tasks: {len(parallel_tasks)} parallel, {len(sequential_tasks)} sequential"
            )

            # Execute parallel tasks first
            parallel_results = []
            if parallel_tasks:
                parallel_results = await self.execute_parallel_tasks(
                    parallel_tasks, execution_engine, context
                )

            # Then execute sequential tasks
            sequential_results = []
            if sequential_tasks:
                sequential_results = await self.execute_sequential_tasks(
                    sequential_tasks, execution_engine, context
                )

            return {"parallel": parallel_results, "sequential": sequential_results}

        except Exception as e:
            logger.error(f"Mixed task execution failed: {e}")
            raise

    async def execute_with_dependencies(
        self,
        tasks: List[TaskExecution],
        execution_engine: TaskExecutionEngine,
        context: Any,  # OrchestrationContext
    ) -> List[TaskResult]:
        """Execute tasks respecting their dependencies.

        Args:
            tasks: List of tasks with dependencies
            execution_engine: Task execution engine
            context: Orchestration context

        Returns:
            List of task results in dependency order
        """
        try:
            logger.info(f"Executing {len(tasks)} tasks with dependency resolution")

            # Group tasks by dependency level
            dependency_groups = self._group_by_dependencies(tasks)

            all_results = []

            for level, level_tasks in dependency_groups.items():
                logger.info(
                    f"Executing dependency level {level} with {len(level_tasks)} tasks"
                )

                # Execute tasks in this level in parallel
                level_results = await self.execute_parallel_tasks(
                    level_tasks, execution_engine, context
                )

                all_results.extend(level_results)

                # Check for failures in this level
                failed_tasks = [
                    r for r in level_results if r.status == TaskStatus.FAILED
                ]
                if failed_tasks:
                    logger.warning(
                        f"Level {level} had {len(failed_tasks)} failed tasks"
                    )

            logger.info(f"Completed dependency-based execution of {len(tasks)} tasks")
            return all_results

        except Exception as e:
            logger.error(f"Dependency-based execution failed: {e}")
            raise

    async def _check_dependencies(
        self, task: TaskExecution, completed_results: List[TaskResult]
    ) -> bool:
        """Check if all dependencies for a task are satisfied.

        Args:
            task: Task to check dependencies for
            completed_results: Results of completed tasks

        Returns:
            True if all dependencies are satisfied
        """
        if not task.definition.dependencies:
            return True

        # Create set of completed task IDs
        completed_ids = {
            str(r.task_id)
            for r in completed_results
            if r.status == TaskStatus.COMPLETED
        }

        # Check if all dependencies are completed
        for dep_id in task.definition.dependencies:
            if dep_id not in completed_ids:
                logger.debug(f"Task {task.id} waiting for dependency {dep_id}")
                return False

        return True

    def _group_by_dependencies(
        self, tasks: List[TaskExecution]
    ) -> Dict[int, List[TaskExecution]]:
        """Group tasks by their dependency level.

        Args:
            tasks: List of tasks to group

        Returns:
            Dictionary mapping dependency level to list of tasks
        """
        # Create dependency graph
        task_map = {str(task.id): task for task in tasks}
        dependency_graph = {}

        for task in tasks:
            task_id = str(task.id)
            dependency_graph[task_id] = {
                "task": task,
                "dependencies": set(task.definition.dependencies),
                "level": 0,
            }

        # Calculate dependency levels
        levels = {}
        processed = set()

        def calculate_level(task_id: str, visited: set) -> int:
            """Calculate dependency level for a task."""
            if task_id in visited:
                raise ValueError(f"Circular dependency detected: {task_id}")

            if task_id in processed:
                return dependency_graph[task_id]["level"]

            visited.add(task_id)

            if task_id not in dependency_graph:
                return 0

            task_info = dependency_graph[task_id]
            max_dep_level = 0

            for dep_id in task_info["dependencies"]:
                if dep_id in dependency_graph:
                    dep_level = calculate_level(dep_id, visited)
                    max_dep_level = max(max_dep_level, dep_level + 1)

            task_info["level"] = max_dep_level
            processed.add(task_id)

            return max_dep_level

        # Calculate levels for all tasks
        for task_id in dependency_graph:
            if task_id not in processed:
                calculate_level(task_id, set())

        # Group by level
        for task_id, task_info in dependency_graph.items():
            level = task_info["level"]
            if level not in levels:
                levels[level] = []
            levels[level].append(task_info["task"])

        return levels

    def _create_dag_node_from_task(self, task: TaskExecution) -> Any:
        """Create a mock DAG node from a task execution.

        Args:
            task: Task execution to convert

        Returns:
            Mock DAG node object
        """

        # Create a simple object that mimics DAG node structure
        class MockDAGNode:
            def __init__(self, task_execution: TaskExecution):
                self.id = task_execution.id
                self.name = task_execution.definition.name
                self.agent = task_execution.definition.agent_type
                self.type = task_execution.definition.type.value
                self.inputs = task_execution.inputs
                self.outputs = task_execution.definition.outputs
                self.dependencies = task_execution.definition.dependencies
                self.description = task_execution.definition.description

        return MockDAGNode(task)

    def get_execution_stats(self) -> Dict[str, Any]:
        """Get execution coordination statistics.

        Returns:
            Dictionary with execution statistics
        """
        return {
            "max_concurrent_tasks": self.max_concurrent_tasks,
            "active_tasks": len(self.active_tasks),
            "semaphore_value": self.task_semaphore._value,
            "semaphore_waiters": len(self.task_semaphore._waiters)
            if hasattr(self.task_semaphore, "_waiters")
            else 0,
        }


class DependencyError(Exception):
    """Exception raised when task dependencies are not met."""

    pass


class CriticalTaskFailure(Exception):
    """Exception raised when a critical task fails."""

    pass

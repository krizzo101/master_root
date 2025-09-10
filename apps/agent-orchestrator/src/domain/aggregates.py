#!/usr/bin/env python3
"""
Domain Aggregates following DDD principles

Aggregates are clusters of domain objects that are treated as a single unit.
The aggregate root enforces consistency boundaries and invariants.
"""

import asyncio
from collections import defaultdict
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Set

from .entities import AgentTask
from .value_objects import RetryPolicy, TaskResult, ValidationResult


class TaskAggregate:
    """
    Task aggregate root that manages a collection of related tasks.

    This aggregate enforces consistency rules across tasks, manages
    dependencies, coordinates execution, and maintains invariants.
    """

    def __init__(
        self,
        aggregate_id: str,
        name: str = "Task Aggregate",
        max_parallel_tasks: int = 10,
        timeout: float = 3600.0,  # 1 hour default
        retry_policy: RetryPolicy = None,
        metadata: Dict[str, Any] = None,
    ):
        """Initialize task aggregate"""
        self.aggregate_id = aggregate_id
        self.name = name
        self.max_parallel_tasks = max_parallel_tasks
        self.timeout = timeout
        self.retry_policy = retry_policy or RetryPolicy()
        self.metadata = metadata or {}

        # Task management
        self._tasks: Dict[str, AgentTask] = {}
        self._task_order: List[str] = []
        self._dependency_graph: Dict[str, Set[str]] = defaultdict(set)
        self._reverse_dependencies: Dict[str, Set[str]] = defaultdict(set)

        # Execution state
        self._running_tasks: Set[str] = set()
        self._completed_tasks: Set[str] = set()
        self._failed_tasks: Set[str] = set()

        # Aggregate state
        self._status = "pending"
        self._start_time: Optional[datetime] = None
        self._end_time: Optional[datetime] = None
        self._aggregate_result: Optional[Dict[str, Any]] = None

        # Event handlers and validators
        self._validators: List[Callable] = []
        self._event_handlers: Dict[str, List[Callable]] = {}
        self._task_executors: Dict[str, Callable] = {}

    def add_task(
        self,
        task: AgentTask,
        executor: Optional[Callable] = None,
        dependencies: List[str] = None,
    ) -> ValidationResult:
        """
        Add a task to the aggregate with validation.

        Enforces aggregate invariants and consistency rules.
        """
        # Validate task
        validation = task.validate()
        if not validation.is_valid:
            return validation

        # Check for duplicate task ID
        if task.task_id in self._tasks:
            return ValidationResult.invalid(
                errors=[f"Task with ID {task.task_id} already exists"]
            )

        # Validate dependencies exist
        dependencies = dependencies or task.dependencies
        for dep_id in dependencies:
            if dep_id not in self._tasks:
                return ValidationResult.invalid(
                    errors=[f"Dependency {dep_id} does not exist in aggregate"]
                )

        # Check for circular dependencies
        if self._would_create_cycle(task.task_id, dependencies):
            return ValidationResult.invalid(
                errors=["Adding task would create circular dependency"]
            )

        # Add task to aggregate
        self._tasks[task.task_id] = task
        self._task_order.append(task.task_id)

        # Set executor if provided
        if executor:
            task.set_executor(executor)
            self._task_executors[task.task_id] = executor

        # Update dependency graph
        for dep_id in dependencies:
            self._dependency_graph[task.task_id].add(dep_id)
            self._reverse_dependencies[dep_id].add(task.task_id)
            task.add_dependency(dep_id)

        return ValidationResult.valid()

    def remove_task(self, task_id: str) -> ValidationResult:
        """
        Remove a task from the aggregate.

        Ensures consistency by handling dependent tasks.
        """
        if task_id not in self._tasks:
            return ValidationResult.invalid(
                errors=[f"Task {task_id} not found in aggregate"]
            )

        # Check if task has dependents
        if task_id in self._reverse_dependencies:
            dependents = self._reverse_dependencies[task_id]
            if dependents:
                return ValidationResult.invalid(
                    errors=[f"Cannot remove task with dependents: {dependents}"]
                )

        # Remove task
        del self._tasks[task_id]
        self._task_order.remove(task_id)

        # Clean up dependencies
        for dep_id in self._dependency_graph[task_id]:
            self._reverse_dependencies[dep_id].discard(task_id)
        del self._dependency_graph[task_id]

        # Clean up execution state
        self._running_tasks.discard(task_id)
        self._completed_tasks.discard(task_id)
        self._failed_tasks.discard(task_id)

        return ValidationResult.valid()

    async def execute(self) -> Dict[str, TaskResult]:
        """
        Execute all tasks in the aggregate respecting dependencies.

        Uses topological sorting and parallel execution where possible.
        """
        # Validate aggregate state
        validation = self.validate()
        if not validation.is_valid:
            return {
                "aggregate_error": TaskResult.failure(
                    error=f"Aggregate validation failed: {validation.errors}",
                    error_type="AggregateValidationError",
                )
            }

        # Initialize execution
        self._status = "running"
        self._start_time = datetime.utcnow()
        results: Dict[str, TaskResult] = {}

        try:
            # Get execution order
            execution_order = self._get_execution_order()
            if not execution_order:
                return {
                    "aggregate_error": TaskResult.failure(
                        error="Could not determine execution order (possible circular dependency)",
                        error_type="DependencyError",
                    )
                }

            # Execute tasks in phases
            for phase in execution_order:
                # Execute tasks in current phase in parallel
                phase_tasks = []

                for task_id in phase:
                    task = self._tasks[task_id]

                    # Check if dependencies completed successfully
                    deps_failed = False
                    for dep_id in task.dependencies:
                        if dep_id in self._failed_tasks:
                            deps_failed = True
                            results[task_id] = TaskResult.failure(
                                error=f"Dependency {dep_id} failed",
                                error_type="DependencyFailure",
                            )
                            self._failed_tasks.add(task_id)
                            break

                    if not deps_failed:
                        # Create execution coroutine
                        executor = self._task_executors.get(task_id)
                        phase_tasks.append(self._execute_task(task, executor))

                # Wait for phase to complete
                if phase_tasks:
                    phase_results = await asyncio.gather(
                        *phase_tasks, return_exceptions=True
                    )

                    # Process results
                    for i, task_id in enumerate(
                        [t for t in phase if t not in self._failed_tasks]
                    ):
                        if isinstance(phase_results[i], Exception):
                            results[task_id] = TaskResult.failure(
                                error=str(phase_results[i]),
                                error_type=type(phase_results[i]).__name__,
                            )
                            self._failed_tasks.add(task_id)
                        else:
                            results[task_id] = phase_results[i]
                            if phase_results[i].is_success():
                                self._completed_tasks.add(task_id)
                            else:
                                self._failed_tasks.add(task_id)

            # Update aggregate status
            if self._failed_tasks:
                self._status = "partial_success"
            else:
                self._status = "completed"

        except Exception as e:
            self._status = "failed"
            results["aggregate_error"] = TaskResult.failure(
                error=str(e), error_type=type(e).__name__
            )

        finally:
            self._end_time = datetime.utcnow()
            self._aggregate_result = {
                "results": results,
                "completed": list(self._completed_tasks),
                "failed": list(self._failed_tasks),
                "duration": (self._end_time - self._start_time).total_seconds(),
            }

        return results

    async def _execute_task(
        self, task: AgentTask, executor: Callable = None
    ) -> TaskResult:
        """Execute a single task with monitoring"""
        self._running_tasks.add(task.task_id)

        try:
            # Execute with timeout
            result = await asyncio.wait_for(
                task.execute(executor), timeout=self.timeout
            )

            # Retry on failure if policy allows
            if result.is_failure() and task.retry_policy.should_retry(
                result.error_type, task._retry_count + 1
            ):
                result = await task.retry(executor)

            return result

        except asyncio.TimeoutError:
            return TaskResult.timeout(
                error=f"Task {task.task_id} exceeded timeout of {self.timeout}s"
            )

        finally:
            self._running_tasks.discard(task.task_id)

    def validate(self) -> ValidationResult:
        """
        Validate aggregate state and invariants.

        Checks for consistency, circular dependencies, and business rules.
        """
        errors = []
        warnings = []

        # Check for empty aggregate
        if not self._tasks:
            warnings.append("Aggregate contains no tasks")

        # Validate individual tasks
        for task_id, task in self._tasks.items():
            task_validation = task.validate()
            if not task_validation.is_valid:
                errors.append(f"Task {task_id}: {', '.join(task_validation.errors)}")

        # Check for circular dependencies
        if self._has_circular_dependencies():
            errors.append("Aggregate contains circular dependencies")

        # Check for orphaned tasks (no dependencies and nothing depends on them)
        orphaned = self._find_orphaned_tasks()
        if orphaned:
            warnings.append(f"Orphaned tasks found: {orphaned}")

        # Check for missing executors
        for task_id, task in self._tasks.items():
            if not task._executor and task_id not in self._task_executors:
                warnings.append(f"Task {task_id} has no executor")

        # Run custom validators
        for validator in self._validators:
            try:
                result = validator(self)
                if isinstance(result, ValidationResult):
                    if not result.is_valid:
                        errors.extend(result.errors)
                    warnings.extend(result.warnings)
            except Exception as e:
                errors.append(f"Validator error: {str(e)}")

        if errors:
            return ValidationResult.invalid(errors=errors, warnings=warnings)

        return ValidationResult.valid(warnings=warnings)

    def _would_create_cycle(self, task_id: str, dependencies: List[str]) -> bool:
        """Check if adding dependencies would create a cycle"""
        # Temporary add dependencies to check
        temp_graph = self._dependency_graph.copy()
        temp_graph[task_id] = set(dependencies)

        # Check for cycles using DFS
        visited = set()
        rec_stack = set()

        def has_cycle(node):
            visited.add(node)
            rec_stack.add(node)

            for neighbor in temp_graph.get(node, set()):
                if neighbor not in visited:
                    if has_cycle(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True

            rec_stack.remove(node)
            return False

        for node in temp_graph:
            if node not in visited:
                if has_cycle(node):
                    return True

        return False

    def _has_circular_dependencies(self) -> bool:
        """Check if the dependency graph has cycles"""
        visited = set()
        rec_stack = set()

        def has_cycle(task_id):
            visited.add(task_id)
            rec_stack.add(task_id)

            for dep_id in self._dependency_graph[task_id]:
                if dep_id not in visited:
                    if has_cycle(dep_id):
                        return True
                elif dep_id in rec_stack:
                    return True

            rec_stack.remove(task_id)
            return False

        for task_id in self._tasks:
            if task_id not in visited:
                if has_cycle(task_id):
                    return True

        return False

    def _get_execution_order(self) -> List[List[str]]:
        """
        Get task execution order using topological sort.

        Returns list of phases, where tasks in each phase can run in parallel.
        """
        # Calculate in-degree for each task
        in_degree = {
            task_id: len(deps) for task_id, deps in self._dependency_graph.items()
        }

        # Add tasks with no dependencies
        for task_id in self._tasks:
            if task_id not in in_degree:
                in_degree[task_id] = 0

        # Find all tasks with no dependencies
        queue = [task_id for task_id, degree in in_degree.items() if degree == 0]

        execution_order = []

        while queue:
            # Current phase - all tasks that can run in parallel
            current_phase = queue[:]
            execution_order.append(current_phase)
            queue = []

            # Process current phase
            for task_id in current_phase:
                # Reduce in-degree for dependent tasks
                for dependent in self._reverse_dependencies[task_id]:
                    in_degree[dependent] -= 1
                    if in_degree[dependent] == 0:
                        queue.append(dependent)

        # Check if all tasks were processed
        if sum(len(phase) for phase in execution_order) != len(self._tasks):
            return []  # Circular dependency detected

        return execution_order

    def _find_orphaned_tasks(self) -> List[str]:
        """Find tasks with no dependencies and no dependents"""
        orphaned = []

        for task_id in self._tasks:
            has_deps = (
                task_id in self._dependency_graph and self._dependency_graph[task_id]
            )
            has_dependents = (
                task_id in self._reverse_dependencies
                and self._reverse_dependencies[task_id]
            )

            if not has_deps and not has_dependents and len(self._tasks) > 1:
                orphaned.append(task_id)

        return orphaned

    def get_task(self, task_id: str) -> Optional[AgentTask]:
        """Get a task by ID"""
        return self._tasks.get(task_id)

    def get_all_tasks(self) -> List[AgentTask]:
        """Get all tasks in the aggregate"""
        return list(self._tasks.values())

    def get_ready_tasks(self) -> List[AgentTask]:
        """Get tasks that are ready to execute"""
        ready = []
        for task in self._tasks.values():
            if task.is_ready():
                # Check if all dependencies are complete
                deps_complete = all(
                    dep_id in self._completed_tasks for dep_id in task.dependencies
                )
                if deps_complete:
                    ready.append(task)
        return ready

    def get_metrics(self) -> Dict[str, Any]:
        """Get aggregate execution metrics"""
        total_tasks = len(self._tasks)
        completed_tasks = len(self._completed_tasks)
        failed_tasks = len(self._failed_tasks)

        metrics = {
            "aggregate_id": self.aggregate_id,
            "name": self.name,
            "status": self._status,
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "failed_tasks": failed_tasks,
            "success_rate": completed_tasks / total_tasks if total_tasks > 0 else 0,
            "running_tasks": len(self._running_tasks),
        }

        if self._start_time:
            metrics["start_time"] = self._start_time.isoformat()

        if self._end_time:
            metrics["end_time"] = self._end_time.isoformat()
            metrics["duration"] = (self._end_time - self._start_time).total_seconds()

        return metrics

    def to_dict(self) -> Dict[str, Any]:
        """Convert aggregate to dictionary representation"""
        return {
            "aggregate_id": self.aggregate_id,
            "name": self.name,
            "status": self._status,
            "max_parallel_tasks": self.max_parallel_tasks,
            "timeout": self.timeout,
            "retry_policy": self.retry_policy.to_dict(),
            "tasks": {task_id: task.to_dict() for task_id, task in self._tasks.items()},
            "dependency_graph": {k: list(v) for k, v in self._dependency_graph.items()},
            "completed_tasks": list(self._completed_tasks),
            "failed_tasks": list(self._failed_tasks),
            "metrics": self.get_metrics(),
            "metadata": self.metadata,
        }

    def __repr__(self) -> str:
        """String representation of aggregate"""
        return (
            f"TaskAggregate(id={self.aggregate_id}, name={self.name}, "
            f"tasks={len(self._tasks)}, status={self._status})"
        )

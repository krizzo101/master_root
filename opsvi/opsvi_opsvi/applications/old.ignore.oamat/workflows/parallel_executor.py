"""
Parallel Task Execution Engine for OAMAT

This module provides sophisticated parallel task execution with dependency management,
resource coordination, and advanced error handling for OAMAT workflows.
"""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from functools import wraps
from graphlib import TopologicalSorter
import logging
import os
import time
from typing import Any, Callable, Dict, List, Optional, Set, Tuple
import uuid

logger = logging.getLogger("ParallelExecutor")


class TaskStatus(Enum):
    """Task execution status"""

    PENDING = "pending"
    WAITING_DEPENDENCIES = "waiting_dependencies"
    READY = "ready"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRY = "retry"


class TaskPriority(Enum):
    """Task execution priority"""

    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


class ResourceType(Enum):
    """Types of resources that tasks might need"""

    FILE_SYSTEM = "file_system"
    NETWORK = "network"
    DATABASE = "database"
    MEMORY = "memory"
    COMPUTE = "compute"


@dataclass
class TaskResource:
    """Represents a resource that a task needs"""

    type: ResourceType
    identifier: str  # e.g., file path, database connection, etc.
    exclusive: bool = False  # Whether task needs exclusive access
    timeout: float = 30.0  # How long to wait for resource


@dataclass
class TaskRetryConfig:
    """Configuration for task retry behavior"""

    max_attempts: int = 3
    initial_delay: float = 1.0
    exponential_backoff: bool = True
    max_delay: float = 60.0
    retry_on_exceptions: List[type] = field(default_factory=lambda: [Exception])


@dataclass
class ParallelTask:
    """Represents a task that can be executed in parallel"""

    id: str
    name: str
    description: str
    function: Callable
    args: List[Any] = field(default_factory=list)
    kwargs: Dict[str, Any] = field(default_factory=dict)

    # Dependencies
    depends_on: List[str] = field(default_factory=list)
    dependent_tasks: Set[str] = field(default_factory=set)

    # Resource management
    required_resources: List[TaskResource] = field(default_factory=list)

    # Execution control
    priority: TaskPriority = TaskPriority.NORMAL
    estimated_duration: Optional[float] = None
    max_parallel_instances: int = 1

    # Error handling
    retry_config: TaskRetryConfig = field(default_factory=TaskRetryConfig)

    # Status tracking
    status: TaskStatus = TaskStatus.PENDING
    start_time: Optional[datetime] = None
    completion_time: Optional[datetime] = None
    duration: Optional[float] = None
    attempts: int = 0
    last_error: Optional[str] = None
    result: Any = None

    # Context data
    context: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExecutionBatch:
    """Represents a batch of tasks that can run in parallel"""

    id: str
    tasks: List[ParallelTask]
    max_concurrent: Optional[int] = None
    estimated_duration: Optional[float] = None
    priority: TaskPriority = TaskPriority.NORMAL


class ResourceManager:
    """Manages shared resources and prevents conflicts"""

    def __init__(self):
        self._resource_locks: Dict[str, asyncio.Lock] = {}
        self._resource_queue: Dict[str, asyncio.Queue] = {}
        self._exclusive_resources: Set[str] = set()
        self._resource_usage: Dict[str, Set[str]] = {}  # resource_id -> set of task_ids

    async def acquire_resources(self, task: ParallelTask) -> bool:
        """Acquire all required resources for a task"""
        acquired_resources = []

        try:
            for resource in task.required_resources:
                resource_key = f"{resource.type.value}:{resource.identifier}"

                # Create lock if it doesn't exist
                if resource_key not in self._resource_locks:
                    self._resource_locks[resource_key] = asyncio.Lock()

                # Try to acquire resource within timeout
                try:
                    await asyncio.wait_for(
                        self._resource_locks[resource_key].acquire(),
                        timeout=resource.timeout,
                    )
                    acquired_resources.append(resource_key)

                    # Track usage
                    if resource_key not in self._resource_usage:
                        self._resource_usage[resource_key] = set()
                    self._resource_usage[resource_key].add(task.id)

                    # Mark as exclusive if needed
                    if resource.exclusive:
                        self._exclusive_resources.add(resource_key)

                    logger.debug(f"Task {task.id} acquired resource {resource_key}")

                except asyncio.TimeoutError:
                    logger.warning(
                        f"Task {task.id} timed out waiting for resource {resource_key}"
                    )
                    # Release any already acquired resources
                    await self._release_resources(acquired_resources, task.id)
                    return False

            return True

        except Exception as e:
            logger.error(f"Error acquiring resources for task {task.id}: {e}")
            await self._release_resources(acquired_resources, task.id)
            return False

    async def release_resources(self, task: ParallelTask):
        """Release all resources used by a task"""
        resources_to_release = []

        for resource in task.required_resources:
            resource_key = f"{resource.type.value}:{resource.identifier}"
            resources_to_release.append(resource_key)

        await self._release_resources(resources_to_release, task.id)

    async def _release_resources(self, resource_keys: List[str], task_id: str):
        """Internal method to release specific resources"""
        for resource_key in resource_keys:
            if resource_key in self._resource_locks:
                # Remove from usage tracking
                if resource_key in self._resource_usage:
                    self._resource_usage[resource_key].discard(task_id)
                    if not self._resource_usage[resource_key]:
                        del self._resource_usage[resource_key]

                # Remove from exclusive if no longer used
                if resource_key in self._exclusive_resources:
                    if resource_key not in self._resource_usage:
                        self._exclusive_resources.discard(resource_key)

                # Release the lock
                self._resource_locks[resource_key].release()
                logger.debug(f"Released resource {resource_key} for task {task_id}")


class TaskDependencyManager:
    """Manages task dependencies using DAG topology"""

    def __init__(self):
        self.dependency_graph: Dict[str, List[str]] = {}
        self.reverse_dependencies: Dict[str, Set[str]] = {}

    def add_task(self, task: ParallelTask):
        """Add a task to the dependency graph"""
        self.dependency_graph[task.id] = task.depends_on.copy()

        # Build reverse dependency mapping
        for dep_id in task.depends_on:
            if dep_id not in self.reverse_dependencies:
                self.reverse_dependencies[dep_id] = set()
            self.reverse_dependencies[dep_id].add(task.id)

    def validate_dependencies(self, tasks: List[ParallelTask]) -> bool:
        """Validate that the dependency graph is acyclic"""
        try:
            # Build dependency graph for validation
            dep_graph = {}
            for task in tasks:
                dep_graph[task.id] = task.depends_on

            # Use TopologicalSorter to detect cycles
            sorter = TopologicalSorter(dep_graph)
            sorter.prepare()
            return True
        except ValueError as e:
            logger.error(f"Cyclic dependency detected: {e}")
            return False

    def get_ready_tasks(
        self, all_tasks: Dict[str, ParallelTask], completed_tasks: Set[str]
    ) -> List[str]:
        """Get tasks that are ready to execute (all dependencies satisfied)"""
        ready_tasks = []

        for task_id, task in all_tasks.items():
            if task.status == TaskStatus.PENDING and all(
                dep_id in completed_tasks for dep_id in task.depends_on
            ):
                ready_tasks.append(task_id)

        return ready_tasks

    def get_dependent_tasks(self, completed_task_id: str) -> Set[str]:
        """Get tasks that depend on the completed task"""
        return self.reverse_dependencies.get(completed_task_id, set())


def retry_with_backoff(retry_config: TaskRetryConfig):
    """Decorator for retrying task execution with exponential backoff"""

    def decorator(func):
        @wraps(func)
        async def wrapper(task: ParallelTask, *args, **kwargs):
            last_exception = None
            delay = retry_config.initial_delay

            for attempt in range(retry_config.max_attempts):
                try:
                    task.attempts = attempt + 1
                    result = await func(task, *args, **kwargs)
                    return result

                except Exception as e:
                    last_exception = e
                    task.last_error = str(e)

                    # Check if we should retry this exception
                    should_retry = any(
                        isinstance(e, exc_type)
                        for exc_type in retry_config.retry_on_exceptions
                    )

                    if not should_retry or attempt == retry_config.max_attempts - 1:
                        raise e

                    logger.warning(
                        f"Task {task.id} failed (attempt {attempt + 1}), "
                        f"retrying in {delay}s: {e}"
                    )

                    await asyncio.sleep(delay)

                    if retry_config.exponential_backoff:
                        delay = min(delay * 2, retry_config.max_delay)

            raise last_exception

        return wrapper

    return decorator


class ParallelTaskExecutor:
    """
    Advanced parallel task execution engine with dependency management,
    resource coordination, and sophisticated error handling.
    """

    def __init__(self, max_workers: int = None, max_concurrent_tasks: int = 10):
        self.max_workers = max_workers or min(32, (os.cpu_count() or 1) + 4)
        self.max_concurrent_tasks = max_concurrent_tasks

        # Core components
        self.resource_manager = ResourceManager()
        self.dependency_manager = TaskDependencyManager()
        self.thread_executor = ThreadPoolExecutor(max_workers=self.max_workers)

        # Task tracking
        self.tasks: Dict[str, ParallelTask] = {}
        self.execution_batches: List[ExecutionBatch] = []
        self.completed_tasks: Set[str] = set()
        self.failed_tasks: Set[str] = set()
        self.running_tasks: Set[str] = set()

        # Event system for coordination
        self.task_completion_events: Dict[str, asyncio.Event] = {}
        self.execution_stats = {
            "total_tasks": 0,
            "completed_tasks": 0,
            "failed_tasks": 0,
            "start_time": None,
            "end_time": None,
            "parallel_efficiency": 0.0,
        }

        # Execution control
        self._stop_execution = False
        self._execution_lock = asyncio.Lock()

        logger.info(f"ParallelTaskExecutor initialized with {self.max_workers} workers")

    def add_task(self, task: ParallelTask) -> str:
        """Add a task to the execution queue"""
        if task.id in self.tasks:
            raise ValueError(f"Task with ID {task.id} already exists")

        self.tasks[task.id] = task
        self.dependency_manager.add_task(task)
        self.task_completion_events[task.id] = asyncio.Event()

        logger.debug(f"Added task: {task.id} with dependencies: {task.depends_on}")
        return task.id

    def create_task(
        self,
        name: str,
        function: Callable,
        *args,
        depends_on: List[str] = None,
        priority: TaskPriority = TaskPriority.NORMAL,
        required_resources: List[TaskResource] = None,
        **kwargs,
    ) -> str:
        """Convenience method to create and add a task"""
        task_id = str(uuid.uuid4())

        task = ParallelTask(
            id=task_id,
            name=name,
            description=f"Task: {name}",
            function=function,
            args=list(args),
            kwargs=kwargs,
            depends_on=depends_on or [],
            priority=priority,
            required_resources=required_resources or [],
        )

        return self.add_task(task)

    def validate_execution_plan(self) -> Tuple[bool, List[str]]:
        """Validate the execution plan for correctness"""
        errors = []

        # Validate dependencies exist
        for task in self.tasks.values():
            for dep_id in task.depends_on:
                if dep_id not in self.tasks:
                    errors.append(
                        f"Task {task.id} depends on non-existent task {dep_id}"
                    )

        # Validate no cycles
        if not self.dependency_manager.validate_dependencies(list(self.tasks.values())):
            errors.append("Cyclic dependencies detected in task graph")

        # Check for resource conflicts
        resource_conflicts = self._check_resource_conflicts()
        errors.extend(resource_conflicts)

        return len(errors) == 0, errors

    def _check_resource_conflicts(self) -> List[str]:
        """Check for potential resource conflicts"""
        conflicts = []
        exclusive_resources = {}

        for task in self.tasks.values():
            for resource in task.required_resources:
                if resource.exclusive:
                    resource_key = f"{resource.type.value}:{resource.identifier}"
                    if resource_key in exclusive_resources:
                        conflicts.append(
                            f"Resource conflict: {resource_key} required exclusively by "
                            f"both {task.id} and {exclusive_resources[resource_key]}"
                        )
                    else:
                        exclusive_resources[resource_key] = task.id

        return conflicts

    async def execute_all(self, timeout: float = None) -> Dict[str, Any]:
        """Execute all tasks with parallel coordination"""
        async with self._execution_lock:
            if self._stop_execution:
                raise RuntimeError("Execution stopped")

            # Validate execution plan
            is_valid, errors = self.validate_execution_plan()
            if not is_valid:
                raise ValueError(f"Invalid execution plan: {errors}")

            self.execution_stats["start_time"] = time.time()
            self.execution_stats["total_tasks"] = len(self.tasks)

            logger.info(f"Starting parallel execution of {len(self.tasks)} tasks")

            try:
                # Create execution coordinator
                execution_task = asyncio.create_task(self._coordinate_execution())

                if timeout:
                    await asyncio.wait_for(execution_task, timeout=timeout)
                else:
                    await execution_task

                self.execution_stats["end_time"] = time.time()

                return self._generate_execution_report()

            except asyncio.TimeoutError:
                logger.error("Execution timed out")
                await self.stop_execution()
                raise
            except Exception as e:
                logger.error(f"Execution failed: {e}")
                await self.stop_execution()
                raise

    async def _coordinate_execution(self):
        """Main coordination loop for parallel execution"""
        execution_queue = asyncio.Queue()

        # Start with tasks that have no dependencies
        ready_tasks = self.dependency_manager.get_ready_tasks(
            self.tasks, self.completed_tasks
        )

        for task_id in ready_tasks:
            await execution_queue.put(task_id)
            self.tasks[task_id].status = TaskStatus.READY

        # Track running tasks
        running_task_futures: Dict[str, asyncio.Task] = {}

        while (
            not execution_queue.empty()
            or running_task_futures
            or len(self.completed_tasks) + len(self.failed_tasks) < len(self.tasks)
        ):
            if self._stop_execution:
                break

            # Start new tasks up to concurrency limit
            while (
                len(running_task_futures) < self.max_concurrent_tasks
                and not execution_queue.empty()
            ):
                task_id = await execution_queue.get()
                task = self.tasks[task_id]

                # Execute task
                future = asyncio.create_task(self._execute_task(task))
                running_task_futures[task_id] = future

                logger.info(f"Started task: {task_id} ({task.name})")

            # Wait for at least one task to complete
            if running_task_futures:
                done, pending = await asyncio.wait(
                    running_task_futures.values(), return_when=asyncio.FIRST_COMPLETED
                )

                # Process completed tasks
                for future in done:
                    task_id = None
                    for tid, tf in running_task_futures.items():
                        if tf == future:
                            task_id = tid
                            break

                    if task_id:
                        del running_task_futures[task_id]

                        try:
                            result = await future
                            await self._handle_task_completion(task_id, result)

                            # Queue dependent tasks
                            dependent_tasks = (
                                self.dependency_manager.get_dependent_tasks(task_id)
                            )
                            for dep_task_id in dependent_tasks:
                                if dep_task_id in self.tasks:
                                    ready_deps = (
                                        self.dependency_manager.get_ready_tasks(
                                            self.tasks, self.completed_tasks
                                        )
                                    )
                                    if dep_task_id in ready_deps:
                                        await execution_queue.put(dep_task_id)
                                        self.tasks[
                                            dep_task_id
                                        ].status = TaskStatus.READY

                        except Exception as e:
                            await self._handle_task_failure(task_id, e)
            else:
                # No tasks running, wait a bit
                await asyncio.sleep(0.1)

        # Wait for any remaining tasks
        if running_task_futures:
            await asyncio.gather(*running_task_futures.values(), return_exceptions=True)

    @retry_with_backoff(TaskRetryConfig())
    async def _execute_task(self, task: ParallelTask) -> Any:
        """Execute a single task with resource management and error handling"""
        task.status = TaskStatus.RUNNING
        task.start_time = datetime.now()
        self.running_tasks.add(task.id)

        try:
            # Acquire required resources
            if task.required_resources:
                if not await self.resource_manager.acquire_resources(task):
                    raise RuntimeError(
                        f"Failed to acquire resources for task {task.id}"
                    )

            # Execute the task function
            if asyncio.iscoroutinefunction(task.function):
                result = await task.function(*task.args, **task.kwargs)
            else:
                # Run synchronous function in thread pool
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    self.thread_executor, task.function, *task.args
                )

            task.result = result
            task.status = TaskStatus.COMPLETED
            task.completion_time = datetime.now()
            task.duration = (task.completion_time - task.start_time).total_seconds()

            return result

        except Exception as e:
            task.status = TaskStatus.FAILED
            task.last_error = str(e)
            raise
        finally:
            # Always release resources
            if task.required_resources:
                await self.resource_manager.release_resources(task)

            self.running_tasks.discard(task.id)

    async def _handle_task_completion(self, task_id: str, result: Any):
        """Handle successful task completion"""
        task = self.tasks[task_id]
        self.completed_tasks.add(task_id)
        self.execution_stats["completed_tasks"] += 1

        # Signal completion
        self.task_completion_events[task_id].set()

        logger.info(f"Task completed: {task_id} ({task.name}) in {task.duration:.2f}s")

    async def _handle_task_failure(self, task_id: str, error: Exception):
        """Handle task failure"""
        task = self.tasks[task_id]
        self.failed_tasks.add(task_id)
        self.execution_stats["failed_tasks"] += 1

        logger.error(f"Task failed: {task_id} ({task.name}) - {error}")

        # Cancel dependent tasks if configured to do so
        await self._cancel_dependent_tasks(task_id)

    async def _cancel_dependent_tasks(self, failed_task_id: str):
        """Cancel tasks that depend on a failed task"""
        dependent_tasks = self.dependency_manager.get_dependent_tasks(failed_task_id)

        for dep_task_id in dependent_tasks:
            if dep_task_id in self.tasks and self.tasks[dep_task_id].status in [
                TaskStatus.PENDING,
                TaskStatus.READY,
                TaskStatus.WAITING_DEPENDENCIES,
            ]:
                self.tasks[dep_task_id].status = TaskStatus.CANCELLED
                logger.warning(
                    f"Cancelled task {dep_task_id} due to failed dependency {failed_task_id}"
                )

    async def stop_execution(self):
        """Stop the execution gracefully"""
        self._stop_execution = True
        logger.info("Stopping parallel execution...")

        # Cancel all running tasks
        for task_id in self.running_tasks.copy():
            self.tasks[task_id].status = TaskStatus.CANCELLED

    def _generate_execution_report(self) -> Dict[str, Any]:
        """Generate comprehensive execution report"""
        total_duration = (
            self.execution_stats["end_time"] - self.execution_stats["start_time"]
        )

        # Calculate parallel efficiency
        total_task_time = sum(
            task.duration or 0
            for task in self.tasks.values()
            if task.status == TaskStatus.COMPLETED
        )

        efficiency = (total_task_time / total_duration) if total_duration > 0 else 0
        self.execution_stats["parallel_efficiency"] = efficiency

        task_details = {}
        for task in self.tasks.values():
            task_details[task.id] = {
                "name": task.name,
                "status": task.status.value,
                "duration": task.duration,
                "attempts": task.attempts,
                "error": task.last_error,
            }

        return {
            "success": len(self.failed_tasks) == 0,
            "execution_stats": self.execution_stats,
            "task_details": task_details,
            "completed_tasks": list(self.completed_tasks),
            "failed_tasks": list(self.failed_tasks),
            "parallel_efficiency": efficiency,
            "total_duration": total_duration,
        }

    async def wait_for_task(self, task_id: str, timeout: float = None) -> Any:
        """Wait for a specific task to complete"""
        if task_id not in self.task_completion_events:
            raise ValueError(f"Task {task_id} not found")

        try:
            if timeout:
                await asyncio.wait_for(
                    self.task_completion_events[task_id].wait(), timeout=timeout
                )
            else:
                await self.task_completion_events[task_id].wait()

            return self.tasks[task_id].result

        except asyncio.TimeoutError:
            raise TimeoutError(f"Task {task_id} did not complete within {timeout}s")

    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """Get detailed status of a specific task"""
        if task_id not in self.tasks:
            raise ValueError(f"Task {task_id} not found")

        task = self.tasks[task_id]
        return {
            "id": task.id,
            "name": task.name,
            "status": task.status.value,
            "progress": self._calculate_task_progress(task),
            "duration": task.duration,
            "estimated_duration": task.estimated_duration,
            "attempts": task.attempts,
            "dependencies_satisfied": all(
                dep_id in self.completed_tasks for dep_id in task.depends_on
            ),
            "error": task.last_error,
        }

    def _calculate_task_progress(self, task: ParallelTask) -> float:
        """Calculate estimated progress for a task"""
        if task.status == TaskStatus.COMPLETED:
            return 1.0
        elif task.status == TaskStatus.FAILED:
            return 0.0
        elif task.status == TaskStatus.RUNNING and task.estimated_duration:
            if task.start_time:
                elapsed = (datetime.now() - task.start_time).total_seconds()
                return min(elapsed / task.estimated_duration, 0.95)

        return 0.0

    def get_execution_visualization(self) -> Dict[str, Any]:
        """Generate data for visualizing the execution graph"""
        nodes = []
        edges = []

        for task in self.tasks.values():
            nodes.append(
                {
                    "id": task.id,
                    "name": task.name,
                    "status": task.status.value,
                    "duration": task.duration,
                    "priority": task.priority.value,
                }
            )

            for dep_id in task.depends_on:
                edges.append({"from": dep_id, "to": task.id})

        return {"nodes": nodes, "edges": edges, "stats": self.execution_stats}

    def shutdown(self):
        """Clean shutdown of the executor"""
        logger.info("Shutting down ParallelTaskExecutor")
        self.thread_executor.shutdown(wait=True)

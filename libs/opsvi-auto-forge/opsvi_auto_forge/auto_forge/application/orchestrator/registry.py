"""
auto_forge/application/orchestrator/registry.py

Production-ready rewrite of the TaskRegistryManager module.

Key fixes & improvements
------------------------
1. Added `initialize()` coroutine – solves the AttributeError raised by
   `api/main.py`.
2. Ensured that expensive I/O (Neo4j fetches) is only performed during
   explicit initialisation, never at import time.
3. Hardened error handling and added structured log messages compatible
   with the existing logging stack.
4. Added type hints, exhaustive doc-strings, PEP-8 compliance and
   defensive programming guards.
5. Simplified public surface – every async method is clearly named and
   documented.

NOTE:
The surrounding codebase (api/main.py, logging_config.py, etc.) must be
adapted to remove the now-unnecessary "hot‐fixes" described in the audit
document.  See the README section at the bottom of this file for the
exact one-line change required in api/main.py.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Dict, List, Optional, Set

from opsvi_auto_forge.config.models import AgentRole
from opsvi_auto_forge.infrastructure.memory.graph.client import Neo4jClient
from opsvi_auto_forge.infrastructure.monitoring.logging_config import get_correlation_id
from .task_models import (
    TaskDefinition,
    TaskRegistry,
    TaskType,
    TaskPriority,
)

_LOGGER: logging.Logger = logging.getLogger(__name__)


class TaskRegistryManager:
    """
    Manages all TaskDefinition objects for the Auto Forge runtime.

    The registry operates in two tiers:
        1. In-memory – ultra-fast look-ups for hot tasks
        2. Neo4j     – durable, shareable storage

    The calling code *must* invoke `await initialize()` during application
    start-up.  This keeps imports cheap (no I/O) and lets application
    owners choose when to do blocking work.
    """

    # NOTE: a class-level constant to explicitly mark when defaults were loaded
    _DEFAULT_TASKS_LOADED_FLAG = "_auto_forge__defaults_loaded"

    def __init__(self, neo4j_client: Optional[Neo4jClient] = None) -> None:
        self._registry: TaskRegistry = TaskRegistry()
        self._neo4j_client: Optional[Neo4jClient] = neo4j_client

        # Track which tasks have already been hydrated from Neo4j so we do
        # not fetch them twice.
        self._neo4j_hydrated: Set[str] = set()

        _LOGGER.debug(
            "TaskRegistryManager instantiated",
            extra={"correlation_id": get_correlation_id()},
        )

    # --------------------------------------------------------------------- #
    # Public API
    # --------------------------------------------------------------------- #

    async def initialize(self) -> None:
        """
        Perform all expensive start-up actions:

        1. Load default compiler/runtime tasks that ship with the codebase
           (pure Python – fast)
        2. Hydrate persisted tasks from Neo4j, if a client was supplied
        """
        _LOGGER.info("Initialising TaskRegistryManager…")

        # Load in-code defaults
        await self._load_default_tasks()

        # Hydrate Neo4j tasks (optional)
        if self._neo4j_client:
            await self._hydrate_all_tasks_from_neo4j()

        _LOGGER.info(
            "TaskRegistryManager initialised",
            extra={
                "defaults_loaded": self._registry.metadata.get(
                    self._DEFAULT_TASKS_LOADED_FLAG, False
                ),
                "total_tasks": len(self._registry.tasks),
            },
        )

    async def register_task(self, task: TaskDefinition) -> bool:
        """
        Register a TaskDefinition in memory and (optionally) persist it.

        Returns True on success, False otherwise.
        """
        try:
            self._validate_task_definition(task)
            self._registry.register_task(task)

            if self._neo4j_client:
                await self._persist_task_definition(task)

            _LOGGER.info(
                "Task registered",
                extra={
                    "task_name": task.name,
                    "task_type": task.type.value,
                    "correlation_id": get_correlation_id(),
                },
            )
            return True

        except Exception:  # pylint: disable=broad-except
            _LOGGER.exception(
                "Unable to register task",
                extra={"task_name": getattr(task, "name", "<unknown>")},
            )
            return False

    async def get_task(self, name: str) -> Optional[TaskDefinition]:
        """
        Fetch a task by name, checking memory first, then Neo4j if needed.
        """
        # 1. Fast in-memory path
        task = self._registry.get_task(name)
        if task is not None:
            return task

        # 2. Slow Neo4j path
        if self._neo4j_client and name not in self._neo4j_hydrated:
            task = await self._load_task_from_neo4j(name)
            if task:
                self._registry.register_task(task)
                self._neo4j_hydrated.add(name)
                return task

        return None

    async def list_tasks(
        self,
        task_type: Optional[TaskType] = None,
        role: Optional[AgentRole] = None,
    ) -> List[TaskDefinition]:
        """
        Return a list of TaskDefinitions filtered by type and/or agent role.
        """
        return [
            t
            for t in self._registry.tasks.values()
            if (task_type is None or t.type == task_type)
            and (role is None or role.value == t.agent_type)
        ]

    async def remove_task(self, name: str) -> bool:
        """
        Remove a task from both memory and Neo4j (if available).

        Returns True when the task no longer exists anywhere.
        """
        in_memory_removed: bool = self._registry.remove_task(name)

        neo4j_removed: bool = True
        if self._neo4j_client:
            neo4j_removed = await self._remove_task_from_neo4j(name)

        removed = in_memory_removed and neo4j_removed
        _LOGGER.debug(
            "Task removal status",
            extra={"task_name": name, "removed": removed},
        )
        return removed

    # --------------------------------------------------------------------- #
    # Internal helpers
    # --------------------------------------------------------------------- #

    @staticmethod
    def _validate_task_definition(task: TaskDefinition) -> None:
        """
        Sanity checks to guarantee the TaskDefinition is well-formed.
        """
        if not task.name:
            raise ValueError("TaskDefinition.name must be a non-empty string")
        if not isinstance(task.type, TaskType):
            raise ValueError("TaskDefinition.type must be a TaskType enum")
        if task.priority and not isinstance(task.priority, TaskPriority):
            raise ValueError("TaskDefinition.priority must be a TaskPriority")

    async def _hydrate_all_tasks_from_neo4j(self) -> None:
        """
        Pull every persisted task from Neo4j into memory.

        Runs concurrently in small batches for I/O efficiency.
        """
        if not self._neo4j_client:
            return

        _LOGGER.info("Hydrating tasks from Neo4j…")

        # Query to get all task definitions from Neo4j
        query = """
        MATCH (t:TaskDefinition)
        RETURN t
        """

        try:
            result = await self._neo4j_client.execute_query(query)
            # If no TaskDefinition nodes exist yet, this is normal for first run
            if not result:
                _LOGGER.info(
                    "No existing TaskDefinition nodes found in Neo4j - this is normal for first run"
                )
                return

            async def _hydrate(node_data: Dict) -> None:
                try:
                    # Extract the task data from the Neo4j node
                    task_props = node_data.get("t", {})
                    if task_props:
                        # Convert Neo4j node properties to TaskDefinition
                        task = TaskDefinition(
                            name=task_props.get("name", ""),
                            type=TaskType(task_props.get("type", "planning")),
                            agent_type=task_props.get("agent_type", "planner"),
                            description=task_props.get("description", ""),
                            inputs=task_props.get("inputs", {}),
                            outputs=task_props.get("outputs", {}),
                            dependencies=task_props.get("dependencies", []),
                            timeout_seconds=task_props.get("timeout_seconds", 300),
                            retry_attempts=task_props.get("retry_attempts", 3),
                            priority=TaskPriority(task_props.get("priority", 2)),
                            queue=task_props.get("queue", "default"),
                            required=task_props.get("required", True),
                            metadata=task_props.get("metadata", {}),
                        )
                        self._registry.register_task(task)
                        self._neo4j_hydrated.add(task.name)
                except Exception as exc:  # pylint: disable=broad-except
                    _LOGGER.error(
                        "Failed to hydrate task from Neo4j",
                        exc_info=exc,
                        extra={"node_data": node_data},
                    )

            # Use bounded concurrency to avoid hammering the DB
            semaphore = asyncio.Semaphore(10)

            async def _worker(node_d: Dict) -> None:
                async with semaphore:
                    await _hydrate(node_d)

            await asyncio.gather(*[_worker(nd) for nd in result])
            _LOGGER.info("Neo4j hydration complete", extra={"count": len(result)})

        except Exception as exc:
            _LOGGER.error("Failed to hydrate tasks from Neo4j", exc_info=exc)

    async def _persist_task_definition(self, task: TaskDefinition) -> None:
        """
        Persist a TaskDefinition to Neo4j.
        """
        if self._neo4j_client is None:
            return

        try:
            # Use MERGE to create or update the task definition
            query = """
            MERGE (t:TaskDefinition {name: $name})
            SET t.type = $type,
                t.agent_type = $agent_type,
                t.description = $description,
                t.inputs = $inputs,
                t.outputs = $outputs,
                t.dependencies = $dependencies,
                t.timeout_seconds = $timeout_seconds,
                t.retry_attempts = $retry_attempts,
                t.priority = $priority,
                t.queue = $queue,
                t.required = $required,
                t.metadata = $metadata,
                t.updated_at = datetime()
            """

            params = {
                "name": task.name,
                "type": task.type.value,
                "agent_type": task.agent_type,
                "description": task.description,
                "inputs": task.inputs,
                "outputs": task.outputs,
                "dependencies": task.dependencies,
                "timeout_seconds": task.timeout_seconds,
                "retry_attempts": task.retry_attempts,
                "priority": task.priority.value,
                "queue": task.queue,
                "required": task.required,
                "metadata": task.metadata,
            }

            await self._neo4j_client.execute_write_query(query, params)
            _LOGGER.debug(
                "Task persisted to Neo4j",
                extra={"task_name": task.name},
            )
        except Exception:  # pylint: disable=broad-except
            _LOGGER.exception(
                "Error persisting task to Neo4j",
                extra={"task_name": task.name},
            )

    async def _load_task_from_neo4j(self, name: str) -> Optional[TaskDefinition]:
        """
        Fetch a single task from Neo4j by name.
        """
        try:
            query = """
            MATCH (t:TaskDefinition {name: $name})
            RETURN t
            """

            result = await self._neo4j_client.execute_query(query, {"name": name})

            if result and len(result) > 0:
                task_props = result[0].get("t", {})
                if task_props:
                    # Convert Neo4j node properties to TaskDefinition
                    return TaskDefinition(
                        name=task_props.get("name", ""),
                        type=TaskType(task_props.get("type", "planning")),
                        agent_type=task_props.get("agent_type", "planner"),
                        description=task_props.get("description", ""),
                        inputs=task_props.get("inputs", {}),
                        outputs=task_props.get("outputs", {}),
                        dependencies=task_props.get("dependencies", []),
                        timeout_seconds=task_props.get("timeout_seconds", 300),
                        retry_attempts=task_props.get("retry_attempts", 3),
                        priority=TaskPriority(task_props.get("priority", 2)),
                        queue=task_props.get("queue", "default"),
                        required=task_props.get("required", True),
                        metadata=task_props.get("metadata", {}),
                    )
        except Exception:  # pylint: disable=broad-except
            _LOGGER.exception(
                "Error loading task from Neo4j",
                extra={"task_name": name},
            )
        return None

    async def _remove_task_from_neo4j(self, name: str) -> bool:
        """
        Delete a task from Neo4j.  Returns True on success.
        """
        try:
            query = """
            MATCH (t:TaskDefinition {name: $name})
            DELETE t
            """

            await self._neo4j_client.execute_write_query(query, {"name": name})
            return True
        except Exception:  # pylint: disable=broad-except
            _LOGGER.exception(
                "Error deleting task from Neo4j",
                extra={"task_name": name},
            )
            return False

    async def _load_default_tasks(self) -> None:
        """
        Load tasks that ship with Auto Forge (compiler passes, house-keeping).

        If you have no defaults, you can leave this method empty or remove the
        call in `initialize()`.  Keeping it here lets future contributors add
        new built-ins in one place.
        """
        if self._registry.metadata.get(self._DEFAULT_TASKS_LOADED_FLAG):
            # Safeguard – avoid double-loading
            return

        # Load comprehensive default tasks
        default_tasks = [
            TaskDefinition(
                name="plan",
                type=TaskType.PLANNING,
                agent_type="planner",
                description="Analyze requirements and create development plan",
                outputs={"plan": "Development plan document"},
                timeout_seconds=300,
                priority=TaskPriority.HIGH,
                queue="default",
            ),
            TaskDefinition(
                name="brainstorm",
                type=TaskType.PLANNING,
                agent_type="planner",
                description="Generate creative solutions and approaches",
                dependencies=["plan"],
                inputs={"plan": "Development plan from planning stage"},
                outputs={"brainstorm": "Creative solutions document"},
                timeout_seconds=180,
                priority=TaskPriority.NORMAL,
                queue="default",
                required=False,
            ),
            TaskDefinition(
                name="requirements",
                type=TaskType.SPECIFICATION,
                agent_type="specifier",
                description="Extract and formalize requirements",
                dependencies=["plan", "brainstorm"],
                inputs={"plan": "Development plan", "brainstorm": "Creative solutions"},
                outputs={"requirements": "Formal requirements document"},
                timeout_seconds=240,
                priority=TaskPriority.HIGH,
                queue="default",
            ),
            TaskDefinition(
                name="spec",
                type=TaskType.SPECIFICATION,
                agent_type="specifier",
                description="Create detailed technical specifications",
                dependencies=["requirements"],
                inputs={"requirements": "Requirements from requirements stage"},
                outputs={"specification": "Detailed specification document"},
                timeout_seconds=300,
                priority=TaskPriority.HIGH,
                queue="default",
            ),
            TaskDefinition(
                name="techspec",
                type=TaskType.SPECIFICATION,
                agent_type="specifier",
                description="Generate technology-specific specifications",
                dependencies=["spec"],
                inputs={"specification": "Specification from spec stage"},
                outputs={"techspec": "Technology-specific specifications"},
                timeout_seconds=240,
                priority=TaskPriority.HIGH,
                queue="default",
            ),
            TaskDefinition(
                name="arch",
                type=TaskType.ARCHITECTURE,
                agent_type="architect",
                description="Design system architecture",
                dependencies=["spec"],
                inputs={"specification": "Specification from spec stage"},
                outputs={"architecture": "Architecture design document"},
                timeout_seconds=300,
                priority=TaskPriority.HIGH,
                queue="default",
            ),
            TaskDefinition(
                name="dataflow",
                type=TaskType.ARCHITECTURE,
                agent_type="architect",
                description="Design data flow and integration patterns",
                dependencies=["arch"],
                inputs={"architecture": "Architecture from arch stage"},
                outputs={"dataflow": "Data flow design document"},
                timeout_seconds=180,
                priority=TaskPriority.NORMAL,
                queue="default",
                required=False,
            ),
            TaskDefinition(
                name="dbschema",
                type=TaskType.ARCHITECTURE,
                agent_type="architect",
                description="Design database schema",
                dependencies=["arch"],
                inputs={"architecture": "Architecture from arch stage"},
                outputs={"dbschema": "Database schema design"},
                timeout_seconds=180,
                priority=TaskPriority.NORMAL,
                queue="default",
                required=False,
            ),
            TaskDefinition(
                name="cicd",
                type=TaskType.ARCHITECTURE,
                agent_type="architect",
                description="Design CI/CD pipeline",
                dependencies=["arch"],
                inputs={"architecture": "Architecture from arch stage"},
                outputs={"cicd": "CI/CD pipeline design"},
                timeout_seconds=120,
                priority=TaskPriority.NORMAL,
                queue="default",
                required=False,
            ),
            TaskDefinition(
                name="scaffold",
                type=TaskType.CODING,
                agent_type="coder",
                description="Create project structure and boilerplate",
                dependencies=["arch", "techspec"],
                inputs={
                    "architecture": "Architecture design",
                    "techspec": "Technology specifications",
                },
                outputs={"scaffold": "Project structure and boilerplate"},
                timeout_seconds=180,
                priority=TaskPriority.HIGH,
                queue="io",
            ),
            TaskDefinition(
                name="code",
                type=TaskType.CODING,
                agent_type="coder",
                description="Implement core functionality",
                dependencies=["scaffold"],
                inputs={"scaffold": "Project structure from scaffold stage"},
                outputs={"code": "Source code files"},
                timeout_seconds=600,
                priority=TaskPriority.NORMAL,
                queue="heavy",
            ),
            TaskDefinition(
                name="testgen",
                type=TaskType.TESTING,
                agent_type="tester",
                description="Generate comprehensive test suites",
                dependencies=["code"],
                inputs={"code": "Source code from coding stage"},
                outputs={"testgen": "Test suite files"},
                timeout_seconds=240,
                priority=TaskPriority.NORMAL,
                queue="io",
            ),
            TaskDefinition(
                name="testrun",
                type=TaskType.TESTING,
                agent_type="tester",
                description="Execute test suites and collect results",
                dependencies=["testgen"],
                inputs={"testgen": "Test suite from testgen stage"},
                outputs={"testrun": "Test execution results"},
                timeout_seconds=300,
                priority=TaskPriority.NORMAL,
                queue="test",
            ),
            TaskDefinition(
                name="assure",
                type=TaskType.ANALYSIS,
                agent_type="critic",
                description="Run assurance checks in parallel",
                dependencies=["testrun"],
                inputs={"testrun": "Test results from testrun stage"},
                outputs={"assure": "Assurance check results"},
                timeout_seconds=180,
                priority=TaskPriority.NORMAL,
                queue="io",
            ),
            TaskDefinition(
                name="perf_smoke",
                type=TaskType.PERFORMANCE,
                agent_type="tester",
                description="Run performance smoke tests",
                dependencies=["testrun"],
                inputs={"testrun": "Test results from testrun stage"},
                outputs={"perf_smoke": "Performance test results"},
                timeout_seconds=120,
                priority=TaskPriority.NORMAL,
                queue="test",
                required=False,
            ),
            TaskDefinition(
                name="critic",
                type=TaskType.REVIEW,
                agent_type="critic",
                description="Evaluate overall quality and generate critique",
                dependencies=["assure", "perf_smoke"],
                inputs={
                    "assure": "Assurance results",
                    "perf_smoke": "Performance results",
                },
                outputs={"critic": "Quality evaluation report"},
                timeout_seconds=180,
                priority=TaskPriority.NORMAL,
                queue="io",
            ),
            TaskDefinition(
                name="repair",
                type=TaskType.CODING,
                agent_type="coder",
                description="Repair issues based on critique",
                dependencies=["critic"],
                inputs={"critic": "Critique from critic stage"},
                outputs={"repair": "Repaired code"},
                timeout_seconds=300,
                priority=TaskPriority.NORMAL,
                queue="heavy",
                required=False,
            ),
            TaskDefinition(
                name="perf_opt",
                type=TaskType.PERFORMANCE,
                agent_type="coder",
                description="Optimize performance if needed",
                dependencies=["critic"],
                inputs={"critic": "Critique from critic stage"},
                outputs={"perf_opt": "Performance optimizations"},
                timeout_seconds=240,
                priority=TaskPriority.NORMAL,
                queue="heavy",
                required=False,
            ),
            TaskDefinition(
                name="finalize",
                type=TaskType.DEPLOYMENT,
                agent_type="coder",
                description="Package and document the solution",
                dependencies=["critic", "repair", "perf_opt"],
                inputs={
                    "critic": "Final critique",
                    "repair": "Repaired code",
                    "perf_opt": "Performance optimizations",
                },
                outputs={"finalize": "Final packaged solution"},
                timeout_seconds=180,
                priority=TaskPriority.NORMAL,
                queue="io",
            ),
        ]

        for task in default_tasks:
            self._registry.register_task(task)

        # Mark as loaded
        self._registry.metadata[self._DEFAULT_TASKS_LOADED_FLAG] = True
        _LOGGER.info(f"Loaded {len(default_tasks)} default tasks")

    # --------------------------------------------------------------------- #
    # Convenience / dunder methods
    # --------------------------------------------------------------------- #

    def __len__(self) -> int:  # noqa: D401
        """Number of tasks currently in memory."""
        return len(self._registry.tasks)

    def __contains__(self, item: str) -> bool:  # noqa: D401
        """`"compile"` in task_registry."""
        return item in self._registry.tasks


# ===================================================================== #
# README - Single API change required
# ===================================================================== #
#
# In src/auto_forge/api/main.py replace the current start-up call:
#
#     await task_registry.initialize()
#
# with:
#
#     await task_registry.initialize()
#
# (Yes, the same line – the difference is that the method now exists.)
#
# If you previously patched main.py to call `load_default_tasks()` or
# something similar, revert that change to use the brand-new initialise
# routine.
#
# ===================================================================== #

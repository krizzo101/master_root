"""
Smart Decomposition Meta-Intelligence System - Dependency Manager
Neo4j-based dependency graph with parallel execution and context propagation
"""

import asyncio
import copy
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import json
import time
from typing import Any, Dict, List, Optional
import uuid

# Neo4j integration with fallback for POC
try:
    from neo4j import AsyncGraphDatabase

    NEO4J_AVAILABLE = True
except ImportError:
    print("⚠️  Neo4j driver not available - using mock for POC demo")
    AsyncGraphDatabase = None
    NEO4J_AVAILABLE = False

from .config import SystemConfig, get_config


class TaskStatus(str, Enum):
    """Task execution status"""

    PENDING = "pending"
    READY = "ready"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class BlockingStrategy(Enum):
    """Dependency blocking strategies"""

    STRICT = "strict"  # Block until all dependencies complete
    OPTIMISTIC = "optimistic"  # Proceed with partial context if safe
    TIMEOUT = "timeout"  # Block with timeout fallback
    CONDITIONAL = "conditional"  # Block based on dependency type


@dataclass
class TaskNode:
    """Task node representation in dependency graph"""

    task_id: str
    agent_role: str
    task_type: str
    status: TaskStatus
    dependencies: List[str]
    context_requirements: Dict[str, Any]
    estimated_duration: int
    created_at: datetime
    priority: int = 1


class Neo4jDependencyGraph:
    """
    Neo4j-based dependency graph management with Cypher queries.
    Implements REQ-002: Context and Dependency Management
    """

    def __init__(
        self,
        neo4j_uri: str = "bolt://localhost:7687",
        username: str = "neo4j",
        password: str = "oamatdbtest",
    ):
        self.neo4j_uri = neo4j_uri
        self.username = username
        self.password = password
        self.driver = None
        self.task_nodes = {}
        self.dependency_cache = {}
        self.initialized = False

    async def initialize(self):
        """Initialize Neo4j connection and schema"""
        if NEO4J_AVAILABLE:
            try:
                self.driver = AsyncGraphDatabase.driver(
                    self.neo4j_uri, auth=(self.username, self.password)
                )
                await self._create_schema()
                self.initialized = True
                print("✅ Neo4j dependency graph initialized")
            except Exception as e:
                print(f"⚠️  Neo4j connection failed: {e}")
                self._use_mock_implementation()
        else:
            self._use_mock_implementation()

    def _use_mock_implementation(self):
        """Use mock implementation for POC demonstration"""
        self.driver = MockNeo4jDriver()
        self.initialized = True
        print("🔄 Using mock dependency graph for POC demo")

    async def _create_schema(self):
        """Create Neo4j constraints and indexes"""
        if not self.driver:
            return

        async with self.driver.session() as session:
            # Create constraints
            await session.run(
                """
                CREATE CONSTRAINT IF NOT EXISTS
                FOR (t:Task) REQUIRE t.task_id IS UNIQUE
            """
            )

            # Create indexes
            await session.run(
                """
                CREATE INDEX IF NOT EXISTS
                FOR (t:Task) ON (t.status, t.agent_role, t.priority)
            """
            )

    async def add_task(self, task: TaskNode) -> bool:
        """Add task node to dependency graph"""
        if not self.initialized:
            await self.initialize()

        async with self.driver.session() as session:
            result = await session.run(
                """
                CREATE (t:Task {
                    task_id: $task_id,
                    agent_role: $agent_role,
                    task_type: $task_type,
                    status: $status,
                    context_requirements: $context_requirements,
                    estimated_duration: $estimated_duration,
                    created_at: $created_at,
                    priority: $priority
                })
                RETURN t.task_id as task_id
            """,
                task_id=task.task_id,
                agent_role=task.agent_role,
                task_type=task.task_type,
                status=task.status.value,
                context_requirements=json.dumps(task.context_requirements),
                estimated_duration=task.estimated_duration,
                created_at=task.created_at.isoformat(),
                priority=task.priority,
            )

            # Add dependency relationships
            for dep_id in task.dependencies:
                await self.add_dependency(task.task_id, dep_id)

            # Cache locally
            self.task_nodes[task.task_id] = task

            return bool(await result.single())

    async def add_dependency(self, task_id: str, dependency_id: str) -> bool:
        """Create dependency relationship"""
        if not self.initialized:
            await self.initialize()

        async with self.driver.session() as session:
            result = await session.run(
                """
                MATCH (t:Task {task_id: $task_id})
                MATCH (d:Task {task_id: $dependency_id})
                CREATE (t)-[:DEPENDS_ON]->(d)
                RETURN count(*) as created
            """,
                task_id=task_id,
                dependency_id=dependency_id,
            )

            record = await result.single()
            return record and record["created"] > 0

    async def get_ready_tasks(self) -> List[str]:
        """Get tasks ready for execution (all dependencies satisfied)"""
        if not self.initialized:
            await self.initialize()

        async with self.driver.session() as session:
            result = await session.run(
                """
                MATCH (t:Task {status: 'pending'})
                WHERE NOT EXISTS {
                    MATCH (t)-[:DEPENDS_ON]->(d:Task)
                    WHERE d.status <> 'completed'
                }
                RETURN t.task_id as task_id
                ORDER BY t.priority DESC, t.created_at
            """
            )

            return [record["task_id"] async for record in result]

    async def get_parallel_execution_waves(self) -> List[List[str]]:
        """
        Identify waves of tasks that can execute in parallel.
        Returns list of waves, each wave contains tasks with no dependencies between them.
        """
        if not self.initialized:
            await self.initialize()

        async with self.driver.session() as session:
            result = await session.run(
                """
                // Find all pending tasks and their dependency depths
                MATCH (t:Task {status: 'pending'})
                OPTIONAL MATCH path = (t)-[:DEPENDS_ON*]->(d:Task {status: 'pending'})
                WITH t, max(length(path)) as depth
                WHERE depth IS NULL OR NOT EXISTS {
                    MATCH (t)-[:DEPENDS_ON]->(d:Task)
                    WHERE d.status <> 'completed'
                }
                RETURN t.task_id as task_id, coalesce(depth, 0) as depth
                ORDER BY depth, t.priority DESC, t.created_at
            """
            )

            # Group tasks by depth (wave)
            waves = {}
            async for record in result:
                depth = record["depth"]
                if depth not in waves:
                    waves[depth] = []
                waves[depth].append(record["task_id"])

            return [waves[depth] for depth in sorted(waves.keys())]

    async def mark_task_completed(self, task_id: str, result_context: Dict[str, Any]):
        """Mark task as completed and store result context"""
        if not self.initialized:
            await self.initialize()

        async with self.driver.session() as session:
            await session.run(
                """
                MATCH (t:Task {task_id: $task_id})
                SET t.status = 'completed',
                    t.completed_at = $completed_at,
                    t.result_context = $result_context
                RETURN t.task_id
            """,
                task_id=task_id,
                completed_at=datetime.utcnow().isoformat(),
                result_context=json.dumps(result_context),
            )

            # Update local cache
            if task_id in self.task_nodes:
                self.task_nodes[task_id].status = TaskStatus.COMPLETED

    async def detect_cycles(self) -> List[List[str]]:
        """Detect dependency cycles using Neo4j graph algorithms"""
        if not self.initialized:
            await self.initialize()

        async with self.driver.session() as session:
            result = await session.run(
                """
                MATCH path = (t:Task)-[:DEPENDS_ON*]->(t)
                RETURN [node in nodes(path) | node.task_id] as cycle
            """
            )

            return [record["cycle"] async for record in result]

    async def get_task_context(self, task_id: str) -> Dict[str, Any]:
        """Get accumulated context for a task"""
        if not self.initialized:
            await self.initialize()

        async with self.driver.session() as session:
            result = await session.run(
                """
                MATCH (t:Task {task_id: $task_id})
                OPTIONAL MATCH (t)-[:DEPENDS_ON]->(d:Task {status: 'completed'})
                RETURN t.context_requirements as requirements,
                       collect(d.result_context) as dependency_contexts
            """,
                task_id=task_id,
            )

            record = await result.single()
            if not record:
                return {}

            # Merge contexts from dependencies
            context = json.loads(record["requirements"] or "{}")
            for dep_context in record["dependency_contexts"]:
                if dep_context:
                    dep_data = json.loads(dep_context)
                    context.update(dep_data)

            return context

    async def close(self):
        """Close Neo4j connection"""
        if self.driver and hasattr(self.driver, "close"):
            await self.driver.close()


class MockNeo4jDriver:
    """Mock Neo4j driver for POC demonstration"""

    def __init__(self):
        self.tasks = {}
        self.dependencies = {}

    def session(self):
        return MockNeo4jSession(self.tasks, self.dependencies)


class MockNeo4jSession:
    """Mock Neo4j session"""

    def __init__(self, tasks, dependencies):
        self.tasks = tasks
        self.dependencies = dependencies

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

    async def run(self, query: str, **params):
        return MockNeo4jResult(query, params, self.tasks, self.dependencies)


class MockNeo4jResult:
    """Mock Neo4j result"""

    def __init__(self, query, params, tasks, dependencies):
        self.query = query
        self.params = params
        self.tasks = tasks
        self.dependencies = dependencies
        self._iteration_count = 0

    async def single(self):
        if "CREATE (t:Task" in self.query:
            task_id = self.params.get("task_id")
            self.tasks[task_id] = self.params
            return {"task_id": task_id}
        elif "DEPENDS_ON" in self.query:
            task_id = self.params.get("task_id")
            dep_id = self.params.get("dependency_id")
            if task_id not in self.dependencies:
                self.dependencies[task_id] = []
            self.dependencies[task_id].append(dep_id)
            return {"created": 1}
        return {}

    def __aiter__(self):
        self._iteration_count = 0
        return self

    async def __anext__(self):
        # Mock iterator for query results
        if "WHERE NOT EXISTS" in self.query and "pending" in self.query:
            # Ready tasks query - return tasks with no pending dependencies
            if self._iteration_count == 0:
                self._iteration_count += 1
                return {"task_id": "requirements_analysis"}
            elif self._iteration_count == 1:
                self._iteration_count += 1
                return {"task_id": "work_planning"}
            else:
                raise StopAsyncIteration
        elif "max(length(path))" in self.query or "depth" in self.query:
            # Parallel execution waves query - return tasks organized by dependency depth
            if self._iteration_count == 0:
                self._iteration_count += 1
                return {"task_id": "requirements_analysis", "depth": 0}
            elif self._iteration_count == 1:
                self._iteration_count += 1
                return {"task_id": "work_planning", "depth": 1}
            elif self._iteration_count == 2:
                self._iteration_count += 1
                return {"task_id": "implementation", "depth": 2}
            elif self._iteration_count == 3:
                self._iteration_count += 1
                return {"task_id": "testing", "depth": 2}
            elif self._iteration_count == 4:
                self._iteration_count += 1
                return {"task_id": "documentation", "depth": 2}
            elif self._iteration_count == 5:
                self._iteration_count += 1
                return {"task_id": "validation", "depth": 3}
            else:
                raise StopAsyncIteration
        else:
            raise StopAsyncIteration


class ContextPropagator:
    """
    Manage context propagation between agents with state contamination prevention.
    Implements isolated context distribution with integrity validation.
    """

    def __init__(self, dependency_graph: Neo4jDependencyGraph):
        self.dependency_graph = dependency_graph
        self.context_store = {}
        self.isolation_locks = {}
        self.contamination_detectors = {}

    async def propagate_context(
        self, from_task: str, to_tasks: List[str], context: Dict[str, Any]
    ) -> Dict[str, bool]:
        """
        Propagate context with state isolation and contamination prevention.
        Returns success status for each target task.
        """
        # Create isolated context copy
        isolated_context = await self._create_isolated_context(context)

        # Validate context integrity
        if not await self._validate_context_integrity(isolated_context):
            raise ValueError("Context integrity validation failed")

        results = {}

        # Propagate to each target task with individual isolation
        for to_task in to_tasks:
            try:
                # Acquire task-specific lock
                lock = await self._get_isolation_lock(to_task)
                async with lock:
                    # Create task-specific context copy
                    task_context = await self._create_task_specific_context(
                        isolated_context, to_task
                    )

                    # Store context with contamination detection
                    await self._store_context_with_detection(to_task, task_context)

                    results[to_task] = True

            except Exception as e:
                print(f"Context propagation failed for task {to_task}: {e}")
                results[to_task] = False

        return results

    async def _create_isolated_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Create deep isolated copy with serialization safety"""
        try:
            # Use JSON serialization for deep copy and type safety
            serialized = json.dumps(context, default=str)
            isolated = json.loads(serialized)

            # Add isolation metadata
            isolated["_isolation"] = {
                "created_at": datetime.utcnow().isoformat(),
                "isolation_id": f"iso_{uuid.uuid4()}",
                "original_hash": hash(str(context)),
            }

            return isolated

        except Exception as e:
            # Fallback to deep copy
            isolated = copy.deepcopy(context)
            isolated["_isolation"] = {
                "created_at": datetime.utcnow().isoformat(),
                "isolation_id": f"iso_{uuid.uuid4()}",
                "fallback": True,
                "error": str(e),
            }
            return isolated

    async def _validate_context_integrity(self, context: Dict[str, Any]) -> bool:
        """Validate context integrity and detect potential contamination"""
        try:
            # Check for required isolation metadata
            if "_isolation" not in context:
                return False

            # Validate context structure
            if not isinstance(context, dict):
                return False

            # Check for suspicious modifications
            isolation_data = context["_isolation"]
            if "created_at" not in isolation_data:
                return False

            # Additional integrity checks
            return True

        except Exception:
            return False

    async def _get_isolation_lock(self, task_id: str) -> asyncio.Lock:
        """Get or create task-specific isolation lock"""
        if task_id not in self.isolation_locks:
            self.isolation_locks[task_id] = asyncio.Lock()
        return self.isolation_locks[task_id]

    async def _create_task_specific_context(
        self, isolated_context: Dict[str, Any], task_id: str
    ) -> Dict[str, Any]:
        """Create task-specific context with additional task metadata"""
        task_context = copy.deepcopy(isolated_context)
        task_context["_task_metadata"] = {
            "target_task_id": task_id,
            "propagated_at": datetime.utcnow().isoformat(),
            "context_version": 1,
        }
        return task_context

    async def _store_context_with_detection(
        self, task_id: str, context: Dict[str, Any]
    ):
        """Store context with contamination detection setup"""
        # Store pre-state hash for contamination detection
        pre_state_hash = hash(json.dumps(context, sort_keys=True, default=str))

        self.contamination_detectors[task_id] = {
            "pre_state_hash": pre_state_hash,
            "stored_at": datetime.utcnow(),
        }

        # Store the actual context
        self.context_store[task_id] = context

    async def detect_state_contamination(self, task_id: str) -> Dict[str, Any]:
        """Detect if task context has been contaminated"""
        if task_id not in self.contamination_detectors:
            return {"contaminated": False, "reason": "no_detection_setup"}

        if task_id not in self.context_store:
            return {"contaminated": True, "reason": "context_missing"}

        detector = self.contamination_detectors[task_id]
        current_context = self.context_store[task_id]

        # Calculate current hash
        current_hash = hash(json.dumps(current_context, sort_keys=True, default=str))

        contaminated = current_hash != detector["pre_state_hash"]

        return {
            "contaminated": contaminated,
            "reason": "hash_mismatch" if contaminated else "clean",
            "detection_setup_at": detector["stored_at"].isoformat(),
            "checked_at": datetime.utcnow().isoformat(),
        }

    async def get_context_for_task(self, task_id: str) -> Dict[str, Any]:
        """Get context for a specific task"""
        return self.context_store.get(task_id, {})


class BlockingManager:
    """
    Multi-strategy blocking manager for dependency resolution.
    Implements configurable blocking patterns with fallback mechanisms.
    """

    def __init__(
        self,
        strategy: BlockingStrategy = BlockingStrategy.TIMEOUT,
        timeout_seconds: int = 300,
    ):
        self.strategy = strategy
        self.timeout_seconds = timeout_seconds
        self.dependency_graph = None
        self.completion_status = {}

    async def wait_for_dependencies(
        self, task_id: str, dependencies: List[str]
    ) -> bool:
        """Wait for dependencies based on configured strategy"""

        if self.strategy == BlockingStrategy.STRICT:
            return await self._strict_blocking(task_id, dependencies)
        elif self.strategy == BlockingStrategy.OPTIMISTIC:
            return await self._optimistic_blocking(task_id, dependencies)
        elif self.strategy == BlockingStrategy.TIMEOUT:
            return await self._timeout_blocking(task_id, dependencies)
        elif self.strategy == BlockingStrategy.CONDITIONAL:
            return await self._conditional_blocking(task_id, dependencies)
        else:
            raise ValueError(f"Unknown blocking strategy: {self.strategy}")

    async def _strict_blocking(self, task_id: str, dependencies: List[str]) -> bool:
        """Strict blocking: wait until ALL dependencies complete"""
        timeout_start = time.time()
        timeout_duration = 10  # 10 second timeout for demo

        while True:
            if all(self.completion_status.get(dep, False) for dep in dependencies):
                return True

            # Check timeout
            if time.time() - timeout_start > timeout_duration:
                print(
                    f"⚠️  Timeout waiting for dependencies {dependencies} for task {task_id}"
                )
                return False

            await asyncio.sleep(0.1)

    async def _timeout_blocking(self, task_id: str, dependencies: List[str]) -> bool:
        """Timeout blocking: strict with timeout fallback"""
        start_time = datetime.utcnow()
        timeout = start_time + timedelta(
            seconds=min(self.timeout_seconds, 10)
        )  # Max 10s for demo

        while datetime.utcnow() < timeout:
            if all(self.completion_status.get(dep, False) for dep in dependencies):
                return True
            await asyncio.sleep(0.1)

        # Timeout occurred - log and decide
        missing_deps = [
            dep for dep in dependencies if not self.completion_status.get(dep, False)
        ]

        print(f"⚠️  Timeout waiting for dependencies {missing_deps} for task {task_id}")
        return False

    async def _optimistic_blocking(self, task_id: str, dependencies: List[str]) -> bool:
        """Optimistic blocking: proceed if safe subset of dependencies ready"""
        # For POC, proceed if at least 50% of dependencies are ready
        ready_deps = [
            dep for dep in dependencies if self.completion_status.get(dep, False)
        ]

        return len(ready_deps) >= len(dependencies) * 0.5

    async def _conditional_blocking(
        self, task_id: str, dependencies: List[str]
    ) -> bool:
        """Conditional blocking: strategy based on dependency types"""
        # For POC, use timeout strategy
        return await self._timeout_blocking(task_id, dependencies)

    def mark_task_completed(self, task_id: str):
        """Mark task as completed for dependency resolution"""
        self.completion_status[task_id] = True

    def get_completion_status(self) -> Dict[str, bool]:
        """Get current completion status for all tasks"""
        return self.completion_status.copy()


# Main dependency manager that orchestrates all components
class DependencyManager:
    """
    Main dependency manager orchestrating Neo4j graph, context propagation,
    and blocking strategies for parallel execution.
    """

    def __init__(self, config: Optional[SystemConfig] = None):
        self.config = config or get_config()
        self.dependency_graph = Neo4jDependencyGraph()
        self.context_propagator = ContextPropagator(self.dependency_graph)
        self.blocking_manager = BlockingManager(
            strategy=BlockingStrategy.TIMEOUT,
            timeout_seconds=self.config.parallel_execution.dependency_timeout_seconds,
        )
        self.initialized = False

    async def initialize(self):
        """Initialize all dependency management components"""
        await self.dependency_graph.initialize()
        self.initialized = True
        print("✅ Dependency manager initialized")

    async def add_task(
        self,
        task_id: str,
        agent_role: str,
        task_type: str,
        dependencies: List[str] = None,
        context_requirements: Dict[str, Any] = None,
        estimated_duration: int = 60,
        priority: int = 1,
    ) -> bool:
        """Add a new task to the dependency graph"""
        if not self.initialized:
            await self.initialize()

        task = TaskNode(
            task_id=task_id,
            agent_role=agent_role,
            task_type=task_type,
            status=TaskStatus.PENDING,
            dependencies=dependencies or [],
            context_requirements=context_requirements or {},
            estimated_duration=estimated_duration,
            created_at=datetime.utcnow(),
            priority=priority,
        )

        return await self.dependency_graph.add_task(task)

    async def get_next_ready_tasks(self, max_tasks: int = 5) -> List[str]:
        """Get next batch of tasks ready for execution"""
        if not self.initialized:
            await self.initialize()

        ready_tasks = await self.dependency_graph.get_ready_tasks()
        return ready_tasks[:max_tasks]

    async def get_parallel_execution_plan(self) -> List[List[str]]:
        """Get parallel execution plan organized by waves"""
        if not self.initialized:
            await self.initialize()

        return await self.dependency_graph.get_parallel_execution_waves()

    async def wait_for_task_dependencies(self, task_id: str) -> bool:
        """Wait for task dependencies to be satisfied"""
        task = self.dependency_graph.task_nodes.get(task_id)
        if not task:
            return False

        return await self.blocking_manager.wait_for_dependencies(
            task_id, task.dependencies
        )

    async def complete_task(self, task_id: str, result_context: Dict[str, Any]) -> bool:
        """Mark task as completed and propagate context"""
        if not self.initialized:
            await self.initialize()

        # Mark task as completed in graph
        await self.dependency_graph.mark_task_completed(task_id, result_context)

        # Mark in blocking manager
        self.blocking_manager.mark_task_completed(task_id)

        # Find dependent tasks and propagate context
        dependent_tasks = await self._get_dependent_tasks(task_id)
        if dependent_tasks:
            await self.context_propagator.propagate_context(
                task_id, dependent_tasks, result_context
            )

        return True

    async def _get_dependent_tasks(self, completed_task_id: str) -> List[str]:
        """Get tasks that depend on the completed task"""
        # For POC, return empty list - would query Neo4j in full implementation
        return []

    async def get_task_context(self, task_id: str) -> Dict[str, Any]:
        """Get accumulated context for a task"""
        if not self.initialized:
            await self.initialize()

        # Get context from dependency graph and propagator
        graph_context = await self.dependency_graph.get_task_context(task_id)
        propagated_context = await self.context_propagator.get_context_for_task(task_id)

        # Merge contexts
        merged_context = {**graph_context, **propagated_context}
        return merged_context

    async def detect_cycles(self) -> List[List[str]]:
        """Detect dependency cycles"""
        if not self.initialized:
            await self.initialize()

        return await self.dependency_graph.detect_cycles()

    async def get_performance_metrics(self) -> Dict[str, Any]:
        """Get dependency management performance metrics"""
        return {
            "total_tasks": len(self.dependency_graph.task_nodes),
            "completed_tasks": len(self.blocking_manager.completion_status),
            "context_propagations": len(self.context_propagator.context_store),
            "contamination_detectors": len(
                self.context_propagator.contamination_detectors
            ),
            "blocking_strategy": self.blocking_manager.strategy.value,
            "timeout_seconds": self.blocking_manager.timeout_seconds,
        }

    async def close(self):
        """Clean up resources"""
        await self.dependency_graph.close()

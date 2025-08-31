"""
Swarm task decomposition for efficient parallel execution.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Set

import networkx as nx

logger = logging.getLogger(__name__)


@dataclass
class TaskNode:
    """Represents a task in the decomposition graph"""

    task_id: str
    task_type: str
    description: str
    dependencies: Set[str] = field(default_factory=set)
    estimated_duration: float = 0.0  # seconds
    priority: int = 0  # Higher is more important
    metadata: Dict[str, Any] = field(default_factory=dict)
    status: str = "pending"  # pending, running, completed, failed


@dataclass
class ExecutionGroup:
    """Group of tasks that can be executed in parallel"""

    group_id: int
    tasks: List[TaskNode]
    total_estimated_duration: float
    can_parallelize: bool = True


class SwarmTaskDecomposer:
    """Decomposes complex tasks into parallel execution groups"""

    def __init__(self, max_parallel_tasks: int = 10):
        self.max_parallel_tasks = max_parallel_tasks
        self.task_graph = nx.DiGraph()
        self.execution_groups: List[ExecutionGroup] = []
        self.task_registry: Dict[str, TaskNode] = {}

    async def decompose_task(self, complex_task: Dict[str, Any]) -> List[ExecutionGroup]:
        """Decompose a complex task into execution groups"""

        # Clear previous state
        self.task_graph.clear()
        self.execution_groups.clear()
        self.task_registry.clear()

        # Extract or generate subtasks
        subtasks = self._extract_subtasks(complex_task)

        # Build task graph
        self._build_task_graph(subtasks)

        # Optimize for parallel execution
        execution_plan = self._optimize_execution_plan()

        # Create execution groups
        self.execution_groups = self._create_execution_groups(execution_plan)

        logger.info(f"Decomposed task into {len(self.execution_groups)} execution groups")

        return self.execution_groups

    def add_task_node(self, task_node: TaskNode):
        """Add a task node to the graph"""
        self.task_registry[task_node.task_id] = task_node
        self.task_graph.add_node(task_node.task_id, task=task_node)

        # Add dependencies as edges
        for dep_id in task_node.dependencies:
            if dep_id in self.task_registry:
                self.task_graph.add_edge(dep_id, task_node.task_id)

    def get_critical_path(self) -> List[str]:
        """Get the critical path through the task graph"""

        if not self.task_graph:
            return []

        # Find longest path (critical path)
        try:
            # Get all paths from sources to sinks
            sources = [n for n in self.task_graph.nodes() if self.task_graph.in_degree(n) == 0]
            sinks = [n for n in self.task_graph.nodes() if self.task_graph.out_degree(n) == 0]

            longest_path = []
            longest_duration = 0

            for source in sources:
                for sink in sinks:
                    try:
                        paths = list(nx.all_simple_paths(self.task_graph, source, sink))
                        for path in paths:
                            duration = sum(
                                self.task_registry[task_id].estimated_duration for task_id in path
                            )
                            if duration > longest_duration:
                                longest_duration = duration
                                longest_path = path
                    except nx.NetworkXNoPath:
                        continue

            return longest_path

        except Exception as e:
            logger.error(f"Error finding critical path: {e}")
            return []

    def get_parallelization_opportunities(self) -> List[Set[str]]:
        """Identify tasks that can be executed in parallel"""

        if not self.task_graph:
            return []

        # Find tasks at each level that can run in parallel
        parallel_groups = []

        try:
            # Topological generations give us parallel groups
            for generation in nx.topological_generations(self.task_graph):
                parallel_groups.append(set(generation))

            return parallel_groups

        except nx.NetworkXError as e:
            logger.error(f"Graph has cycles, cannot determine parallelization: {e}")
            return []

    def visualize_graph(self) -> str:
        """Generate a text visualization of the task graph"""

        if not self.task_graph:
            return "Empty task graph"

        lines = ["Task Decomposition Graph:"]
        lines.append("=" * 50)

        # Show execution groups
        for i, group in enumerate(self.execution_groups):
            lines.append(f"\nExecution Group {group.group_id}:")
            lines.append(f"  Parallel: {group.can_parallelize}")
            lines.append(f"  Estimated Duration: {group.total_estimated_duration:.1f}s")
            lines.append("  Tasks:")

            for task in group.tasks:
                status_icon = {"pending": "⏳", "running": "🔄", "completed": "✅", "failed": "❌"}.get(
                    task.status, "❓"
                )

                lines.append(f"    {status_icon} {task.task_id}: {task.description}")
                if task.dependencies:
                    lines.append(f"      Dependencies: {', '.join(task.dependencies)}")

        # Show critical path
        critical_path = self.get_critical_path()
        if critical_path:
            lines.append(f"\nCritical Path: {' -> '.join(critical_path)}")

        return "\n".join(lines)

    def _extract_subtasks(self, complex_task: Dict[str, Any]) -> List[TaskNode]:
        """Extract or generate subtasks from complex task"""

        subtasks = []

        # Check if subtasks are explicitly defined
        if "subtasks" in complex_task:
            for i, subtask_data in enumerate(complex_task["subtasks"]):
                task_node = TaskNode(
                    task_id=subtask_data.get("id", f"task_{i}"),
                    task_type=subtask_data.get("type", "generic"),
                    description=subtask_data.get("description", f"Subtask {i}"),
                    dependencies=set(subtask_data.get("dependencies", [])),
                    estimated_duration=subtask_data.get("duration", 10.0),
                    priority=subtask_data.get("priority", 0),
                    metadata=subtask_data.get("metadata", {}),
                )
                subtasks.append(task_node)
        else:
            # Generate subtasks based on task type
            subtasks = self._generate_subtasks(complex_task)

        return subtasks

    def _generate_subtasks(self, complex_task: Dict[str, Any]) -> List[TaskNode]:
        """Generate subtasks based on task type"""

        task_type = complex_task.get("type", "generic")
        subtasks = []

        if task_type == "code_implementation":
            subtasks = [
                TaskNode("research", "research", "Research requirements", set(), 5.0, 3),
                TaskNode("design", "design", "Design architecture", {"research"}, 10.0, 2),
                TaskNode("implement_core", "coding", "Implement core logic", {"design"}, 20.0, 1),
                TaskNode("implement_ui", "coding", "Implement UI", {"design"}, 15.0, 1),
                TaskNode("write_tests", "testing", "Write unit tests", {"implement_core"}, 10.0, 2),
                TaskNode(
                    "integration",
                    "testing",
                    "Integration testing",
                    {"implement_core", "implement_ui"},
                    10.0,
                    1,
                ),
                TaskNode(
                    "documentation",
                    "documentation",
                    "Write documentation",
                    {"implement_core"},
                    8.0,
                    3,
                ),
            ]
        elif task_type == "analysis":
            subtasks = [
                TaskNode("data_collection", "research", "Collect data", set(), 10.0, 1),
                TaskNode("data_cleaning", "processing", "Clean data", {"data_collection"}, 8.0, 2),
                TaskNode("analysis", "analysis", "Analyze data", {"data_cleaning"}, 15.0, 1),
                TaskNode(
                    "visualization", "visualization", "Create visualizations", {"analysis"}, 10.0, 2
                ),
                TaskNode(
                    "report",
                    "documentation",
                    "Generate report",
                    {"analysis", "visualization"},
                    12.0,
                    1,
                ),
            ]
        else:
            # Generic decomposition
            subtasks = [
                TaskNode("init", "initialization", "Initialize task", set(), 5.0, 3),
                TaskNode("process", "processing", "Process task", {"init"}, 15.0, 1),
                TaskNode("validate", "validation", "Validate results", {"process"}, 8.0, 2),
                TaskNode("finalize", "finalization", "Finalize task", {"validate"}, 5.0, 3),
            ]

        return subtasks

    def _build_task_graph(self, subtasks: List[TaskNode]):
        """Build directed graph from subtasks"""

        for task in subtasks:
            self.add_task_node(task)

    def _optimize_execution_plan(self) -> List[Set[str]]:
        """Optimize task execution for parallelism"""

        if not self.task_graph:
            return []

        # Check for cycles
        if not nx.is_directed_acyclic_graph(self.task_graph):
            raise ValueError("Task graph contains cycles - cannot create execution plan")

        # Use topological generations for natural parallelization
        parallel_groups = []

        for generation in nx.topological_generations(self.task_graph):
            # Split large groups if they exceed max parallel tasks
            if len(generation) > self.max_parallel_tasks:
                # Sort by priority and split
                sorted_tasks = sorted(
                    generation, key=lambda t: self.task_registry[t].priority, reverse=True
                )

                for i in range(0, len(sorted_tasks), self.max_parallel_tasks):
                    parallel_groups.append(set(sorted_tasks[i : i + self.max_parallel_tasks]))
            else:
                parallel_groups.append(set(generation))

        return parallel_groups

    def _create_execution_groups(self, execution_plan: List[Set[str]]) -> List[ExecutionGroup]:
        """Create execution groups from optimized plan"""

        groups = []

        for i, task_ids in enumerate(execution_plan):
            tasks = [self.task_registry[tid] for tid in task_ids]

            # Calculate total duration (max duration for parallel, sum for sequential)
            if len(tasks) > 1:
                # Parallel execution - duration is the longest task
                total_duration = max(t.estimated_duration for t in tasks)
                can_parallelize = True
            else:
                # Single task
                total_duration = tasks[0].estimated_duration if tasks else 0
                can_parallelize = False

            group = ExecutionGroup(
                group_id=i,
                tasks=tasks,
                total_estimated_duration=total_duration,
                can_parallelize=can_parallelize,
            )

            groups.append(group)

        return groups

#!/usr/bin/env python3
"""
Execution Plan Module for UnifiedOrchestrator
Provides execution planning, phase management, and dependency resolution
"""

import asyncio
import json
import logging
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import networkx as nx

from ..unified.orchestrator_module import ModuleConfig, OrchestratorModule

logger = logging.getLogger(__name__)


class ExecutionMode(Enum):
    """Execution modes for tasks"""

    SEQUENTIAL = "sequential"  # Tasks run one after another
    PARALLEL = "parallel"  # Tasks run simultaneously
    MIXED = "mixed"  # Combination based on dependencies
    ADAPTIVE = "adaptive"  # Dynamically adjust based on resources


class TaskPhase(Enum):
    """Phases of task execution"""

    PLANNING = "planning"
    PREPARATION = "preparation"
    EXECUTION = "execution"
    VALIDATION = "validation"
    CLEANUP = "cleanup"
    COMPLETE = "complete"


@dataclass
class ExecutionPhase:
    """Represents a phase in the execution plan"""

    phase_id: str
    name: str
    tasks: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)  # Other phase IDs
    execution_mode: ExecutionMode = ExecutionMode.PARALLEL
    priority: int = 0
    estimated_duration: float = 0
    actual_duration: Optional[float] = None
    status: str = "pending"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_task(self, task_id: str):
        """Add a task to this phase"""
        if task_id not in self.tasks:
            self.tasks.append(task_id)

    def remove_task(self, task_id: str):
        """Remove a task from this phase"""
        if task_id in self.tasks:
            self.tasks.remove(task_id)

    def is_ready(self, completed_phases: Set[str]) -> bool:
        """Check if this phase is ready to execute"""
        return all(dep in completed_phases for dep in self.dependencies)


@dataclass
class ExecutionPlan:
    """Complete execution plan for a set of tasks"""

    plan_id: str
    created_at: datetime = field(default_factory=datetime.now)
    phases: List[ExecutionPhase] = field(default_factory=list)
    task_graph: Optional[nx.DiGraph] = None
    phase_graph: Optional[nx.DiGraph] = None
    total_tasks: int = 0
    estimated_duration: float = 0
    actual_duration: Optional[float] = None
    status: str = "pending"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_phase(self, phase: ExecutionPhase):
        """Add a phase to the plan"""
        self.phases.append(phase)
        self.total_tasks += len(phase.tasks)
        self.estimated_duration += phase.estimated_duration

    def get_phase_by_id(self, phase_id: str) -> Optional[ExecutionPhase]:
        """Get a phase by its ID"""
        for phase in self.phases:
            if phase.phase_id == phase_id:
                return phase
        return None

    def get_next_phases(self, completed_phases: Set[str]) -> List[ExecutionPhase]:
        """Get the next phases that are ready to execute"""
        ready_phases = []
        for phase in self.phases:
            if phase.status == "pending" and phase.is_ready(completed_phases):
                ready_phases.append(phase)
        return sorted(ready_phases, key=lambda p: p.priority, reverse=True)

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "plan_id": self.plan_id,
            "created_at": self.created_at.isoformat(),
            "total_tasks": self.total_tasks,
            "estimated_duration": self.estimated_duration,
            "actual_duration": self.actual_duration,
            "status": self.status,
            "phases": [
                {
                    "phase_id": p.phase_id,
                    "name": p.name,
                    "tasks": p.tasks,
                    "dependencies": p.dependencies,
                    "execution_mode": p.execution_mode.value,
                    "priority": p.priority,
                    "status": p.status,
                }
                for p in self.phases
            ],
            "metadata": self.metadata,
        }


class ExecutionPlanModule(OrchestratorModule):
    """
    Module implementing execution planning and phase management.
    Creates optimal execution plans based on task dependencies and resources.
    """

    def __init__(self, orchestrator, config: ModuleConfig = None):
        super().__init__(orchestrator, config)
        self.plans: Dict[str, ExecutionPlan] = {}
        self.active_plan: Optional[ExecutionPlan] = None
        self.completed_phases: Set[str] = set()
        self.task_to_phase: Dict[str, str] = {}  # task_id -> phase_id
        self.phase_metrics: Dict[str, Dict] = defaultdict(
            lambda: {
                "tasks_completed": 0,
                "tasks_failed": 0,
                "total_duration": 0,
                "resource_usage": {},
            }
        )
        self.plans_dir = None

        # Planning configuration
        self.max_parallel_tasks = (
            config.config.get("max_parallel_tasks", 10) if config else 10
        )
        self.enable_adaptive_planning = (
            config.config.get("enable_adaptive", True) if config else True
        )
        self.phase_timeout = (
            config.config.get("phase_timeout", 600.0) if config else 600.0
        )

    @property
    def name(self) -> str:
        return "execution_plan"

    @property
    def description(self) -> str:
        return "Task execution planning with phases and dependency management"

    async def _initialize(self):
        """Initialize execution plan module"""
        # Setup plans directory
        self.plans_dir = self.orchestrator.output_dir / "execution_plans"
        self.plans_dir.mkdir(parents=True, exist_ok=True)

        # Check if networkx is available
        try:
            import networkx as nx

            self.has_networkx = True
        except ImportError:
            self.has_networkx = False
            logger.warning("NetworkX not available - graph-based planning disabled")

        logger.info(
            f"Execution plan module initialized (adaptive={self.enable_adaptive_planning})"
        )

    def create_plan(self, tasks: List["AgentTask"]) -> ExecutionPlan:
        """Create an execution plan from a list of tasks"""
        import uuid

        plan = ExecutionPlan(plan_id=str(uuid.uuid4()), total_tasks=len(tasks))

        # Build dependency graph if networkx is available
        if self.has_networkx:
            plan.task_graph = self._build_task_graph(tasks)
            plan.phase_graph = nx.DiGraph()

        # Group tasks into phases
        phases = self._create_phases(tasks)

        for phase in phases:
            plan.add_phase(phase)

            # Map tasks to phases
            for task_id in phase.tasks:
                self.task_to_phase[task_id] = phase.phase_id

        # Build phase dependency graph
        if self.has_networkx and plan.phase_graph:
            for phase in phases:
                plan.phase_graph.add_node(phase.phase_id, phase=phase)
                for dep in phase.dependencies:
                    plan.phase_graph.add_edge(dep, phase.phase_id)

        # Store plan
        self.plans[plan.plan_id] = plan
        self.active_plan = plan

        # Save plan to file
        self._save_plan(plan)

        logger.info(f"Created execution plan {plan.plan_id} with {len(phases)} phases")

        return plan

    def _build_task_graph(self, tasks: List["AgentTask"]) -> nx.DiGraph:
        """Build a directed graph of task dependencies"""
        graph = nx.DiGraph()

        # Add all tasks as nodes
        for task in tasks:
            graph.add_node(task.task_id, task=task)

        # Add dependency edges
        for task in tasks:
            if hasattr(task, "dependencies") and task.dependencies:
                for dep in task.dependencies:
                    if graph.has_node(dep):
                        graph.add_edge(dep, task.task_id)

        return graph

    def _create_phases(self, tasks: List["AgentTask"]) -> List[ExecutionPhase]:
        """Create execution phases from tasks"""
        phases = []

        if self.has_networkx:
            # Use topological sorting for phase creation
            phases = self._create_phases_with_graph(tasks)
        else:
            # Fallback to simple phase creation
            phases = self._create_simple_phases(tasks)

        return phases

    def _create_phases_with_graph(
        self, tasks: List["AgentTask"]
    ) -> List[ExecutionPhase]:
        """Create phases using graph analysis"""
        import uuid

        phases = []
        task_graph = self._build_task_graph(tasks)

        # Find strongly connected components (tasks that must run together)
        sccs = list(nx.strongly_connected_components(task_graph))

        # Find topological levels (tasks that can run in parallel)
        if nx.is_directed_acyclic_graph(task_graph):
            levels = self._topological_levels(task_graph)
        else:
            # Handle cycles by treating SCCs as single units
            condensed = nx.condensation(task_graph, scc=sccs)
            levels = self._topological_levels(condensed)

        # Create phases based on levels
        for level_idx, level_tasks in enumerate(levels):
            phase = ExecutionPhase(
                phase_id=str(uuid.uuid4()),
                name=f"Phase {level_idx + 1}",
                tasks=list(level_tasks),
                priority=len(levels) - level_idx,  # Higher priority for earlier phases
                execution_mode=ExecutionMode.PARALLEL
                if len(level_tasks) > 1
                else ExecutionMode.SEQUENTIAL,
            )

            # Set dependencies based on previous phases
            if level_idx > 0:
                phase.dependencies = [phases[level_idx - 1].phase_id]

            # Estimate duration based on tasks
            phase.estimated_duration = self._estimate_phase_duration(level_tasks, tasks)

            phases.append(phase)

        return phases

    def _topological_levels(self, graph: nx.DiGraph) -> List[Set[str]]:
        """Group nodes into topological levels"""
        levels = []
        remaining = set(graph.nodes())

        while remaining:
            # Find nodes with no dependencies in remaining set
            level = set()
            for node in remaining:
                predecessors = set(graph.predecessors(node))
                if not predecessors.intersection(remaining):
                    level.add(node)

            if not level:
                # Cycle detected, add remaining nodes as final level
                level = remaining.copy()

            levels.append(level)
            remaining -= level

        return levels

    def _create_simple_phases(self, tasks: List["AgentTask"]) -> List[ExecutionPhase]:
        """Create simple phases without graph analysis"""
        import uuid

        phases = []

        # Group tasks by priority and dependencies
        priority_groups = defaultdict(list)

        for task in tasks:
            priority = getattr(task, "priority", 0)
            priority_groups[priority].append(task)

        # Create phases for each priority group
        for priority in sorted(priority_groups.keys(), reverse=True):
            group_tasks = priority_groups[priority]

            # Split into dependent and independent tasks
            independent = []
            dependent = []

            for task in group_tasks:
                if hasattr(task, "dependencies") and task.dependencies:
                    dependent.append(task)
                else:
                    independent.append(task)

            # Create phase for independent tasks
            if independent:
                phase = ExecutionPhase(
                    phase_id=str(uuid.uuid4()),
                    name=f"Priority {priority} - Independent",
                    tasks=[t.task_id for t in independent],
                    priority=priority,
                    execution_mode=ExecutionMode.PARALLEL,
                )
                phases.append(phase)

            # Create phase for dependent tasks
            if dependent:
                phase = ExecutionPhase(
                    phase_id=str(uuid.uuid4()),
                    name=f"Priority {priority} - Dependent",
                    tasks=[t.task_id for t in dependent],
                    priority=priority,
                    execution_mode=ExecutionMode.MIXED,
                    dependencies=[phases[-1].phase_id] if phases else [],
                )
                phases.append(phase)

        return phases

    def _estimate_phase_duration(
        self, task_ids: Set[str], all_tasks: List["AgentTask"]
    ) -> float:
        """Estimate duration for a phase"""
        # Simple estimation based on task count and type
        base_duration = 10.0  # Base duration per task

        task_map = {t.task_id: t for t in all_tasks}
        total_duration = 0

        for task_id in task_ids:
            if task_id in task_map:
                task = task_map[task_id]
                # Adjust based on task type
                task_type = getattr(task, "task_type", "default")

                multiplier = {
                    "analysis": 2.0,
                    "synthesis": 3.0,
                    "validation": 1.5,
                    "simple": 0.5,
                }.get(task_type, 1.0)

                total_duration += base_duration * multiplier

        return total_duration

    def _save_plan(self, plan: ExecutionPlan):
        """Save execution plan to file"""
        plan_file = self.plans_dir / f"plan_{plan.plan_id}.json"
        plan_file.write_text(json.dumps(plan.to_dict(), indent=2, default=str))

    async def execute_plan(self, plan: ExecutionPlan) -> Dict[str, Any]:
        """Execute a complete plan"""
        start_time = datetime.now()
        plan.status = "executing"
        results = {
            "plan_id": plan.plan_id,
            "phases_completed": [],
            "phases_failed": [],
            "total_duration": 0,
            "success": True,
        }

        completed_phases = set()

        while True:
            # Get next phases to execute
            ready_phases = plan.get_next_phases(completed_phases)

            if not ready_phases:
                # Check if all phases are complete
                pending_phases = [p for p in plan.phases if p.status == "pending"]
                if not pending_phases:
                    break
                else:
                    # Deadlock or circular dependency
                    logger.error(
                        "No phases ready but pending phases exist - possible deadlock"
                    )
                    results["success"] = False
                    break

            # Execute ready phases
            if len(ready_phases) == 1:
                # Execute single phase
                await self._execute_phase(ready_phases[0])
            else:
                # Execute multiple phases in parallel
                tasks = [self._execute_phase(phase) for phase in ready_phases]
                await asyncio.gather(*tasks, return_exceptions=True)

            # Update completed phases
            for phase in ready_phases:
                if phase.status == "completed":
                    completed_phases.add(phase.phase_id)
                    results["phases_completed"].append(phase.phase_id)
                elif phase.status == "failed":
                    results["phases_failed"].append(phase.phase_id)
                    if not self.enable_adaptive_planning:
                        results["success"] = False
                        break

        # Calculate total duration
        end_time = datetime.now()
        plan.actual_duration = (end_time - start_time).total_seconds()
        results["total_duration"] = plan.actual_duration

        # Update plan status
        plan.status = "completed" if results["success"] else "failed"

        # Save final plan state
        self._save_plan(plan)

        logger.info(
            f"Plan {plan.plan_id} execution {'completed' if results['success'] else 'failed'} "
            f"in {plan.actual_duration:.2f}s"
        )

        return results

    async def _execute_phase(self, phase: ExecutionPhase):
        """Execute a single phase"""
        start_time = datetime.now()
        phase.status = "executing"

        logger.info(f"Executing phase {phase.name} with {len(phase.tasks)} tasks")

        try:
            # Execute tasks based on execution mode
            if phase.execution_mode == ExecutionMode.SEQUENTIAL:
                # Execute tasks one by one
                for task_id in phase.tasks:
                    # This would interact with the orchestrator to execute the actual task
                    await asyncio.sleep(0.1)  # Simulated execution

            elif phase.execution_mode == ExecutionMode.PARALLEL:
                # Execute all tasks in parallel
                # This would interact with the orchestrator to execute tasks
                await asyncio.sleep(0.1)  # Simulated execution

            elif phase.execution_mode == ExecutionMode.MIXED:
                # Execute based on dependencies within the phase
                await self._execute_mixed_phase(phase)

            elif phase.execution_mode == ExecutionMode.ADAPTIVE:
                # Dynamically adjust based on resources
                await self._execute_adaptive_phase(phase)

            # Update phase status
            phase.status = "completed"
            phase.actual_duration = (datetime.now() - start_time).total_seconds()

            # Update metrics
            self.phase_metrics[phase.phase_id]["total_duration"] = phase.actual_duration

        except Exception as e:
            logger.error(f"Phase {phase.name} failed: {e}")
            phase.status = "failed"
            phase.actual_duration = (datetime.now() - start_time).total_seconds()

    async def _execute_mixed_phase(self, phase: ExecutionPhase):
        """Execute phase with mixed mode (combination of parallel and sequential)"""
        # Group tasks by dependencies
        independent_tasks = []
        dependent_tasks = []

        for task_id in phase.tasks:
            # Check if task has dependencies within this phase
            has_internal_deps = False  # Simplified - would check actual dependencies

            if has_internal_deps:
                dependent_tasks.append(task_id)
            else:
                independent_tasks.append(task_id)

        # Execute independent tasks in parallel
        if independent_tasks:
            # Would execute via orchestrator
            await asyncio.sleep(0.1)  # Simulated

        # Execute dependent tasks sequentially
        for task_id in dependent_tasks:
            # Would execute via orchestrator
            await asyncio.sleep(0.1)  # Simulated

    async def _execute_adaptive_phase(self, phase: ExecutionPhase):
        """Execute phase with adaptive mode based on resource availability"""
        # Check current resource usage
        # This would interact with the monitoring module
        available_slots = self.max_parallel_tasks

        # Execute tasks in batches based on available resources
        task_queue = deque(phase.tasks)
        running_tasks = []

        while task_queue or running_tasks:
            # Start new tasks if slots available
            while task_queue and len(running_tasks) < available_slots:
                task_id = task_queue.popleft()
                # Would start task execution
                running_tasks.append(task_id)

            # Wait for some tasks to complete
            await asyncio.sleep(0.1)  # Simulated

            # Update running tasks (would check actual completion)
            running_tasks.clear()  # Simulated completion

    def validate_task(self, task: "AgentTask") -> Optional[str]:
        """Validate task for execution planning"""
        # Check if task fits in current plan
        if self.active_plan and hasattr(task, "task_id"):
            if task.task_id not in self.task_to_phase:
                return "Task not part of active execution plan"

        return None

    async def pre_task_execution(self, task: "AgentTask"):
        """Update execution plan before task execution"""
        if hasattr(task, "task_id") and task.task_id in self.task_to_phase:
            phase_id = self.task_to_phase[task.task_id]

            # Update task phase if available
            if hasattr(task, "phase"):
                task.phase = phase_id

            # Set execution mode from phase
            if self.active_plan:
                phase = self.active_plan.get_phase_by_id(phase_id)
                if phase and hasattr(task, "execution_mode"):
                    task.execution_mode = phase.execution_mode.value

    async def post_task_execution(self, task: "AgentTask"):
        """Update execution plan after task execution"""
        if hasattr(task, "task_id") and task.task_id in self.task_to_phase:
            phase_id = self.task_to_phase[task.task_id]

            # Update phase metrics
            if task.status == "completed":
                self.phase_metrics[phase_id]["tasks_completed"] += 1
            else:
                self.phase_metrics[phase_id]["tasks_failed"] += 1

    async def pre_batch_execution(self, tasks: List["AgentTask"]):
        """Create execution plan for batch"""
        if not self.active_plan:
            self.create_plan(tasks)

    def get_metrics(self) -> Dict[str, Any]:
        """Get execution planning metrics"""
        metrics = {
            "total_plans": len(self.plans),
            "active_plan": self.active_plan.plan_id if self.active_plan else None,
            "completed_phases": len(self.completed_phases),
            "phase_metrics": dict(self.phase_metrics),
        }

        if self.active_plan:
            metrics["active_plan_details"] = {
                "total_phases": len(self.active_plan.phases),
                "completed_phases": sum(
                    1 for p in self.active_plan.phases if p.status == "completed"
                ),
                "failed_phases": sum(
                    1 for p in self.active_plan.phases if p.status == "failed"
                ),
                "estimated_duration": self.active_plan.estimated_duration,
                "actual_duration": self.active_plan.actual_duration,
            }

        return metrics

    async def _cleanup(self):
        """Cleanup module resources"""
        # Save final execution plans
        if self.plans_dir:
            for plan in self.plans.values():
                self._save_plan(plan)

            # Save summary report
            report = {
                "timestamp": datetime.now().isoformat(),
                "total_plans": len(self.plans),
                "metrics": self.get_metrics(),
                "plans": [plan.to_dict() for plan in self.plans.values()],
            }

            report_file = (
                self.plans_dir
                / f"final_execution_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            )
            report_file.write_text(json.dumps(report, indent=2, default=str))

        logger.info("Execution plan module cleanup complete")

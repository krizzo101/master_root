"""
Load Balancing Orchestrator
Main coordinator for intelligent load balancing, task scheduling, and resource management
"""
import asyncio
import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

try:
    from ..generic_orchestrator import AgentTask, GenericOrchestrator
except ImportError:
    # Handle different import paths
    import sys

    sys.path.append(str(Path(__file__).parent.parent))
    from generic_orchestrator import AgentTask, GenericOrchestrator

from .load_balancer import (
    AgentPerformanceMetrics,
    DynamicLoadBalancer,
    LoadBalancingStrategy,
)
from .resource_monitor import (
    ResourceMonitor,
    SystemResources,
    get_global_resource_monitor,
)
from .task_scheduler import ScheduledTask, SchedulingPolicy, TaskPriority, TaskScheduler

logger = logging.getLogger(__name__)


@dataclass
class LoadBalancingConfiguration:
    """Configuration for load balancing orchestrator"""

    load_balancing_strategy: LoadBalancingStrategy = LoadBalancingStrategy.ADAPTIVE
    scheduling_policy: SchedulingPolicy = SchedulingPolicy.ADAPTIVE
    max_concurrent_per_agent: int = 3
    max_total_concurrent: int = 20
    resource_monitoring_interval: float = 1.0
    auto_scaling_enabled: bool = True
    performance_tracking_enabled: bool = True
    adaptive_threshold_cpu: float = 80.0
    adaptive_threshold_memory: float = 85.0


@dataclass
class LoadBalancingReport:
    """Comprehensive load balancing performance report"""

    timestamp: float = field(default_factory=time.time)
    total_tasks_processed: int = 0
    active_agents: int = 0
    current_load_distribution: Dict[str, Any] = field(default_factory=dict)
    resource_utilization: Dict[str, float] = field(default_factory=dict)
    performance_metrics: Dict[str, Any] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)
    efficiency_score: float = 0.0


class LoadBalancingOrchestrator:
    """Advanced orchestrator with integrated load balancing and resource management"""

    def __init__(
        self,
        output_dir: Union[str, Path],
        tokens: Optional[List[str]] = None,
        config: Optional[LoadBalancingConfiguration] = None,
    ):
        self.config = config or LoadBalancingConfiguration()

        # Initialize base orchestrator
        self.base_orchestrator = GenericOrchestrator(
            output_dir=output_dir,
            tokens=tokens,
            max_parallel=self.config.max_total_concurrent,
        )

        # Initialize load balancing components
        self.resource_monitor = get_global_resource_monitor()

        self.load_balancer = DynamicLoadBalancer(
            strategy=self.config.load_balancing_strategy,
            max_concurrent_per_agent=self.config.max_concurrent_per_agent,
            resource_monitor=self.resource_monitor,
        )

        self.task_scheduler = TaskScheduler(
            policy=self.config.scheduling_policy, max_queue_size=1000
        )

        # Register agents with load balancer
        self._initialize_agents()

        # Performance tracking
        self._execution_history: List[Dict[str, Any]] = []
        self._performance_baseline: Optional[Dict[str, float]] = None

        # Auto-scaling state
        self._last_scaling_decision = time.time()
        self._scaling_cooldown = 30.0  # seconds

        logger.info(
            "LoadBalancingOrchestrator initialized with %d agents",
            len(self.base_orchestrator.token_pool.tokens),
        )

    async def execute_batch_with_load_balancing(
        self, tasks: List[AgentTask], enable_scheduling: bool = True
    ) -> List[Dict]:
        """Execute tasks with intelligent load balancing and scheduling"""
        start_time = time.time()

        logger.info("Starting load-balanced execution of %d tasks", len(tasks))

        # Convert to scheduled tasks if scheduling is enabled
        if enable_scheduling:
            scheduled_tasks = self._convert_to_scheduled_tasks(tasks)

            # Add tasks to scheduler
            for scheduled_task in scheduled_tasks:
                self.task_scheduler.schedule_task(scheduled_task)

            # Execute with scheduling
            results = await self._execute_with_scheduling(scheduled_tasks)
        else:
            # Direct execution with load balancing only
            results = await self._execute_with_load_balancing_only(tasks)

        # Record performance metrics
        execution_time = time.time() - start_time
        self._record_execution_metrics(tasks, results, execution_time)

        # Auto-scaling decision
        if self.config.auto_scaling_enabled:
            await self._make_scaling_decision()

        logger.info("Load-balanced execution completed in %.2fs", execution_time)
        return results

    async def execute_with_dependencies_and_load_balancing(
        self, tasks: List[AgentTask]
    ) -> List[Dict]:
        """Execute tasks with dependencies, load balancing, and intelligent scheduling"""
        start_time = time.time()

        logger.info("Starting dependency-resolved execution with load balancing")

        # Build dependency graph
        dependency_map = self._build_dependency_map(tasks)

        # Convert to scheduled tasks with dependencies
        scheduled_tasks = []
        for task in tasks:
            priority = self._infer_task_priority(task)
            dependencies = dependency_map.get(task.task_id, [])

            scheduled_task = ScheduledTask(
                task_id=task.task_id,
                priority=priority,
                estimated_duration=self._estimate_task_duration(task),
                dependencies=dependencies,
                metadata={"original_task": task},
            )
            scheduled_tasks.append(scheduled_task)

        # Schedule all tasks (scheduler handles dependencies)
        for scheduled_task in scheduled_tasks:
            self.task_scheduler.schedule_task(scheduled_task)

        # Execute with dependency resolution
        results = await self._execute_with_dependencies_and_scheduling(scheduled_tasks)

        # Record metrics
        execution_time = time.time() - start_time
        self._record_execution_metrics(tasks, results, execution_time)

        logger.info("Dependency-resolved execution completed in %.2fs", execution_time)
        return results

    async def get_load_balancing_report(self) -> LoadBalancingReport:
        """Generate comprehensive load balancing performance report"""
        current_resources = self.resource_monitor.get_current_resources()
        load_distribution = self.load_balancer.get_load_distribution()
        performance_stats = self.load_balancer.get_performance_statistics()
        queue_status = self.task_scheduler.get_queue_status()

        # Calculate efficiency score
        efficiency_score = self._calculate_efficiency_score()

        # Generate recommendations
        recommendations = self._generate_optimization_recommendations()

        return LoadBalancingReport(
            total_tasks_processed=performance_stats["system_metrics"]["total_tasks"],
            active_agents=performance_stats["active_agents"],
            current_load_distribution=load_distribution,
            resource_utilization={
                "cpu": current_resources.cpu_percent if current_resources else 0,
                "memory": current_resources.memory_percent if current_resources else 0,
                "available_capacity": current_resources.available_capacity
                if current_resources
                else 0,
            },
            performance_metrics={
                "load_balancer_stats": performance_stats,
                "scheduler_stats": queue_status,
                "execution_history_count": len(self._execution_history),
            },
            recommendations=recommendations,
            efficiency_score=efficiency_score,
        )

    def configure_load_balancing(
        self,
        strategy: Optional[LoadBalancingStrategy] = None,
        policy: Optional[SchedulingPolicy] = None,
        max_concurrent: Optional[int] = None,
    ) -> None:
        """Dynamically configure load balancing parameters"""
        if strategy:
            self.load_balancer.set_strategy(strategy)
            self.config.load_balancing_strategy = strategy
            logger.info("Load balancing strategy updated to: %s", strategy.value)

        if policy:
            self.task_scheduler.set_policy(policy)
            self.config.scheduling_policy = policy
            logger.info("Scheduling policy updated to: %s", policy.value)

        if max_concurrent:
            self.config.max_total_concurrent = max_concurrent
            self.base_orchestrator.max_parallel = max_concurrent
            logger.info("Maximum concurrent tasks updated to: %d", max_concurrent)

    async def optimize_for_workload(
        self, workload_characteristics: Dict[str, Any]
    ) -> None:
        """Automatically optimize configuration based on workload characteristics"""
        task_count = workload_characteristics.get("task_count", 0)
        avg_duration = workload_characteristics.get("avg_duration", 60)
        priority_distribution = workload_characteristics.get(
            "priority_distribution", {}
        )
        has_dependencies = workload_characteristics.get("has_dependencies", False)

        # Strategy selection based on workload
        if has_dependencies and task_count > 20:
            recommended_strategy = LoadBalancingStrategy.RESOURCE_AWARE
            recommended_policy = SchedulingPolicy.DEADLINE_AWARE
        elif task_count > 50:
            recommended_strategy = LoadBalancingStrategy.PERFORMANCE_BASED
            recommended_policy = SchedulingPolicy.PRIORITY_QUEUE
        elif avg_duration < 30:  # Short tasks
            recommended_strategy = LoadBalancingStrategy.LEAST_LOADED
            recommended_policy = SchedulingPolicy.SHORTEST_JOB_FIRST
        else:
            recommended_strategy = LoadBalancingStrategy.ADAPTIVE
            recommended_policy = SchedulingPolicy.ADAPTIVE

        # Apply optimizations
        self.configure_load_balancing(
            strategy=recommended_strategy, policy=recommended_policy
        )

        logger.info(
            "Optimized for workload: strategy=%s, policy=%s",
            recommended_strategy.value,
            recommended_policy.value,
        )

    def _initialize_agents(self) -> None:
        """Initialize agents in the load balancer"""
        tokens = self.base_orchestrator.token_pool.tokens
        for i, token in enumerate(tokens):
            agent_id = f"agent_{i}"
            # Weight based on token position (first tokens might be premium)
            weight = 1.0 if i < len(tokens) // 2 else 0.8
            self.load_balancer.register_agent(agent_id, weight=weight)

        logger.info("Initialized %d agents in load balancer", len(tokens))

    def _convert_to_scheduled_tasks(
        self, tasks: List[AgentTask]
    ) -> List[ScheduledTask]:
        """Convert AgentTask to ScheduledTask with intelligent defaults"""
        scheduled_tasks = []

        for task in tasks:
            priority = self._infer_task_priority(task)
            estimated_duration = self._estimate_task_duration(task)

            scheduled_task = ScheduledTask(
                task_id=task.task_id,
                priority=priority,
                estimated_duration=estimated_duration,
                metadata={"original_task": task},
            )
            scheduled_tasks.append(scheduled_task)

        return scheduled_tasks

    def _infer_task_priority(self, task: AgentTask) -> TaskPriority:
        """Infer task priority from task characteristics"""
        # Simple heuristics - could be enhanced with ML
        task_type = task.task_type.lower()
        prompt_length = len(task.prompt)

        if "critical" in task_type or "urgent" in task.prompt.lower():
            return TaskPriority.CRITICAL
        elif "high" in task_type or prompt_length > 1000:
            return TaskPriority.HIGH
        elif "low" in task_type or "background" in task_type:
            return TaskPriority.LOW
        else:
            return TaskPriority.MEDIUM

    def _estimate_task_duration(self, task: AgentTask) -> float:
        """Estimate task execution duration"""
        # Simple heuristics - could use historical data or ML
        base_duration = 30.0  # seconds

        # Adjust based on prompt length
        prompt_complexity = len(task.prompt) / 100.0
        duration = base_duration + (prompt_complexity * 10)

        # Adjust based on task type
        if "research" in task.task_type.lower():
            duration *= 1.5
        elif "quick" in task.task_type.lower():
            duration *= 0.5

        return min(300.0, max(10.0, duration))  # Clamp between 10s and 5m

    def _build_dependency_map(self, tasks: List[AgentTask]) -> Dict[str, List[str]]:
        """Build dependency map from task dependencies"""
        dependency_map = {}
        for task in tasks:
            dependency_map[task.task_id] = task.dependencies
        return dependency_map

    async def _execute_with_load_balancing_only(
        self, tasks: List[AgentTask]
    ) -> List[Dict]:
        """Execute tasks with load balancing but no scheduling queue"""
        # Simple load-balanced execution
        task_results = {}
        pending_tasks = list(tasks)

        while pending_tasks or len(task_results) < len(tasks):
            # Get available agent
            if pending_tasks:
                task = pending_tasks.pop(0)
                agent_id = self.load_balancer.select_agent()

                if agent_id and self.load_balancer.assign_task(task.task_id, agent_id):
                    # Execute task
                    start_time = time.time()

                    # Use base orchestrator to execute single task
                    single_task_result = await self.base_orchestrator.execute_batch(
                        [task]
                    )

                    execution_time = time.time() - start_time
                    success = not single_task_result[0].get("is_error", False)

                    # Update load balancer
                    self.load_balancer.complete_task(
                        task.task_id, execution_time, success
                    )

                    task_results[task.task_id] = single_task_result[0]
                else:
                    # No available agent, wait briefly
                    await asyncio.sleep(0.1)
                    pending_tasks.append(task)
            else:
                await asyncio.sleep(0.1)

        return [task_results[task.task_id] for task in tasks]

    async def _execute_with_scheduling(
        self, scheduled_tasks: List[ScheduledTask]
    ) -> List[Dict]:
        """Execute tasks using the task scheduler"""
        task_results = {}

        while len(task_results) < len(scheduled_tasks):
            # Get next task from scheduler
            next_scheduled_task = self.task_scheduler.get_next_task()

            if next_scheduled_task:
                # Get agent for task
                agent_id = self.load_balancer.select_agent(next_scheduled_task.metadata)

                if agent_id and self.load_balancer.assign_task(
                    next_scheduled_task.task_id, agent_id
                ):
                    # Start task
                    self.task_scheduler.start_task(next_scheduled_task.task_id)

                    # Execute task
                    original_task = next_scheduled_task.metadata["original_task"]
                    start_time = time.time()

                    single_task_result = await self.base_orchestrator.execute_batch(
                        [original_task]
                    )

                    execution_time = time.time() - start_time
                    success = not single_task_result[0].get("is_error", False)

                    # Update components
                    self.load_balancer.complete_task(
                        next_scheduled_task.task_id, execution_time, success
                    )
                    self.task_scheduler.complete_task(
                        next_scheduled_task.task_id, execution_time, success
                    )

                    task_results[next_scheduled_task.task_id] = single_task_result[0]
                else:
                    # No available agent, brief wait
                    await asyncio.sleep(0.1)
            else:
                await asyncio.sleep(0.1)

        # Return results in original order
        return [task_results[task.task_id] for task in scheduled_tasks]

    async def _execute_with_dependencies_and_scheduling(
        self, scheduled_tasks: List[ScheduledTask]
    ) -> List[Dict]:
        """Execute tasks with dependency resolution and scheduling"""
        # This would be similar to _execute_with_scheduling but scheduler handles dependencies
        return await self._execute_with_scheduling(scheduled_tasks)

    def _record_execution_metrics(
        self, tasks: List[AgentTask], results: List[Dict], execution_time: float
    ) -> None:
        """Record execution metrics for performance analysis"""
        success_count = sum(
            1 for result in results if not result.get("is_error", False)
        )

        metrics = {
            "timestamp": time.time(),
            "task_count": len(tasks),
            "execution_time": execution_time,
            "success_rate": success_count / len(tasks),
            "throughput": len(tasks) / execution_time,
            "average_task_time": execution_time / len(tasks),
        }

        self._execution_history.append(metrics)

        # Keep only last 100 executions
        if len(self._execution_history) > 100:
            self._execution_history.pop(0)

    async def _make_scaling_decision(self) -> None:
        """Make intelligent scaling decisions based on system state"""
        current_time = time.time()
        if current_time - self._last_scaling_decision < self._scaling_cooldown:
            return

        current_resources = self.resource_monitor.get_current_resources()
        if not current_resources:
            return

        # Simple scaling logic
        if (
            current_resources.cpu_percent > self.config.adaptive_threshold_cpu
            or current_resources.memory_percent > self.config.adaptive_threshold_memory
        ):
            # Scale down
            if self.config.max_concurrent_per_agent > 1:
                self.config.max_concurrent_per_agent -= 1
                logger.info(
                    "Scaled down: max_concurrent_per_agent = %d",
                    self.config.max_concurrent_per_agent,
                )
        elif current_resources.available_capacity > 0.5:
            # Scale up
            if self.config.max_concurrent_per_agent < 5:
                self.config.max_concurrent_per_agent += 1
                logger.info(
                    "Scaled up: max_concurrent_per_agent = %d",
                    self.config.max_concurrent_per_agent,
                )

        self._last_scaling_decision = current_time

    def _calculate_efficiency_score(self) -> float:
        """Calculate overall system efficiency score (0-100)"""
        if not self._execution_history:
            return 50.0

        # Recent performance metrics
        recent_metrics = self._execution_history[-10:]  # Last 10 executions

        avg_success_rate = sum(m["success_rate"] for m in recent_metrics) / len(
            recent_metrics
        )
        avg_throughput = sum(m["throughput"] for m in recent_metrics) / len(
            recent_metrics
        )

        # Resource utilization
        current_resources = self.resource_monitor.get_current_resources()
        resource_efficiency = 1.0
        if current_resources:
            # Prefer moderate resource usage (not too high, not too low)
            cpu_efficiency = 1.0 - abs(current_resources.cpu_percent - 60) / 100
            memory_efficiency = 1.0 - abs(current_resources.memory_percent - 60) / 100
            resource_efficiency = (cpu_efficiency + memory_efficiency) / 2

        # Combine factors
        efficiency = (
            avg_success_rate * 0.4
            + min(avg_throughput / 10, 1.0) * 0.3
            + resource_efficiency * 0.3
        ) * 100

        return round(max(0, min(100, efficiency)), 2)

    def _generate_optimization_recommendations(self) -> List[str]:
        """Generate optimization recommendations"""
        recommendations = []

        # Get current system state
        current_resources = self.resource_monitor.get_current_resources()
        load_stats = self.load_balancer.get_performance_statistics()

        if current_resources:
            if current_resources.is_high_load:
                recommendations.append(
                    "System under high load - consider reducing concurrency"
                )
                recommendations.append(
                    "Switch to LEAST_LOADED strategy to distribute load evenly"
                )
            elif current_resources.available_capacity > 0.6:
                recommendations.append(
                    "System has available capacity - consider increasing concurrency"
                )

        # Load balancing recommendations
        success_rate = load_stats["system_metrics"]["recent_success_rate"]
        if success_rate < 0.8:
            recommendations.append(
                "Low success rate - consider PERFORMANCE_BASED strategy"
            )

        return recommendations[:5]


# Convenience function for load-balanced execution
async def execute_with_intelligent_load_balancing(
    tasks: List[AgentTask],
    output_dir: Union[str, Path],
    tokens: Optional[List[str]] = None,
    strategy: LoadBalancingStrategy = LoadBalancingStrategy.ADAPTIVE,
    enable_scheduling: bool = True,
) -> tuple[List[Dict], LoadBalancingReport]:
    """Execute tasks with intelligent load balancing and return results + report"""

    config = LoadBalancingConfiguration(load_balancing_strategy=strategy)
    orchestrator = LoadBalancingOrchestrator(output_dir, tokens, config)

    results = await orchestrator.execute_batch_with_load_balancing(
        tasks, enable_scheduling=enable_scheduling
    )

    report = await orchestrator.get_load_balancing_report()

    return results, report

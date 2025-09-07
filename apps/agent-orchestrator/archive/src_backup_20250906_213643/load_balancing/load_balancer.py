"""
Dynamic Load Balancer
Intelligent task distribution based on system resources and agent performance
"""
import asyncio
import logging
import math
import random
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple

from .resource_monitor import (
    ResourceMonitor,
    SystemResources,
    get_global_resource_monitor,
)

logger = logging.getLogger(__name__)


class LoadBalancingStrategy(Enum):
    """Load balancing strategies"""

    ROUND_ROBIN = "round_robin"
    LEAST_LOADED = "least_loaded"
    WEIGHTED_ROUND_ROBIN = "weighted_round_robin"
    RESOURCE_AWARE = "resource_aware"
    PERFORMANCE_BASED = "performance_based"
    ADAPTIVE = "adaptive"


@dataclass
class AgentPerformanceMetrics:
    """Performance metrics for individual agents"""

    agent_id: str
    total_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    average_execution_time: float = 0.0
    total_execution_time: float = 0.0
    current_load: int = 0
    success_rate: float = 1.0
    last_updated: float = field(default_factory=time.time)

    @property
    def is_available(self) -> bool:
        """Check if agent is available for new tasks"""
        return self.current_load == 0

    @property
    def efficiency_score(self) -> float:
        """Calculate agent efficiency score (0-1, higher is better)"""
        if self.total_tasks == 0:
            return 1.0

        # Combine success rate and execution time efficiency
        time_efficiency = 1.0 / (1.0 + self.average_execution_time / 10.0)  # Normalize
        return (self.success_rate * 0.7) + (time_efficiency * 0.3)


@dataclass
class ResourceMetrics:
    """System resource metrics for load balancing decisions"""

    cpu_utilization: float
    memory_utilization: float
    available_capacity: float
    load_trend: float = 0.0  # Positive = increasing load
    timestamp: float = field(default_factory=time.time)

    @property
    def can_accept_tasks(self) -> bool:
        """Check if system can accept more tasks"""
        return (
            self.cpu_utilization < 85
            and self.memory_utilization < 90
            and self.available_capacity > 0.1
        )

    @property
    def recommended_concurrency(self) -> int:
        """Recommend optimal concurrency level"""
        if not self.can_accept_tasks:
            return 1

        # Base concurrency on available capacity
        base_concurrency = max(1, int(self.available_capacity * 10))

        # Adjust based on load trend
        if self.load_trend > 0:
            return max(1, base_concurrency - 1)
        else:
            return min(20, base_concurrency + 1)


class DynamicLoadBalancer:
    """Intelligent load balancer with adaptive strategies"""

    def __init__(
        self,
        strategy: LoadBalancingStrategy = LoadBalancingStrategy.ADAPTIVE,
        max_concurrent_per_agent: int = 3,
        resource_monitor: Optional[ResourceMonitor] = None,
    ):
        self.strategy = strategy
        self.max_concurrent_per_agent = max_concurrent_per_agent
        self.resource_monitor = resource_monitor or get_global_resource_monitor()

        # Agent management
        self._agents: Dict[str, AgentPerformanceMetrics] = {}
        self._agent_weights: Dict[str, float] = {}
        self._round_robin_index = 0

        # Task tracking
        self._active_tasks: Dict[str, str] = {}  # task_id -> agent_id
        self._task_queue: deque = deque()
        self._completed_tasks_history = deque(maxlen=1000)

        # Strategy state
        self._strategy_state: Dict[str, Any] = {}
        self._last_resource_check = 0
        self._resource_check_interval = 5.0  # seconds

        # Performance tracking
        self._decision_history = deque(maxlen=500)

        logger.info("DynamicLoadBalancer initialized with strategy: %s", strategy.value)

    def register_agent(self, agent_id: str, weight: float = 1.0) -> None:
        """Register a new agent for load balancing"""
        self._agents[agent_id] = AgentPerformanceMetrics(agent_id=agent_id)
        self._agent_weights[agent_id] = weight

        logger.info("Registered agent %s with weight %.2f", agent_id, weight)

    def unregister_agent(self, agent_id: str) -> None:
        """Unregister an agent"""
        if agent_id in self._agents:
            del self._agents[agent_id]
            del self._agent_weights[agent_id]

            # Remove from active tasks
            tasks_to_remove = [
                task_id
                for task_id, aid in self._active_tasks.items()
                if aid == agent_id
            ]
            for task_id in tasks_to_remove:
                del self._active_tasks[task_id]

            logger.info("Unregistered agent %s", agent_id)

    def select_agent(
        self, task_metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """Select best agent for a task based on current strategy"""
        if not self._agents:
            return None

        # Update resource metrics
        self._update_resource_metrics()

        # Apply strategy-specific selection
        if self.strategy == LoadBalancingStrategy.ROUND_ROBIN:
            return self._select_round_robin()
        elif self.strategy == LoadBalancingStrategy.LEAST_LOADED:
            return self._select_least_loaded()
        elif self.strategy == LoadBalancingStrategy.WEIGHTED_ROUND_ROBIN:
            return self._select_weighted_round_robin()
        elif self.strategy == LoadBalancingStrategy.RESOURCE_AWARE:
            return self._select_resource_aware()
        elif self.strategy == LoadBalancingStrategy.PERFORMANCE_BASED:
            return self._select_performance_based()
        elif self.strategy == LoadBalancingStrategy.ADAPTIVE:
            return self._select_adaptive(task_metadata)
        else:
            return self._select_least_loaded()  # Default fallback

    def assign_task(self, task_id: str, agent_id: str) -> bool:
        """Assign a task to a specific agent"""
        if agent_id not in self._agents:
            logger.error("Cannot assign task to unknown agent: %s", agent_id)
            return False

        agent_metrics = self._agents[agent_id]

        # Check if agent can accept more tasks
        if agent_metrics.current_load >= self.max_concurrent_per_agent:
            logger.warning(
                "Agent %s at maximum capacity (%d tasks)",
                agent_id,
                agent_metrics.current_load,
            )
            return False

        # Assign task
        self._active_tasks[task_id] = agent_id
        agent_metrics.current_load += 1
        agent_metrics.total_tasks += 1

        # Record decision
        self._decision_history.append(
            {
                "timestamp": time.time(),
                "task_id": task_id,
                "agent_id": agent_id,
                "strategy": self.strategy.value,
                "agent_load": agent_metrics.current_load,
            }
        )

        logger.debug(
            "Assigned task %s to agent %s (load: %d)",
            task_id,
            agent_id,
            agent_metrics.current_load,
        )
        return True

    def complete_task(
        self, task_id: str, execution_time: float, success: bool = True
    ) -> None:
        """Mark a task as completed and update agent metrics"""
        if task_id not in self._active_tasks:
            logger.warning("Task %s not found in active tasks", task_id)
            return

        agent_id = self._active_tasks[task_id]
        agent_metrics = self._agents.get(agent_id)

        if not agent_metrics:
            logger.error("Agent %s not found for completed task %s", agent_id, task_id)
            return

        # Update agent metrics
        agent_metrics.current_load = max(0, agent_metrics.current_load - 1)
        agent_metrics.total_execution_time += execution_time

        if success:
            agent_metrics.completed_tasks += 1
        else:
            agent_metrics.failed_tasks += 1

        # Update averages
        if agent_metrics.completed_tasks > 0:
            agent_metrics.average_execution_time = (
                agent_metrics.total_execution_time / agent_metrics.completed_tasks
            )
            agent_metrics.success_rate = (
                agent_metrics.completed_tasks / agent_metrics.total_tasks
            )

        agent_metrics.last_updated = time.time()

        # Remove from active tasks
        del self._active_tasks[task_id]

        # Add to history
        self._completed_tasks_history.append(
            {
                "task_id": task_id,
                "agent_id": agent_id,
                "execution_time": execution_time,
                "success": success,
                "timestamp": time.time(),
            }
        )

        logger.debug(
            "Task %s completed on agent %s (%.2fs, %s)",
            task_id,
            agent_id,
            execution_time,
            "success" if success else "failed",
        )

    def get_load_distribution(self) -> Dict[str, Any]:
        """Get current load distribution across agents"""
        total_load = sum(metrics.current_load for metrics in self._agents.values())

        distribution = {"total_active_tasks": total_load, "agents": {}}

        for agent_id, metrics in self._agents.items():
            distribution["agents"][agent_id] = {
                "current_load": metrics.current_load,
                "total_tasks": metrics.total_tasks,
                "completed_tasks": metrics.completed_tasks,
                "success_rate": metrics.success_rate,
                "average_execution_time": metrics.average_execution_time,
                "efficiency_score": metrics.efficiency_score,
                "load_percentage": (metrics.current_load / total_load * 100)
                if total_load > 0
                else 0,
            }

        return distribution

    def get_performance_statistics(self) -> Dict[str, Any]:
        """Get performance statistics and recommendations"""
        current_resources = self.resource_monitor.get_current_resources()
        avg_resources = self.resource_monitor.get_average_resources(300)  # 5 minutes

        # Calculate system-wide metrics
        total_tasks = sum(metrics.total_tasks for metrics in self._agents.values())
        total_completed = sum(
            metrics.completed_tasks for metrics in self._agents.values()
        )
        total_failed = sum(metrics.failed_tasks for metrics in self._agents.values())

        overall_success_rate = (
            (total_completed / total_tasks) if total_tasks > 0 else 1.0
        )

        # Recent performance (last 100 tasks)
        recent_tasks = list(self._completed_tasks_history)[-100:]
        recent_success_rate = (
            (sum(1 for t in recent_tasks if t["success"]) / len(recent_tasks))
            if recent_tasks
            else 1.0
        )
        recent_avg_time = (
            (sum(t["execution_time"] for t in recent_tasks) / len(recent_tasks))
            if recent_tasks
            else 0.0
        )

        return {
            "strategy": self.strategy.value,
            "total_agents": len(self._agents),
            "active_agents": sum(
                1 for m in self._agents.values() if m.current_load > 0
            ),
            "total_active_tasks": sum(m.current_load for m in self._agents.values()),
            "system_metrics": {
                "total_tasks": total_tasks,
                "completed_tasks": total_completed,
                "failed_tasks": total_failed,
                "overall_success_rate": round(overall_success_rate, 3),
                "recent_success_rate": round(recent_success_rate, 3),
                "recent_average_execution_time": round(recent_avg_time, 2),
            },
            "resource_metrics": {
                "current_cpu": current_resources.cpu_percent
                if current_resources
                else 0,
                "current_memory": current_resources.memory_percent
                if current_resources
                else 0,
                "average_cpu": avg_resources.cpu_percent if avg_resources else 0,
                "average_memory": avg_resources.memory_percent if avg_resources else 0,
                "available_capacity": current_resources.available_capacity
                if current_resources
                else 0.5,
            },
            "recommendations": self._generate_recommendations(),
        }

    def _select_round_robin(self) -> Optional[str]:
        """Round-robin selection strategy"""
        available_agents = [
            aid
            for aid, metrics in self._agents.items()
            if metrics.current_load < self.max_concurrent_per_agent
        ]

        if not available_agents:
            return None

        # Simple round-robin
        selected = available_agents[self._round_robin_index % len(available_agents)]
        self._round_robin_index += 1
        return selected

    def _select_least_loaded(self) -> Optional[str]:
        """Select agent with least current load"""
        available_agents = [
            (aid, metrics.current_load)
            for aid, metrics in self._agents.items()
            if metrics.current_load < self.max_concurrent_per_agent
        ]

        if not available_agents:
            return None

        # Sort by load and return the least loaded
        available_agents.sort(key=lambda x: x[1])
        return available_agents[0][0]

    def _select_weighted_round_robin(self) -> Optional[str]:
        """Weighted round-robin based on agent weights"""
        available_agents = [
            (aid, self._agent_weights.get(aid, 1.0))
            for aid, metrics in self._agents.items()
            if metrics.current_load < self.max_concurrent_per_agent
        ]

        if not available_agents:
            return None

        # Weighted selection
        total_weight = sum(weight for _, weight in available_agents)
        if total_weight == 0:
            return available_agents[0][0]

        # Random weighted selection
        r = random.uniform(0, total_weight)
        cumulative_weight = 0

        for agent_id, weight in available_agents:
            cumulative_weight += weight
            if r <= cumulative_weight:
                return agent_id

        return available_agents[-1][0]  # Fallback

    def _select_resource_aware(self) -> Optional[str]:
        """Select agent based on system resource availability"""
        current_resources = self.resource_monitor.get_current_resources()
        if not current_resources:
            return self._select_least_loaded()

        available_agents = [
            aid
            for aid, metrics in self._agents.items()
            if metrics.current_load < self.max_concurrent_per_agent
        ]

        if not available_agents:
            return None

        # Adjust selection based on system load
        if current_resources.is_high_load:
            # Under high load, prefer agents with least current load
            return self._select_least_loaded()
        elif current_resources.is_moderate_load:
            # Under moderate load, balance between load and performance
            return self._select_performance_based()
        else:
            # Under low load, can use any available agent
            return self._select_round_robin()

    def _select_performance_based(self) -> Optional[str]:
        """Select agent based on performance metrics"""
        available_agents = [
            (aid, metrics)
            for aid, metrics in self._agents.items()
            if metrics.current_load < self.max_concurrent_per_agent
        ]

        if not available_agents:
            return None

        # Score agents based on efficiency and current load
        scored_agents = []
        for agent_id, metrics in available_agents:
            # Higher efficiency is better, lower load is better
            load_factor = 1.0 / (1.0 + metrics.current_load)
            score = metrics.efficiency_score * load_factor
            scored_agents.append((agent_id, score))

        # Return agent with highest score
        scored_agents.sort(key=lambda x: x[1], reverse=True)
        return scored_agents[0][0]

    def _select_adaptive(
        self, task_metadata: Optional[Dict[str, Any]]
    ) -> Optional[str]:
        """Adaptive strategy that switches based on conditions"""
        current_resources = self.resource_monitor.get_current_resources()

        # Decide strategy based on current conditions
        if not current_resources:
            return self._select_least_loaded()

        total_active_tasks = sum(m.current_load for m in self._agents.values())
        avg_success_rate = (
            (sum(m.success_rate for m in self._agents.values()) / len(self._agents))
            if self._agents
            else 1.0
        )

        # Strategy selection logic
        if current_resources.is_high_load:
            # Under high load, minimize resource usage
            return self._select_least_loaded()
        elif avg_success_rate < 0.8:
            # Low success rate, focus on performance
            return self._select_performance_based()
        elif total_active_tasks > len(self._agents) * 2:
            # High task volume, use weighted distribution
            return self._select_weighted_round_robin()
        else:
            # Normal conditions, use resource-aware
            return self._select_resource_aware()

    def _update_resource_metrics(self) -> None:
        """Update resource metrics if needed"""
        current_time = time.time()
        if current_time - self._last_resource_check > self._resource_check_interval:
            # Update resource information
            resources = self.resource_monitor.get_current_resources()
            if resources:
                self._strategy_state["last_resources"] = resources

            self._last_resource_check = current_time

    def _generate_recommendations(self) -> List[str]:
        """Generate optimization recommendations"""
        recommendations = []
        current_resources = self.resource_monitor.get_current_resources()

        if current_resources:
            if current_resources.is_high_load:
                recommendations.append(
                    "System under high load - consider reducing concurrent tasks"
                )
            elif current_resources.available_capacity > 0.7:
                recommendations.append(
                    "System has high available capacity - consider increasing parallelism"
                )

        # Agent-based recommendations
        agent_loads = [m.current_load for m in self._agents.values()]
        if agent_loads:
            max_load = max(agent_loads)
            min_load = min(agent_loads)

            if max_load - min_load > 2:
                recommendations.append(
                    "Uneven load distribution - consider rebalancing"
                )

        # Performance recommendations
        low_performing_agents = [
            aid
            for aid, metrics in self._agents.items()
            if metrics.success_rate < 0.8 and metrics.total_tasks > 5
        ]
        if low_performing_agents:
            recommendations.append(
                f"Low performing agents detected: {', '.join(low_performing_agents)}"
            )

        return recommendations[:5]  # Limit to top 5 recommendations

    def set_strategy(self, strategy: LoadBalancingStrategy) -> None:
        """Change load balancing strategy"""
        old_strategy = self.strategy
        self.strategy = strategy
        self._strategy_state.clear()  # Reset strategy state

        logger.info(
            "Load balancing strategy changed from %s to %s",
            old_strategy.value,
            strategy.value,
        )

    def get_agent_metrics(self, agent_id: str) -> Optional[AgentPerformanceMetrics]:
        """Get metrics for specific agent"""
        return self._agents.get(agent_id)

    def reset_metrics(self) -> None:
        """Reset all performance metrics"""
        for metrics in self._agents.values():
            metrics.total_tasks = 0
            metrics.completed_tasks = 0
            metrics.failed_tasks = 0
            metrics.average_execution_time = 0.0
            metrics.total_execution_time = 0.0
            metrics.success_rate = 1.0

        self._completed_tasks_history.clear()
        self._decision_history.clear()

        logger.info("All load balancer metrics reset")

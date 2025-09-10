"""
Metrics Calculator

Calculates performance and collaboration metrics for agent swarms.
"""

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class CollaborationMetrics:
    """Comprehensive collaboration metrics."""

    # Basic counts
    active_agents: int = 0
    total_spawns: int = 0
    total_communications: int = 0
    total_collaborations: int = 0

    # Performance metrics
    avg_response_time: float = 0.0
    collaboration_efficiency: float = 0.0
    network_density: float = 0.0

    # Trends (per minute rates)
    spawn_rate: float = 0.0
    communication_rate: float = 0.0
    error_rate: float = 0.0

    # Quality indicators
    conflict_rate: float = 0.0
    success_rate: float = 0.0
    coordination_score: float = 0.0


class MetricsCalculator:
    """Calculates collaboration and performance metrics."""

    def __init__(self, settings):
        self.settings = settings
        self.metrics_history: List[CollaborationMetrics] = []
        self.last_calculation: float = 0.0

    async def update_metrics(self, active_sessions: Dict) -> CollaborationMetrics:
        """Calculate current metrics from active sessions."""
        current_time = time.time()

        metrics = CollaborationMetrics()
        metrics.active_agents = len(active_sessions)

        # Calculate basic counts
        for session in active_sessions.values():
            metrics.total_spawns += len(session.agents_spawned)
            metrics.total_communications += len(session.communication_partners)
            metrics.total_collaborations += len(session.collaboration_events)

        # Calculate rates (events per minute)
        if self.metrics_history:
            time_window = 60.0  # 1 minute
            recent_metrics = [
                m
                for m in self.metrics_history
                if current_time - self.last_calculation <= time_window
            ]

            if recent_metrics:
                prev_metrics = recent_metrics[0]
                time_delta = current_time - self.last_calculation

                if time_delta > 0:
                    spawn_delta = metrics.total_spawns - prev_metrics.total_spawns
                    comm_delta = (
                        metrics.total_communications - prev_metrics.total_communications
                    )

                    metrics.spawn_rate = (spawn_delta / time_delta) * 60.0
                    metrics.communication_rate = (comm_delta / time_delta) * 60.0

        # Calculate collaboration efficiency
        if metrics.active_agents > 1:
            actual_collaborations = sum(
                1
                for session in active_sessions.values()
                if len(session.communication_partners) > 0
            )
            metrics.collaboration_efficiency = (
                actual_collaborations / metrics.active_agents
            )

        # Store metrics
        self.metrics_history.append(metrics)
        if len(self.metrics_history) > 100:  # Keep last 100 metrics
            self.metrics_history.pop(0)

        self.last_calculation = current_time

        return metrics

    async def get_current_metrics(self) -> CollaborationMetrics:
        """Get the most recent metrics."""
        if self.metrics_history:
            return self.metrics_history[-1]
        return CollaborationMetrics()

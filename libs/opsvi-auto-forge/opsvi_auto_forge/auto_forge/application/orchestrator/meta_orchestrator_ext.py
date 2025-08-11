"""Meta orchestrator extensions for decision kernel integration."""

from __future__ import annotations
from typing import Any, Dict
from uuid import UUID

from opsvi_auto_forge.core.decision_kernel.analyzer import analyze_task
from opsvi_auto_forge.core.decision_kernel.strategies import select_strategy
from opsvi_auto_forge.core.decision_kernel.models import RouteDecision


async def plan_and_route(
    task_data: Dict[str, Any], policies: Dict[str, Any]
) -> RouteDecision:
    """Plan and route a task using the decision kernel.

    Args:
        task_data: Task information including id, agent, type, inputs
        policies: Policy constraints and preferences

    Returns:
        RouteDecision with strategy and model selection
    """
    # Analyze task
    analysis = await analyze_task(
        task_id=task_data["id"],
        agent=task_data["agent"],
        task_type=task_data["type"],
        inputs=task_data.get("inputs", {}),
        budget_hint=policies.get("budget", {}),
    )

    # Get historical data (simplified - in real implementation would query Neo4j)
    priors = {
        "avg_cost": 0.05,
        "avg_tokens": 500,
        "avg_duration": 30.0,
        "success_rate": 0.85,
        "total_executions": 100,
    }

    # Select strategy
    route_decision = await select_strategy(analysis, policies, priors)

    return route_decision

from __future__ import annotations

from typing import Any, Dict

from opsvi_auto_forge.core.decision_kernel.models import RouteDecision


def route_with_decision(
    task: Dict[str, Any], decision: RouteDecision
) -> Dict[str, Any]:
    """Shim to pass decision hints into the existing router.

    Returns router parameters (do not execute here).
    """
    return {
        "task_id": str(decision.task_id),
        "agent": task.get("agent"),
        "model": decision.model,
        "strategy": decision.strategy,
        "k_samples": decision.k_samples,
        "verifier_model": decision.verifier_model,
    }

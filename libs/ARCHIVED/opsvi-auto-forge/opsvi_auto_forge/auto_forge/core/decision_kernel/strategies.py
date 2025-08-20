from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict
from uuid import UUID

from .models import RouteDecision

logger = logging.getLogger(__name__)


def _choose_model(features: Dict[str, Any], priors: Dict[str, Any]) -> str:
    """Choose model using bandit-based selection with fallback to rule-based logic."""
    try:
        from opsvi_auto_forge.core.model_selection.bandit_selector import (
            select_model_bandit,
        )

        # Get available models from priors
        available_models = list(priors.get("models", {}).keys())
        if not available_models:
            # Fallback to default models
            available_models = ["o4-mini", "o3", "gpt-4o-mini"]

        # Use bandit selection
        selected_model = asyncio.run(select_model_bandit(available_models))
        return selected_model

    except Exception as e:
        logger.warning(f"Bandit selection failed, using fallback: {e}")
        # Fallback to rule-based selection
        if features.get("complexity", 0.0) > 0.7 or features.get("risk", 0.0) > 0.6:
            return "o3"
        return "o4-mini"


async def select_strategy(
    features: Dict[str, Any], policies: Dict[str, Any], priors: Dict[str, Any]
) -> RouteDecision:
    """Budget-aware strategy selection.

    Policies may include min_confidence, max_cost_usd, strategy_for_agent, etc.
    Priors hold empirical success rates per strategy/model.
    """
    model = _choose_model(features, priors)
    strategy = "single"
    k_samples = 1
    max_thoughts = 0
    reason = "Default single-shot chosen; low-medium complexity."

    if features.get("complexity", 0.0) >= 0.5:
        strategy = "self_consistency"
        k_samples = 5
        reason = "Moderate complexity → self-consistency (k=5)."

    if features.get("risk", 0.0) >= 0.7:
        strategy = "solver_verifier"
        reason = "High risk → solver/verifier pattern."

    return RouteDecision(
        task_id=UUID(features["task_id"]),
        strategy=strategy,
        model=model,
        k_samples=k_samples,
        max_thoughts=max_thoughts,
        verifier_model=policies.get("verifier", "gpt-4.1"),
        p_pass=0.0,
        confidence=0.0,
        reason=reason,
        params={"features": features},
    )

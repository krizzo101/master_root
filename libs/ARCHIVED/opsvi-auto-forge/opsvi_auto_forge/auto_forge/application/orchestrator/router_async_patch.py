from __future__ import annotations

from typing import Any, Dict, Optional


class EscalationDecision(Dict[str, Any]):
    pass


PRICE_TABLE = {
    # approximate; replace with project-accurate values
    "o4-mini": {"input_per_1k": 0.0003, "output_per_1k": 0.0012},
    "gpt-4.1": {"input_per_1k": 0.005, "output_per_1k": 0.015},
    "o3": {"input_per_1k": 0.010, "output_per_1k": 0.030},
}


def estimate_cost_usd(model: str, input_tokens: int, output_tokens: int) -> float:
    p = PRICE_TABLE.get(model, PRICE_TABLE["gpt-4.1"])
    return (input_tokens / 1000.0) * p["input_per_1k"] + (output_tokens / 1000.0) * p[
        "output_per_1k"
    ]


async def route_task(
    *,  # enforce kw-only
    model_hint: str,
    strategy: str,
    k_samples: int,
    verifier_model: Optional[str],
    budget_usd_remaining: float,
    confidence_min: float,
    last_confidence: Optional[float] = None,
    last_verifier_passed: Optional[bool] = None,
) -> EscalationDecision:
    """Async-safe router core that can be called by the orchestrator.

    Returns an object containing selected_model and whether escalation occurred.
    """
    model_chain = ["o4-mini", "gpt-4.1", "o3"]
    # Choose starting point
    try:
        idx = model_chain.index(model_hint)
    except ValueError:
        idx = 0
    selected = model_chain[idx]

    # Decide escalation
    escalate = False
    reason = "initial"
    if last_verifier_passed is False or (
        last_confidence is not None and last_confidence < confidence_min
    ):
        if idx + 1 < len(model_chain):
            selected = model_chain[idx + 1]
            escalate = True
            reason = "verification_failed_or_low_confidence"

    return EscalationDecision(
        selected_model=selected,
        escalated=escalate,
        reason=reason,
        strategy=strategy,
        k_samples=k_samples,
        verifier_model=verifier_model,
    )

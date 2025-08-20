from __future__ import annotations

from .models import RouteDecision


def apply_router_hints(route_params: dict, decision: RouteDecision) -> dict:
    """Mutate/extend the router params with decision hints.

    Keeps backward compatibility with existing router signatures.
    """
    params = dict(route_params)
    params["model_hint"] = decision.model
    params["strategy"] = decision.strategy
    params["k_samples"] = decision.k_samples
    params["verifier_model"] = decision.verifier_model
    return params

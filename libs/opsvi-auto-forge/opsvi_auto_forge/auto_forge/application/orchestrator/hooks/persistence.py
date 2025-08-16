from __future__ import annotations
from typing import Any, Dict, Optional
from uuid import UUID
from datetime import datetime

# Expect high-level decision client in the codebase; provide import placeholder
try:
    from opsvi_auto_forge.infrastructure.memory.graph.decision_client import (
        DecisionClient,
    )
except Exception:  # pragma: no cover
    DecisionClient = None  # type: ignore


async def persist_post_task(
    decision_id: str,
    task_id: str,
    cost_usd: float,
    latency_ms: int,
    input_tokens: int,
    output_tokens: int,
    confidence: float,
    verifier_passed: bool,
    verifier_score: float,
    verifier_rationale: str,
) -> None:
    if DecisionClient is None:
        return
    dc = DecisionClient()
    await dc.update_decision_post(
        decision_id=decision_id,
        props={
            "task_id": task_id,
            "cost_actual": cost_usd,
            "latency_ms": latency_ms,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "confidence": confidence,
            "verifier_passed": verifier_passed,
            "verifier_score": verifier_score,
            "verifier_rationale": verifier_rationale,
            "completed_at": datetime.utcnow().isoformat(),
        },
    )

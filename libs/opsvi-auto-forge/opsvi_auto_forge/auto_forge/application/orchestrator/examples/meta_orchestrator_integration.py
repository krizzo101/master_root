from __future__ import annotations
import asyncio
from uuid import uuid4

from opsvi_auto_forge.core.decision_kernel import (
    analyze_task,
    select_strategy,
    verify_output,
    calibrate_confidence,
    persist_decision,
)
from opsvi_auto_forge.core.retrieval_orchestrator.models import RetrievalConfig
from opsvi_auto_forge.core.retrieval_orchestrator.assembler import build_context_pack

# Placeholder imports; replace with your project modules
# from opsvi_auto_forge.application.orchestrator.router import route_task, submit_to_worker
# from opsvi_auto_forge.core.prompting.gateway import PromptGateway
# from opsvi_auto_forge.core.prompting.schema_registry import get_schema


async def run_demo_task():
    # --- simulated task ---
    task = {
        "id": str(uuid4()),
        "agent": "CODER",
        "type": "code",
        "instructions": "Implement a function to compute Fibonacci using memoization in Python.",
        "query": "Python memoization patterns for fibonacci",
    }
    policies = {
        "budget": {"max_cost_usd": 2.0},
        "verifier": "gpt-4.1",
        "min_confidence": 0.85,
    }

    # 1) Analyze and select decision
    features = await analyze_task(
        task_id=uuid4(),
        agent=task["agent"],
        task_type=task["type"],
        budget_hint=policies["budget"],
    )
    decision = await select_strategy(features, policies, priors={})
    await persist_decision(decision)  # stubbed

    # 2) Build context
    cfg = RetrievalConfig()
    context_pack = await build_context_pack(task["query"], entities=[], cfg=cfg)

    # 3) Build prompt (pseudo-code; adapt to your gateway)
    # schema = get_schema("coder:impl")
    # prompt = build_prompt_pack(role="CODER", task_type="impl", instructions=task["instructions"], context_pack=context_pack, schema=schema, knobs={})
    # router_params = apply_router_hints({}, decision)
    # route_task(router_params)  # submit prompt + schema to LLM
    # result = await submit_to_worker(...)

    # 4) Verify (pseudo result)
    llm_output = {"code": "def fib(n, memo={}): ...", "citations": []}
    passed, vscore, rationale = await verify_output(
        llm_output, schema={}, verifier_model=policies["verifier"]
    )
    confidence = calibrate_confidence(vscore, critic_score=0.9, agreement_rate=1.0)
    print("Decision:", decision)
    print("Verification:", passed, vscore, rationale)
    print("Confidence:", confidence)


if __name__ == "__main__":
    asyncio.run(run_demo_task())

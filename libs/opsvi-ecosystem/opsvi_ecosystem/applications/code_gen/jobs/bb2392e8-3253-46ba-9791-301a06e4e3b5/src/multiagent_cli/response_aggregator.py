"""
ResponseAggregator: Collects agent results, re-validates structure, and aggregates as JSON
"""
from typing import Any

from loguru import logger
from pydantic import BaseModel, ValidationError


class AgentResultModel(BaseModel):
    agent: str
    output: dict
    status: str


def aggregate_responses(agent_outputs: dict[str, Any]) -> dict:
    """
    Aggregates agent outputs, validates structure, returns in unified format.
    """
    results = []
    for task_id, output in agent_outputs.items():
        try:
            ar = AgentResultModel(
                agent=output.get("agent", "unknown"), output=output, status="success"
            )
            results.append(dict(task_id=task_id, **ar.dict()))
        except ValidationError as exc:
            logger.opt(exception=exc).error(
                f"Malformed agent output for task {task_id}: {output}"
            )
            results.append(
                {
                    "task_id": task_id,
                    "agent": "unknown",
                    "output": {},
                    "status": "error",
                    "reason": str(exc),
                }
            )
    aggregated = {"results": results}
    return aggregated

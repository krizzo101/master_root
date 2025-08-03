"""
ACCF Task Market

Purpose:
    Provides task publishing and claiming for agent coordination.

References:
    - docs/applications/ACCF/standards/orchestration_requirements.md
    - docs/applications/ACCF/architecture/adr/orchestration_adrs.md
    - .cursor/templates/implementation/orchestration_output_template.yml

Usage:
    from orchestrator.task_market import TaskMarket
    market = TaskMarket(...)
"""

import asyncio
from typing import Any, Dict, List


class TaskMarket:
    def __init__(self):
        self.tasks: List[Dict[str, Any]] = []
        self.claimed: List[Dict[str, Any]] = []
        self.lock = asyncio.Lock()

    async def publish_task(self, task: Dict[str, Any]):
        async with self.lock:
            self.tasks.append(task)

    async def claim_task(self, agent_id: str) -> Dict[str, Any]:
        async with self.lock:
            if self.tasks:
                task = self.tasks.pop(0)
                task["claimed_by"] = agent_id
                self.claimed.append(task)
                return task
            return None

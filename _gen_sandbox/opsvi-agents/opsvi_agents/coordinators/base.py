"""Coordinator base for opsvi-agents."""
from opsvi_agents.core.base import OpsviAgentsManager

class Coordinator(OpsviAgentsManager):
    async def coordinate(self) -> None:
        pass

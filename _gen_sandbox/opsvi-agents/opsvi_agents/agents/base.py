"""Agent base for opsvi-agents."""
from opsvi_agents.core.base import OpsviAgentsManager

class Agent(OpsviAgentsManager):
    async def act(self, input_data: str) -> str:
        return input_data

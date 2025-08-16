"""Coordinator base for opsvi-orchestration."""
from opsvi_orchestration.core.base import OpsviOrchestrationManager

class Coordinator(OpsviOrchestrationManager):
    async def coordinate(self) -> None:
        pass

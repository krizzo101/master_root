"""Coordinator base for opsvi-deploy."""
from opsvi_deploy.core.base import OpsviDeployManager

class Coordinator(OpsviDeployManager):
    async def coordinate(self) -> None:
        pass

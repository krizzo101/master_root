"""Coordinator base for opsvi-gateway."""
from opsvi_gateway.core.base import OpsviGatewayManager

class Coordinator(OpsviGatewayManager):
    async def coordinate(self) -> None:
        pass

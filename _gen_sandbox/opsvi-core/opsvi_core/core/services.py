"""Core services for opsvi-core.

Provides service management and orchestration.
"""

from typing import Dict, Any, Optional
import asyncio
import logging

from opsvi_core.core.base import OpsviCoreManager
from opsvi_core.config.settings import OpsviCoreConfig
from opsvi_core.exceptions.base import OpsviCoreError

logger = logging.getLogger(__name__)

class OpsviCoreServiceManager(OpsviCoreManager):
    """Service manager for opsvi-core."""

    def __init__(self, config: OpsviCoreConfig):
        super().__init__(config=config)
        self.services: Dict[str, Any] = {}

    async def register_service(self, name: str, service: Any) -> None:
        """Register a service."""
        self.services[name] = service
        logger.info(f"Registered service: {name}")

    async def get_service(self, name: str) -> Optional[Any]:
        """Get a service by name."""
        return self.services.get(name)

    async def list_services(self) -> Dict[str, Any]:
        """List all registered services."""
        return self.services.copy()

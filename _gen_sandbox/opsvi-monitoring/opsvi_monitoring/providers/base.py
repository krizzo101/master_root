"""Provider base classes for opsvi-monitoring.

Provides base classes for service providers.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import asyncio
import logging

from opsvi_monitoring.core.base import OpsviMonitoringManager
from opsvi_monitoring.config.settings import OpsviMonitoringConfig
from opsvi_monitoring.exceptions.base import OpsviMonitoringError

logger = logging.getLogger(__name__)

class OpsviMonitoringProvider(OpsviMonitoringManager, ABC):
    """Base provider class for opsvi-monitoring."""

    def __init__(self, config: OpsviMonitoringConfig):
        super().__init__(config=config)
        self.provider_name = self.__class__.__name__

    @abstractmethod
    async def connect(self) -> bool:
        """Connect to the provider service."""
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from the provider service."""
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Check provider health."""
        pass

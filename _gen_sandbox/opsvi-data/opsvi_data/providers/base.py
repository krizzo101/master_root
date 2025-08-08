"""Provider base classes for opsvi-data.

Provides base classes for service providers.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import asyncio
import logging

from opsvi_data.core.base import OpsviDataManager
from opsvi_data.config.settings import OpsviDataConfig
from opsvi_data.exceptions.base import OpsviDataError

logger = logging.getLogger(__name__)

class OpsviDataProvider(OpsviDataManager, ABC):
    """Base provider class for opsvi-data."""

    def __init__(self, config: OpsviDataConfig):
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

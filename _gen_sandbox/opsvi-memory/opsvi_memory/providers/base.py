"""Provider base classes for opsvi-memory.

Provides base classes for service providers.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import asyncio
import logging

from opsvi_memory.core.base import OpsviMemoryManager
from opsvi_memory.config.settings import OpsviMemoryConfig
from opsvi_memory.exceptions.base import OpsviMemoryError

logger = logging.getLogger(__name__)

class OpsviMemoryProvider(OpsviMemoryManager, ABC):
    """Base provider class for opsvi-memory."""

    def __init__(self, config: OpsviMemoryConfig):
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

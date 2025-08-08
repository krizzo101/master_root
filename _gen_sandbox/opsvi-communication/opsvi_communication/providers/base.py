"""Provider base classes for opsvi-communication.

Provides base classes for service providers.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import asyncio
import logging

from opsvi_communication.core.base import OpsviCommunicationManager
from opsvi_communication.config.settings import OpsviCommunicationConfig
from opsvi_communication.exceptions.base import OpsviCommunicationError

logger = logging.getLogger(__name__)

class OpsviCommunicationProvider(OpsviCommunicationManager, ABC):
    """Base provider class for opsvi-communication."""

    def __init__(self, config: OpsviCommunicationConfig):
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

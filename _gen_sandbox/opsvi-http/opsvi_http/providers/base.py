"""Provider base classes for opsvi-http.

Provides base classes for service providers.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import asyncio
import logging

from opsvi_http.core.base import OpsviHttpManager
from opsvi_http.config.settings import OpsviHttpConfig
from opsvi_http.exceptions.base import OpsviHttpError

logger = logging.getLogger(__name__)

class OpsviHttpProvider(OpsviHttpManager, ABC):
    """Base provider class for opsvi-http."""

    def __init__(self, config: OpsviHttpConfig):
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

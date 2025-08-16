"""Provider base classes for opsvi-security.

Provides base classes for service providers.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import asyncio
import logging

from opsvi_security.core.base import OpsviSecurityManager
from opsvi_security.config.settings import OpsviSecurityConfig
from opsvi_security.exceptions.base import OpsviSecurityError

logger = logging.getLogger(__name__)

class OpsviSecurityProvider(OpsviSecurityManager, ABC):
    """Base provider class for opsvi-security."""

    def __init__(self, config: OpsviSecurityConfig):
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

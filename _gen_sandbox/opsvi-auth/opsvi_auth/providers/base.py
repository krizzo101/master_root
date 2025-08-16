"""Provider base classes for opsvi-auth.

Provides base classes for service providers.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import asyncio
import logging

from opsvi_auth.core.base import OpsviAuthManager
from opsvi_auth.config.settings import OpsviAuthConfig
from opsvi_auth.exceptions.base import OpsviAuthError

logger = logging.getLogger(__name__)

class OpsviAuthProvider(OpsviAuthManager, ABC):
    """Base provider class for opsvi-auth."""

    def __init__(self, config: OpsviAuthConfig):
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

"""Provider base classes for opsvi-fs.

Provides base classes for service providers.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import asyncio
import logging

from opsvi_fs.core.base import OpsviFsManager
from opsvi_fs.config.settings import OpsviFsConfig
from opsvi_fs.exceptions.base import OpsviFsError

logger = logging.getLogger(__name__)

class OpsviFsProvider(OpsviFsManager, ABC):
    """Base provider class for opsvi-fs."""

    def __init__(self, config: OpsviFsConfig):
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

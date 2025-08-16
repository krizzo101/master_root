"""Provider base classes for opsvi-llm.

Provides base classes for service providers.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import asyncio
import logging

from opsvi_llm.core.base import OpsviLlmManager
from opsvi_llm.config.settings import OpsviLlmConfig
from opsvi_llm.exceptions.base import OpsviLlmError

logger = logging.getLogger(__name__)

class OpsviLlmProvider(OpsviLlmManager, ABC):
    """Base provider class for opsvi-llm."""

    def __init__(self, config: OpsviLlmConfig):
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

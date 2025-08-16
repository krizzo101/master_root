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
    """Base provider class for opsvi-security.

    Concrete providers should implement connect, disconnect and health_check.
    This base class provides a small lifecycle helper and simple retry logic
    for connection attempts.
    """

    def __init__(self, config: OpsviSecurityConfig):
        super().__init__(config=config)
        self.provider_name = self.__class__.__name__
        self._connected: bool = False
        self._lock = asyncio.Lock()

    @abstractmethod
    async def connect(self) -> bool:
        """Connect to the provider service.

        Should set any client handles and return True on success.
        """

    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from the provider service and cleanup resources."""

    @abstractmethod
    async def health_check(self) -> bool:
        """Check provider health. Return True if healthy."""

    async def ensure_connected(self, retries: int = 3, delay: float = 0.5) -> None:
        """Ensure the provider is connected, with simple retry.

        Raises:
            OpsviSecurityError: if connection cannot be established.
        """
        async with self._lock:
            if self._connected:
                return
            last_exc: Optional[BaseException] = None
            for attempt in range(1, retries + 1):
                try:
                    logger.debug("%s: attempting connect (%d/%d)", self.provider_name, attempt, retries)
                    ok = await self.connect()
                    if ok:
                        self._connected = True
                        logger.info("%s: connected", self.provider_name)
                        return
                    last_exc = OpsviSecurityError(f"{self.provider_name}: connect returned False")
                except Exception as exc:  # noqa: BLE001 - propagate as OpsviSecurityError
                    last_exc = exc
                    logger.exception("%s: connect attempt failed", self.provider_name)
                if attempt < retries:
                    await asyncio.sleep(delay)
            raise OpsviSecurityError(f"{self.provider_name}: failed to connect after {retries} attempts") from last_exc

    async def ensure_disconnected(self) -> None:
        """Ensure the provider is disconnected and resources cleaned up."""
        async with self._lock:
            if not self._connected:
                return
            try:
                await self.disconnect()
            finally:
                self._connected = False
                logger.info("%s: disconnected", self.provider_name)

    async def check_and_warn(self) -> bool:
        """Run a health check and log a warning if unhealthy.

        Returns True if healthy, False otherwise.
        """
        try:
            healthy = await self.health_check()
            if not healthy:
                logger.warning("%s: health_check reported unhealthy", self.provider_name)
            return healthy
        except Exception:
            logger.exception("%s: health_check raised an exception", self.provider_name)
            return False

    def status_metadata(self) -> Dict[str, Any]:
        """Return provider status metadata for metrics/logging."""
        return {
            "provider": self.provider_name,
            "connected": self._connected,
        }

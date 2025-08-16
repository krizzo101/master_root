"""Provider base classes for opsvi-memory.

Provides base classes for service providers.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Awaitable, Callable, Dict, Optional, TypeVar
import asyncio
import logging

from opsvi_memory.core.base import OpsviMemoryManager
from opsvi_memory.config.settings import OpsviMemoryConfig
from opsvi_memory.exceptions.base import OpsviMemoryError

logger = logging.getLogger(__name__)

T = TypeVar("T")


class OpsviMemoryProvider(OpsviMemoryManager, ABC):
    """Base provider class for opsvi-memory.

    Subclasses should implement connect, disconnect and health_check.

    This base class provides lifecycle management, timeout handling,
    and unified error translation to OpsviMemoryError.
    """

    def __init__(self, config: OpsviMemoryConfig):
        super().__init__(config=config)
        self.provider_name: str = self.__class__.__name__
        self._connected: bool = False
        self._lock: asyncio.Lock = asyncio.Lock()

    # ----- Provider API contract -----
    @abstractmethod
    async def connect(self) -> bool:
        """Connect to the provider service.

        Return True on successful connection, False otherwise.
        """

    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from the provider service."""

    @abstractmethod
    async def health_check(self) -> bool:
        """Check provider health. Return True if healthy."""

    # ----- Lifecycle helpers -----
    @property
    def connected(self) -> bool:
        """Return current connection state (non-authoritative)."""
        return self._connected

    async def ensure_connected(self, timeout: Optional[float] = 5.0) -> bool:
        """Ensure the provider is connected. Connects if not already.

        Returns True if connected at the end of the call.
        """
        async with self._lock:
            if self._connected:
                return True
            try:
                coro = self.connect()
                if timeout is not None and timeout > 0:
                    result = await asyncio.wait_for(coro, timeout)
                else:
                    result = await coro
                self._connected = bool(result)
                return self._connected
            except Exception as exc:  # pragma: no cover - propagate as OpsviMemoryError
                logger.exception("Failed to connect provider %s", self.provider_name)
                raise OpsviMemoryError(
                    f"Connection failed for provider {self.provider_name}: {exc}"
                )

    async def safe_disconnect(self) -> None:
        """Disconnect if connected, swallowing non-fatal errors."""
        async with self._lock:
            if not self._connected:
                return
            try:
                await self.disconnect()
            except Exception:
                logger.exception("Error disconnecting provider %s", self.provider_name)
            finally:
                self._connected = False

    async def __aenter__(self) -> "OpsviMemoryProvider":
        """Async context: connect on enter."""
        await self.ensure_connected()
        return self

    async def __aexit__(self, exc_type, exc, tb) -> Optional[bool]:
        """Async context: always try to disconnect on exit."""
        await self.safe_disconnect()
        return None

    # ----- Operation helpers -----
    async def run_with_timeout(self, coro: Awaitable[T], timeout: Optional[float] = None) -> T:
        """Run a coroutine with optional timeout and map exceptions to OpsviMemoryError.

        Example: await provider.run_with_timeout(provider.do_something(), timeout=2.0)
        """
        try:
            if timeout is not None and timeout > 0:
                return await asyncio.wait_for(coro, timeout)
            return await coro
        except asyncio.TimeoutError as exc:
            logger.warning("Operation timed out on provider %s", self.provider_name)
            raise OpsviMemoryError(
                f"Operation timed out on provider {self.provider_name}"
            ) from exc
        except OpsviMemoryError:
            # Preserve already translated errors
            raise
        except Exception as exc:
            logger.exception("Provider %s raised an error during operation", self.provider_name)
            raise OpsviMemoryError(
                f"Provider {self.provider_name} error: {exc}"
            ) from exc

    async def run(self, op: Callable[[], Awaitable[T]], *, timeout: Optional[float] = None, require_connection: bool = True) -> T:
        """Run an async provider operation with optional ensure-connect and timeout.

        - If require_connection is True, ensures the provider is connected before running.
        - Exceptions are normalized to OpsviMemoryError.
        """
        if require_connection:
            ok = await self.ensure_connected()
            if not ok:
                raise OpsviMemoryError(f"Provider {self.provider_name} is not connected")
        return await self.run_with_timeout(op(), timeout)

    # ----- Reporting -----
    async def ping_and_report(self) -> Dict[str, Any]:
        """Perform a health check and return a small report dict."""
        status = False
        error: Optional[str] = None
        try:
            status = await self.health_check()
        except Exception as exc:
            logger.exception("Health check failed for provider %s", self.provider_name)
            error = str(exc)
        return {
            "provider": self.provider_name,
            "healthy": bool(status),
            "connected": self._connected,
            "error": error,
        }

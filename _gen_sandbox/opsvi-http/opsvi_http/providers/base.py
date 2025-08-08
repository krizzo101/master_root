"""Provider base classes for opsvi-http.

Provides base classes for service providers.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Callable, Awaitable, Union
import asyncio
import logging
from datetime import datetime, timezone

from opsvi_http.core.base import OpsviHttpManager
from opsvi_http.config.settings import OpsviHttpConfig
from opsvi_http.exceptions.base import OpsviHttpError

logger = logging.getLogger(__name__)

Callback = Union[Callable[..., Any], Callable[..., Awaitable[Any]]]


class OpsviHttpProvider(OpsviHttpManager, ABC):
    """Base provider class for opsvi-http.

    Concrete providers should implement connect, disconnect and health_check.

    This base class provides lifecycle helpers, simple callbacks and
    optional async context management.
    """

    def __init__(self, config: OpsviHttpConfig):
        super().__init__(config=config)
        self.provider_name: str = self.__class__.__name__
        self._connected: bool = False
        self._lock: asyncio.Lock = asyncio.Lock()
        # Optional callbacks: on_connect(), on_disconnect(), on_health_change(bool)
        self._callbacks: Dict[str, Callback] = {}
        self._last_health_ok: Optional[bool] = None
        self._last_health_at: Optional[datetime] = None

    # ----- abstract API -----
    @abstractmethod
    async def connect(self) -> bool:
        """Connect to the provider service.

        Returns True when connection was established, False otherwise.
        May raise OpsviHttpError on unrecoverable failure.
        """

    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from the provider service."""

    @abstractmethod
    async def health_check(self) -> bool:
        """Check provider health and return True if healthy."""

    # ----- lifecycle helpers -----
    @property
    def connected(self) -> bool:
        """Current connection state."""
        return self._connected

    async def ensure_connected(self, timeout: Optional[float] = None) -> bool:
        """Ensure provider is connected; attempts connection if needed.

        Uses a lock to serialize concurrent connect attempts.
        Returns True if connected after the call.
        """
        if self._connected:
            return True

        async with self._lock:
            if self._connected:
                return True

            try:
                coro = self.connect()
                connected = (
                    await asyncio.wait_for(coro, timeout=timeout)
                    if timeout is not None
                    else await coro
                )
            except asyncio.TimeoutError:
                logger.warning("%s: connect timed out", self.provider_name)
                return False
            except Exception as exc:  # pragma: no cover - pass-through
                logger.exception("%s: error during connect: %s", self.provider_name, exc)
                raise OpsviHttpError(str(exc)) from exc

            self._connected = bool(connected)
            if self._connected:
                self._invoke_callback("on_connect")
            return self._connected

    async def ensure_disconnected(self) -> None:
        """Ensure provider is disconnected. Safe to call multiple times."""
        async with self._lock:
            if not self._connected:
                return
            try:
                await self.disconnect()
            except Exception as exc:  # pragma: no cover - pass-through
                logger.exception("%s: error during disconnect: %s", self.provider_name, exc)
                raise OpsviHttpError(str(exc)) from exc
            finally:
                self._connected = False
                self._invoke_callback("on_disconnect")

    async def check_and_report_health(self) -> bool:
        """Run health_check and call health callback if provided.

        Returns the health boolean.
        """
        healthy = False
        try:
            healthy = await self.health_check()
        except Exception as exc:
            logger.exception("%s: health_check failed: %s", self.provider_name, exc)
            healthy = False

        self._last_health_ok = healthy
        self._last_health_at = datetime.now(timezone.utc)
        self._invoke_callback("on_health_change", healthy)
        return healthy

    # ----- callbacks -----
    def register_callback(self, name: str, callback: Callback) -> None:
        """Register a callback for lifecycle events.

        Supported names: on_connect, on_disconnect, on_health_change
        """
        if not callable(callback):
            raise TypeError("callback must be callable")
        self._callbacks[name] = callback

    def unregister_callback(self, name: str) -> None:
        """Unregister a previously registered callback."""
        self._callbacks.pop(name, None)

    def _invoke_callback(self, name: str, *args: Any) -> None:
        cb = self._callbacks.get(name)
        if not cb:
            return
        try:
            result = cb(*args)
            if asyncio.iscoroutine(result):
                # schedule but don't await
                asyncio.create_task(result)
        except Exception:
            logger.exception("%s: callback %s raised an exception", self.provider_name, name)

    # ----- context manager helpers -----
    async def __aenter__(self) -> "OpsviHttpProvider":
        await self.ensure_connected()
        return self

    async def __aexit__(self, exc_type, exc, tb) -> Optional[bool]:
        await self.ensure_disconnected()
        return None

    # ----- diagnostics -----
    def status(self) -> Dict[str, Any]:
        """Return a lightweight diagnostic snapshot."""
        return {
            "provider": self.provider_name,
            "connected": self._connected,
            "last_health_ok": self._last_health_ok,
            "last_health_at": self._last_health_at.isoformat() if self._last_health_at else None,
        }

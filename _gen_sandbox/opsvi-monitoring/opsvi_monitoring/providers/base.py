"""Provider base classes for opsvi-monitoring.

Provides base classes for service providers.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import asyncio
import logging

from opsvi_monitoring.core.base import OpsviMonitoringManager
from opsvi_monitoring.config.settings import OpsviMonitoringConfig
from opsvi_monitoring.exceptions.base import OpsviMonitoringError

logger = logging.getLogger(__name__)


class OpsviMonitoringProvider(OpsviMonitoringManager, ABC):
    """Base provider class for opsvi-monitoring.

    Subclasses should implement connect/disconnect/health_check. This base class
    offers a simple lifecycle helper and a guarded run loop helper for providers
    that need to perform periodic work.
    """

    def __init__(self, config: OpsviMonitoringConfig):
        super().__init__(config=config)
        self.provider_name = self.__class__.__name__
        self._connected: bool = False
        self._run_task: Optional[asyncio.Task] = None
        self._stop_event = asyncio.Event()

    @abstractmethod
    async def connect(self) -> bool:
        """Connect to the provider service.

        Return True if connection succeeded, False otherwise.
        """

    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from the provider service and release resources."""

    @abstractmethod
    async def health_check(self) -> bool:
        """Return True when provider is healthy."""

    async def start(self) -> None:
        """Start the provider: connect and optionally kick off background work.

        Subclasses may override start to provide custom startup behavior but should
        call super().start() to benefit from the built-in lifecycle handling.
        """
        if self._connected:
            logger.debug("%s already started", self.provider_name)
            return

        try:
            ok = await self.connect()
        except Exception as exc:  # pragma: no cover - bubble up as OpsviMonitoringError
            logger.exception("Exception while connecting %s", self.provider_name)
            raise OpsviMonitoringError("connect failed") from exc

        if not ok:
            raise OpsviMonitoringError("connect returned False")

        self._connected = True
        self._stop_event.clear()
        logger.info("%s connected", self.provider_name)

    async def stop(self) -> None:
        """Stop the provider: cancel background work and disconnect."""
        if not self._connected:
            logger.debug("%s not connected; nothing to stop", self.provider_name)
            return

        # signal run loop to stop
        self._stop_event.set()

        if self._run_task is not None:
            self._run_task.cancel()
            try:
                await self._run_task
            except asyncio.CancelledError:
                logger.debug("%s background task cancelled", self.provider_name)
            finally:
                self._run_task = None

        try:
            await self.disconnect()
        except Exception as exc:  # pragma: no cover - bubble up as OpsviMonitoringError
            logger.exception("Exception while disconnecting %s", self.provider_name)
            raise OpsviMonitoringError("disconnect failed") from exc

        self._connected = False
        logger.info("%s disconnected", self.provider_name)

    def run_background(self, coro_func, *, name: Optional[str] = None) -> None:
        """Schedule a background coroutine function to run until stopped.

        coro_func must be a callable that accepts a single argument: an
        asyncio.Event used as a cancellation signal. The function should be
        an async function and return when the event is set.
        """
        if self._run_task is not None and not self._run_task.done():
            logger.debug("%s already running background task", self.provider_name)
            return

        async def _runner():
            try:
                await coro_func(self._stop_event)
            except asyncio.CancelledError:
                logger.debug("%s runner cancelled", self.provider_name)
                raise
            except Exception:
                logger.exception("Unhandled exception in %s background runner", self.provider_name)

        loop = asyncio.get_event_loop()
        task_name = name or f"{self.provider_name}-background"
        self._run_task = loop.create_task(_runner(), name=task_name)
        logger.info("%s started background task %s", self.provider_name, task_name)

    async def guarded_periodic(self, interval: float, callback, *args, **kwargs) -> None:
        """Run callback periodically while provider is started.

        The callback may be regular or async. Exceptions are logged and do not
        stop the loop. The loop exits when stop() is called.
        """
        if interval <= 0:
            raise ValueError("interval must be positive")

        while not self._stop_event.is_set():
            try:
                result = callback(*args, **kwargs)
                if asyncio.iscoroutine(result):
                    await result
            except Exception:
                logger.exception("Error in periodic callback for %s", self.provider_name)
            try:
                await asyncio.wait_for(self._stop_event.wait(), timeout=interval)
            except asyncio.TimeoutError:
                continue

    async def ensure_healthy(self, timeout: float = 5.0) -> bool:
        """Check provider health with a timeout.

        Returns True if healthy within timeout, False otherwise.
        """
        try:
            return await asyncio.wait_for(self.health_check(), timeout=timeout)
        except asyncio.TimeoutError:
            logger.warning("Health check timed out for %s", self.provider_name)
            return False
        except Exception:
            logger.exception("Health check raised for %s", self.provider_name)
            return False

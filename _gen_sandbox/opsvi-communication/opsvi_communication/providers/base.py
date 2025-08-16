"""Provider base classes for opsvi-communication.

Provides base classes for service providers.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Callable, Awaitable
import asyncio
import logging
import time

from opsvi_communication.core.base import OpsviCommunicationManager
from opsvi_communication.config.settings import OpsviCommunicationConfig
from opsvi_communication.exceptions.base import OpsviCommunicationError

logger = logging.getLogger(__name__)


class OpsviCommunicationProvider(OpsviCommunicationManager, ABC):
    """Base provider class for opsvi-communication.

    This class provides common lifecycle helpers and lightweight metrics hooks
    that concrete providers can reuse. Concrete subclasses must implement the
    connect, disconnect and health_check abstract methods.
    """

    def __init__(self, config: OpsviCommunicationConfig):
        super().__init__(config=config)
        self.provider_name = self.__class__.__name__
        self._connected: bool = False
        self._lock = asyncio.Lock()

    @abstractmethod
    async def connect(self) -> bool:
        """Connect to the provider service.

        Implementations should set any internal client state needed to mark
        the provider as usable. Return True on success, False otherwise.
        """
        raise NotImplementedError

    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from the provider service.

        Implementations should clean up resources and make the provider
        safe to re-connect later.
        """
        raise NotImplementedError

    @abstractmethod
    async def health_check(self) -> bool:
        """Check provider health.

        Return True if the service is healthy and reachable, False otherwise.
        """
        raise NotImplementedError

    # Lifecycle helpers
    async def ensure_connected(self, timeout: Optional[float] = None) -> bool:
        """Ensure the provider is connected.

        If already connected, returns True. Otherwise attempts to connect using
        run_with_retry and marks state accordingly.
        """
        if self._connected:
            return True

        async with self._lock:
            if self._connected:
                return True

            # try to connect with retries from config if available
            retries = getattr(self.config, "connect_retries", 1)
            delay = getattr(self.config, "connect_retry_delay", 0.5)
            try:
                success = await self.run_with_retry(
                    lambda: self.run_with_timeout(self.connect(), timeout),
                    retries=retries,
                    delay=delay,
                )
            except Exception as exc:
                raise OpsviCommunicationError(
                    f"{self.provider_name} failed to connect: {exc}"
                ) from exc

            self._connected = bool(success)
            return self._connected

    async def ensure_disconnected(self, timeout: Optional[float] = None) -> None:
        """Ensure the provider is disconnected.

        If not connected, this is a no-op. Otherwise runs disconnect and clears
        connected state.
        """
        if not self._connected:
            return

        async with self._lock:
            if not self._connected:
                return
            try:
                await self.run_with_timeout(self.disconnect(), timeout)
            except Exception as exc:
                logger.warning("%s failed to disconnect cleanly: %s", self.provider_name, exc)
            finally:
                self._connected = False

    async def run_with_timeout(self, coro: Awaitable[Any], timeout: Optional[float]) -> Any:
        """Run coroutine with an optional timeout.

        If timeout is None, uses config.default_timeout if present, otherwise
        waits indefinitely.
        """
        default_timeout = getattr(self.config, "default_timeout", None)
        use_timeout = timeout if timeout is not None else default_timeout
        if use_timeout is None:
            return await coro
        return await asyncio.wait_for(coro, timeout=use_timeout)

    async def run_with_retry(self, func: Callable[[], Awaitable[Any]], retries: int = 1, delay: float = 0.5) -> Any:
        """Run an async function with simple retry logic.

        retries: total attempts (>=1). delay: seconds to wait between attempts.
        The last exception is raised if all attempts fail.
        """
        if retries < 1:
            retries = 1
        last_exc: Optional[BaseException] = None
        for attempt in range(1, retries + 1):
            try:
                return await func()
            except Exception as exc:  # noqa: BLE001 - we need to catch general exceptions
                last_exc = exc
                logger.debug(
                    "%s attempt %d/%d failed: %s",
                    self.provider_name,
                    attempt,
                    retries,
                    exc,
                )
                if attempt < retries:
                    await asyncio.sleep(delay)
        # all attempts failed
        raise last_exc  # type: ignore

    async def safe_execute(self, coro: Awaitable[Any], *, wrap_message: Optional[str] = None) -> Any:
        """Execute a coroutine and convert exceptions to OpsviCommunicationError.

        Useful for provider operations where upstream callers expect
        OpsviCommunicationError on failure.
        """
        try:
            return await coro
        except OpsviCommunicationError:
            raise
        except Exception as exc:
            msg = wrap_message or f"{self.provider_name} operation failed"
            logger.exception("%s: %s", self.provider_name, exc)
            raise OpsviCommunicationError(f"{msg}: {exc}") from exc

    # Lightweight metrics hooks
    def record_metric(self, name: str, value: float, tags: Optional[Dict[str, Any]] = None) -> None:
        """Record a metric. Default implementation logs the metric.

        Concrete providers can override to integrate with real metrics backends.
        """
        tags = tags or {}
        logger.debug("METRIC %s=%s %s (%s)", name, value, self.provider_name, tags)

    def start_timer(self) -> float:
        """Start a simple timer. Returns a monotonic timestamp to pass to stop_timer."""
        return time.monotonic()

    def stop_timer(self, start: float, name: str, tags: Optional[Dict[str, Any]] = None) -> float:
        """Stop a timer started with start_timer and record elapsed as a metric.

        Returns the elapsed time in seconds.
        """
        elapsed = time.monotonic() - start
        self.record_metric(name, elapsed, tags=tags)
        return elapsed

    # Async context manager convenience
    async def __aenter__(self) -> "OpsviCommunicationProvider":
        await self.ensure_connected()
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.ensure_disconnected()

    @property
    def is_connected(self) -> bool:
        """Simple property showing whether the provider is marked connected."""
        return self._connected

"""Provider base classes for opsvi-fs.

Provides base classes for service providers.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Callable, Awaitable, TypeVar, Coroutine
import asyncio
import logging
import time
from contextlib import asynccontextmanager

from opsvi_fs.core.base import OpsviFsManager
from opsvi_fs.config.settings import OpsviFsConfig
from opsvi_fs.exceptions.base import OpsviFsError

logger = logging.getLogger(__name__)

T = TypeVar("T")


class OpsviFsProvider(OpsviFsManager, ABC):
    """Base provider class for opsvi-fs.

    Concrete providers should implement connect, disconnect and health_check.
    This base class provides simple lifecycle orchestration and a small
    concurrency-safe connection guard.
    """

    def __init__(self, config: OpsviFsConfig):
        super().__init__(config=config)
        self.provider_name = self.__class__.__name__
        self._connected = False
        self._lock = asyncio.Lock()
        # Minimal in-memory metrics
        self._metrics: Dict[str, Any] = {
            "connect_attempts": 0,
            "connect_success": 0,
            "connect_failure": 0,
            "connect_timeout": 0,
            "connect_duration_total": 0.0,
            "disconnect_attempts": 0,
            "disconnect_success": 0,
            "disconnect_errors": 0,
            "disconnect_duration_total": 0.0,
            "health_attempts": 0,
            "health_success": 0,
            "health_failures": 0,
            "health_errors": 0,
            "health_duration_total": 0.0,
            "last_error": None,
        }

    @property
    def is_connected(self) -> bool:
        """Return current connection state (non-blocking)."""
        return self._connected

    @abstractmethod
    async def connect(self) -> bool:
        """Connect to the provider service.

        Should perform any async IO needed to establish the connection.
        Return True on success, False on harmless failure.
        Raise OpsviFsError on unrecoverable errors.
        """
        raise NotImplementedError

    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from the provider service.

        Should clean up resources and be safe to call multiple times.
        """
        raise NotImplementedError

    @abstractmethod
    async def health_check(self) -> bool:
        """Check provider health.

        Return True when healthy, False otherwise. Should be non-raising where
        possible; raise OpsviFsError for unexpected conditions.
        """
        raise NotImplementedError

    async def ensure_connected(self, timeout: Optional[float] = 10.0) -> bool:
        """Ensure provider is connected, establishing connection if needed.

        This method is concurrency-safe: multiple coroutines may call it and
        only one will attempt connection. Returns True when connected.
        """
        if self._connected:
            return True
        async with self._lock:
            if self._connected:
                return True
            self._metrics["connect_attempts"] += 1
            start = time.perf_counter()
            try:
                coro = self.connect()
                if timeout is not None and timeout > 0:
                    result = await asyncio.wait_for(coro, timeout)
                else:
                    result = await coro
                self._connected = bool(result)
                self._metrics["connect_duration_total"] += time.perf_counter() - start
                if not self._connected:
                    self._metrics["connect_failure"] += 1
                    logger.warning("%s: connect() completed but returned False", self.provider_name)
                else:
                    self._metrics["connect_success"] += 1
                    logger.info("%s: connected", self.provider_name)
                return self._connected
            except asyncio.TimeoutError as exc:
                self._metrics["connect_timeout"] += 1
                self._metrics["last_error"] = f"timeout: {exc}"  # store last error cause
                logger.exception("%s: connection attempt timed out", self.provider_name)
                raise OpsviFsError("connection timed out") from exc
            except Exception as exc:  # pragma: no cover - propagate as OpsviFsError
                self._metrics["last_error"] = str(exc)
                logger.exception("%s: connection attempt failed", self.provider_name)
                raise OpsviFsError("connection failed") from exc

    async def ensure_disconnected(self) -> None:
        """Ensure provider is disconnected, safe to call multiple times."""
        async with self._lock:
            if not self._connected:
                return
            self._metrics["disconnect_attempts"] += 1
            start = time.perf_counter()
            try:
                await self.disconnect()
                self._metrics["disconnect_success"] += 1
            except Exception as exc:
                self._metrics["disconnect_errors"] += 1
                self._metrics["last_error"] = str(exc)
                logger.exception("%s: error during disconnect", self.provider_name)
                # Do not raise: best effort cleanup
            finally:
                self._metrics["disconnect_duration_total"] += time.perf_counter() - start
                self._connected = False
                logger.info("%s: disconnected", self.provider_name)

    async def run_health_check_with_retry(self, retries: int = 3, delay: float = 1.0) -> bool:
        """Run health_check with simple retries and backoff.

        Returns True if any attempt reports healthy. Raises OpsviFsError if
        unexpected exceptions occur repeatedly.
        """
        last_exc: Optional[Exception] = None
        for attempt in range(1, max(1, retries) + 1):
            self._metrics["health_attempts"] += 1
            start = time.perf_counter()
            try:
                healthy = await self.health_check()
                self._metrics["health_duration_total"] += time.perf_counter() - start
                if healthy:
                    self._metrics["health_success"] += 1
                    logger.debug("%s: health check passed on attempt %d", self.provider_name, attempt)
                    return True
                self._metrics["health_failures"] += 1
                logger.debug("%s: health check failed on attempt %d", self.provider_name, attempt)
            except Exception as exc:
                last_exc = exc
                self._metrics["health_errors"] += 1
                self._metrics["last_error"] = str(exc)
                logger.exception("%s: health check exception on attempt %d", self.provider_name, attempt)
            if attempt < retries:
                await asyncio.sleep(delay * attempt)
        if last_exc:
            raise OpsviFsError("health check failed") from last_exc
        return False

    # Provider-specific lifecycle helpers and metrics hooks

    async def ensure_ready(self, connect_timeout: Optional[float] = 10.0, health_retries: int = 1, health_delay: float = 0.5) -> bool:
        """Ensure the provider is connected and healthy.

        Returns True if connected and healthy. False if unhealthy after retries.
        Raises OpsviFsError for connection errors or unexpected health errors.
        """
        connected = await self.ensure_connected(timeout=connect_timeout)
        if not connected:
            return False
        return await self.run_health_check_with_retry(retries=max(1, health_retries), delay=health_delay)

    async def run_with_connection(self, op: Callable[[], Awaitable[T]], ensure_health: bool = False, connect_timeout: Optional[float] = 10.0) -> T:
        """Execute an async operation with connection ensured.

        Optionally runs a health check before executing the operation.
        """
        await self.ensure_connected(timeout=connect_timeout)
        if ensure_health:
            ok = await self.run_health_check_with_retry(retries=1)
            if not ok:
                raise OpsviFsError("provider not healthy")
        return await op()

    @asynccontextmanager
    async def connected(self, timeout: Optional[float] = 10.0):
        """Async context manager ensuring connection for a block.

        Example:
            async with provider.connected():
                await provider.do_something()
        """
        await self.ensure_connected(timeout=timeout)
        try:
            yield self
        finally:
            # Best-effort: do not propagate disconnect errors
            try:
                await self.ensure_disconnected()
            except Exception:
                pass

    async def __aenter__(self) -> "OpsviFsProvider":
        await self.ensure_connected()
        return self

    async def __aexit__(self, exc_type, exc, tb) -> bool:
        await self.ensure_disconnected()
        return False

    def reset_metrics(self) -> None:
        """Reset all in-memory metrics counters."""
        self._metrics.update({
            "connect_attempts": 0,
            "connect_success": 0,
            "connect_failure": 0,
            "connect_timeout": 0,
            "connect_duration_total": 0.0,
            "disconnect_attempts": 0,
            "disconnect_success": 0,
            "disconnect_errors": 0,
            "disconnect_duration_total": 0.0,
            "health_attempts": 0,
            "health_success": 0,
            "health_failures": 0,
            "health_errors": 0,
            "health_duration_total": 0.0,
            "last_error": None,
        })

    def get_metrics(self) -> Dict[str, Any]:
        """Return a snapshot of metrics including simple averages."""
        m = dict(self._metrics)
        m["connected"] = self._connected
        # Simple averages if attempts exist
        m["connect_avg_duration"] = (
            m["connect_duration_total"] / m["connect_attempts"] if m["connect_attempts"] else 0.0
        )
        m["disconnect_avg_duration"] = (
            m["disconnect_duration_total"] / m["disconnect_attempts"] if m["disconnect_attempts"] else 0.0
        )
        m["health_avg_duration"] = (
            m["health_duration_total"] / m["health_attempts"] if m["health_attempts"] else 0.0
        )
        return m

    def __repr__(self) -> str:
        state = "connected" if self._connected else "disconnected"
        return f"{self.provider_name}<{state}>"

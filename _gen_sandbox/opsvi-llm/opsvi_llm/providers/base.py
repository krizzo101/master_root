"""Provider base classes for opsvi-llm.

Provides base classes for service providers.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Callable, Awaitable
import asyncio
import logging
import time

from opsvi_llm.core.base import OpsviLlmManager
from opsvi_llm.config.settings import OpsviLlmConfig
from opsvi_llm.exceptions.base import OpsviLlmError

logger = logging.getLogger(__name__)


class OpsviLlmProvider(OpsviLlmManager, ABC):
    """Base provider class for opsvi-llm.

    Concrete providers must implement connect, disconnect and health_check.

    This base class supplies common lifecycle helpers, basic concurrency
    protection around connect/disconnect, an async context manager, and
    lightweight metric hooks.
    """

    def __init__(self, config: OpsviLlmConfig):
        super().__init__(config=config)
        self.provider_name = self.__class__.__name__
        self._connected: bool = False
        self._lock = asyncio.Lock()

    @abstractmethod
    async def connect(self) -> bool:
        """Connect to the provider service.

        Implementations should establish any network connections or clients
        necessary. Return True on successful connection, False otherwise.
        """
        raise NotImplementedError

    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from the provider service and release resources."""
        raise NotImplementedError

    @abstractmethod
    async def health_check(self) -> bool:
        """Check provider health and return True when healthy."""
        raise NotImplementedError

    @property
    def is_connected(self) -> bool:
        """Whether the provider is currently considered connected."""
        return self._connected

    async def open(self, *, timeout: Optional[float] = None) -> bool:
        """Safely open a connection to the provider.

        This method acquires an internal lock so that concurrent callers do not
        race to connect. It calls the provider's connect() implementation and
        sets internal connection state on success.

        If timeout is provided, the connect attempt will be cancelled after
        timeout seconds and an OpsviLlmError will be raised.
        """
        async with self._lock:
            if self._connected:
                logger.debug("%s already connected", self.provider_name)
                return True

            try:
                if timeout is None:
                    ok = await self.connect()
                else:
                    ok = await asyncio.wait_for(self.connect(), timeout)
            except asyncio.TimeoutError as exc:
                logger.exception("Connect to %s timed out", self.provider_name)
                raise OpsviLlmError(f"connect timed out for {self.provider_name}") from exc
            except Exception as exc:  # pragma: no cover - defensive
                logger.exception("Error connecting to %s", self.provider_name)
                raise OpsviLlmError(f"error connecting to {self.provider_name}: {exc}") from exc

            if not ok:
                raise OpsviLlmError(f"provider {self.provider_name} reported failed connection")

            self._connected = True
            logger.info("%s connected", self.provider_name)
            self.record_metric("provider.connect", 1, {"provider": self.provider_name})
            return True

    async def close(self) -> None:
        """Safely close the provider connection.

        This method is idempotent and will swallow exceptions from disconnect
        while logging them, but it will still raise an OpsviLlmError for
        unexpected failures so callers can react if needed.
        """
        async with self._lock:
            if not self._connected:
                logger.debug("%s already disconnected", self.provider_name)
                return

            try:
                await self.disconnect()
            except Exception as exc:  # pragma: no cover - defensive
                logger.exception("Error disconnecting from %s", self.provider_name)
                # store metric and wrap in provider error
                self.record_metric("provider.disconnect.error", 1, {"provider": self.provider_name})
                raise OpsviLlmError(f"error disconnecting from {self.provider_name}: {exc}") from exc
            finally:
                self._connected = False
                logger.info("%s disconnected", self.provider_name)
                self.record_metric("provider.disconnect", 1, {"provider": self.provider_name})

    async def ensure_healthy(self, *, timeout: Optional[float] = None) -> bool:
        """Run a health check with optional timeout and convert exceptions.

        Returns True when the provider is healthy.
        """
        try:
            if timeout is None:
                healthy = await self.health_check()
            else:
                healthy = await asyncio.wait_for(self.health_check(), timeout)
        except asyncio.TimeoutError as exc:
            logger.warning("Health check for %s timed out", self.provider_name)
            raise OpsviLlmError(f"health_check timed out for {self.provider_name}") from exc
        except Exception as exc:  # pragma: no cover - defensive
            logger.exception("Health check failed for %s", self.provider_name)
            raise OpsviLlmError(f"health_check failed for {self.provider_name}: {exc}") from exc

        self.record_metric("provider.health", int(bool(healthy)), {"provider": self.provider_name})
        return bool(healthy)

    async def retry_connect(self, retries: int = 3, backoff: float = 0.5) -> bool:
        """Attempt to connect multiple times with exponential backoff.

        On success returns True. Raises OpsviLlmError if all attempts fail.
        """
        attempt = 0
        last_exc: Optional[BaseException] = None
        while attempt < retries:
            attempt += 1
            try:
                logger.debug("Attempt %d to connect to %s", attempt, self.provider_name)
                ok = await self.open()
                if ok:
                    return True
            except Exception as exc:
                last_exc = exc
                logger.debug("Connect attempt %d failed for %s: %s", attempt, self.provider_name, exc)
                # back off before next try
                await asyncio.sleep(backoff * (2 ** (attempt - 1)))

        logger.error("All %d connect attempts failed for %s", retries, self.provider_name)
        raise OpsviLlmError(f"failed to connect to {self.provider_name} after {retries} attempts") from last_exc

    async def timed_run(self, name: str, coro: Awaitable[Any], *, timeout: Optional[float] = None) -> Any:
        """Run a coroutine, measure duration and record a metric.

        If timeout is given and exceeded, an OpsviLlmError is raised.
        """
        start = time.monotonic()
        try:
            if timeout is None:
                result = await coro
            else:
                result = await asyncio.wait_for(coro, timeout)
        except asyncio.TimeoutError as exc:
            self.record_metric(f"{name}.timeout", 1, {"provider": self.provider_name})
            logger.warning("Timed out %s for provider %s", name, self.provider_name)
            raise OpsviLlmError(f"operation {name} timed out for {self.provider_name}") from exc
        finally:
            duration = time.monotonic() - start
            # record timing metric (value is seconds)
            self.record_metric(f"{name}.duration", duration, {"provider": self.provider_name})

        # success metric
        self.record_metric(f"{name}.success", 1, {"provider": self.provider_name})
        return result

    def record_metric(self, name: str, value: Any, tags: Optional[Dict[str, Any]] = None) -> None:
        """Lightweight hook for recording provider metrics.

        Providers or the manager may override this to integrate with metrics
        systems. The default implementation logs at debug level.
        """
        if tags is None:
            tags = {}
        logger.debug("metric %s=%s tags=%s", name, value, tags)

    async def __aenter__(self) -> "OpsviLlmProvider":
        await self.open()
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.close()

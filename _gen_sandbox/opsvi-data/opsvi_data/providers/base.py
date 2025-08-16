"""Provider base classes for opsvi-data.

Provides base classes for service providers.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Awaitable, Callable, Mapping
import asyncio
import logging
from contextlib import asynccontextmanager

from opsvi_data.core.base import OpsviDataManager
from opsvi_data.config.settings import OpsviDataConfig
from opsvi_data.exceptions.base import OpsviDataError

logger = logging.getLogger(__name__)


class OpsviDataProvider(OpsviDataManager, ABC):
    """Base provider class for opsvi-data.

    Subclasses must implement connect, disconnect and health_check. This base
    class provides common lifecycle helpers such as retrying connects,
    timeouts, safe disconnects, a context manager and a simple metric hook.
    """

    def __init__(self, config: OpsviDataConfig):
        super().__init__(config=config)
        self.provider_name = self.__class__.__name__

    @abstractmethod
    async def connect(self) -> bool:
        """Connect to the provider service.

        Should return True on success and raise an exception (or return False)
        on failure.
        """
        raise NotImplementedError

    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from the provider service."""
        raise NotImplementedError

    @abstractmethod
    async def health_check(self) -> bool:
        """Check provider health. Return True if healthy, False otherwise."""
        raise NotImplementedError

    async def connect_with_retries(
        self,
        retries: int = 3,
        initial_delay: float = 1.0,
        backoff: float = 2.0,
        timeout: Optional[float] = None,
    ) -> bool:
        """Attempt to connect with retries and exponential backoff.

        Raises OpsviDataError if unable to connect after the retries.
        """
        attempt = 0
        delay = initial_delay
        last_exc: Optional[BaseException] = None

        while attempt <= retries:
            try:
                attempt += 1
                logger.debug(
                    "%s: connect attempt %d/%d",
                    self.provider_name,
                    attempt,
                    retries + 1,
                )
                if timeout is not None:
                    result = await asyncio.wait_for(self.connect(), timeout=timeout)
                else:
                    result = await self.connect()

                if result:
                    logger.info("%s: connected on attempt %d", self.provider_name, attempt)
                    return True
                # If connect returned falsy but no exception, treat as failure and retry
                last_exc = OpsviDataError(f"{self.provider_name}: connect returned falsy result")
            except (asyncio.TimeoutError,) as exc:
                last_exc = OpsviDataError(f"{self.provider_name}: connect timed out")
                logger.warning("%s: connect timed out on attempt %d", self.provider_name, attempt)
            except Exception as exc:  # pragma: no cover - defensive
                last_exc = exc
                logger.exception("%s: connect failed on attempt %d", self.provider_name, attempt)

            if attempt > retries:
                break

            logger.debug("%s: retrying connect in %.2fs", self.provider_name, delay)
            try:
                await asyncio.sleep(delay)
            except asyncio.CancelledError:  # pragma: no cover - propagate cancellation
                logger.debug("%s: connect retry cancelled", self.provider_name)
                raise
            delay *= backoff

        raise OpsviDataError(
            f"{self.provider_name}: failed to connect after {retries + 1} attempts"
        ) from last_exc

    async def disconnect_safely(self) -> None:
        """Attempt to disconnect and suppress exceptions.

        Useful to call from cleanup code where failures should be logged but not
        propagated.
        """
        try:
            await self.disconnect()
            logger.info("%s: disconnected cleanly", self.provider_name)
        except Exception:  # pragma: no cover - defensive
            logger.exception("%s: error while disconnecting (suppressed)", self.provider_name)

    async def run_with_timeout(self, awaitable: Awaitable[Any], timeout: Optional[float]) -> Any:
        """Run an awaitable with an optional timeout.

        Raises OpsviDataError on timeout or cancellation.
        """
        try:
            if timeout is None:
                return await awaitable
            return await asyncio.wait_for(awaitable, timeout=timeout)
        except asyncio.TimeoutError as exc:  # pragma: no cover - expected behavior
            raise OpsviDataError(f"{self.provider_name}: operation timed out") from exc
        except asyncio.CancelledError:  # pragma: no cover - propagate
            logger.debug("%s: operation cancelled", self.provider_name)
            raise
        except Exception as exc:  # pragma: no cover - propagate underlying error
            raise

    @asynccontextmanager
    async def ensure_connected(
        self,
        retries: int = 3,
        initial_delay: float = 1.0,
        backoff: float = 2.0,
        timeout: Optional[float] = None,
    ):
        """Async context manager that ensures the provider is connected on enter
        and is disconnected (safely) on exit.

        Example:
            async with provider.ensure_connected():
                # do work with provider
        """
        await self.connect_with_retries(retries=retries, initial_delay=initial_delay, backoff=backoff, timeout=timeout)
        try:
            yield self
        finally:
            await self.disconnect_safely()

    async def run_health_watch(
        self,
        interval: float = 30.0,
        on_unhealthy: Optional[Callable[["OpsviDataProvider"], Awaitable[None] | None]] = None,
        stop_event: Optional[asyncio.Event] = None,
    ) -> None:
        """Run periodic health checks until stop_event is set.

        If on_unhealthy is provided it will be called with (self,) when a
        health_check returns False. This helper never raises; it logs errors
        and continues until stopped.
        """
        stop_event = stop_event or asyncio.Event()

        logger.info("%s: starting health watch (interval=%.1fs)", self.provider_name, interval)
        try:
            while not stop_event.is_set():
                try:
                    healthy = await self.health_check()
                    logger.debug("%s: health_check -> %s", self.provider_name, healthy)
                    if not healthy:
                        logger.warning("%s: reported unhealthy", self.provider_name)
                        if on_unhealthy:
                            try:
                                maybe_awaitable = on_unhealthy(self)
                                if asyncio.iscoroutine(maybe_awaitable):
                                    await maybe_awaitable
                            except Exception:
                                logger.exception("%s: on_unhealthy handler raised", self.provider_name)
                except Exception:
                    logger.exception("%s: health_check raised an unexpected error", self.provider_name)

                try:
                    await asyncio.wait_for(stop_event.wait(), timeout=interval)
                except asyncio.TimeoutError:
                    # timeout means interval elapsed; continue loop
                    continue
        finally:
            logger.info("%s: stopping health watch", self.provider_name)

    def metric_hook(self, name: str, value: Any, tags: Optional[Dict[str, str]] = None) -> None:
        """Lightweight hook to record provider-specific metrics.

        Default implementation logs the metric. Subclasses may override to
        integrate with monitoring/metrics systems.
        """
        tags = tags or {}
        try:
            logger.debug("%s: metric %s=%s tags=%s", self.provider_name, name, value, tags)
        except Exception:  # pragma: no cover - defensive
            # Never raise from a metric hook
            logger.exception("%s: failed to emit metric %s", self.provider_name, name)

    # Additional provider lifecycle helpers and metric utilities

    async def with_operation_metrics(
        self,
        op_name: str,
        coro: Awaitable[Any],
        tags: Optional[Mapping[str, str]] = None,
        timeout: Optional[float] = None,
    ) -> Any:
        """Run an operation while emitting start/end/duration metrics."""
        ttags: Dict[str, str] = dict(tags or {})
        self.metric_hook("op_start", op_name, tags=ttags)
        start = asyncio.get_running_loop().time()
        try:
            result = await self.run_with_timeout(coro, timeout)
            return result
        except Exception as exc:
            ttags_err = {**ttags, "error": exc.__class__.__name__}
            self.metric_hook("op_error", op_name, tags=ttags_err)
            raise
        finally:
            duration = asyncio.get_running_loop().time() - start
            self.metric_hook("op_duration_seconds", duration, tags={**ttags, "op": op_name})
            self.metric_hook("op_end", op_name, tags=ttags)

    async def reconnect(self, *, timeout: Optional[float] = None) -> bool:
        """Best-effort reconnect: disconnect safely then connect with retries=0."""
        await self.disconnect_safely()
        if timeout is not None:
            return await self.connect_with_retries(retries=0, timeout=timeout)
        return await self.connect_with_retries(retries=0)

    async def ensure_healthy_or_reconnect(
        self,
        *,
        health_timeout: Optional[float] = None,
        reconnect_timeout: Optional[float] = None,
    ) -> bool:
        """Validate health; if unhealthy, attempt a reconnect."""
        try:
            ok = await self.run_with_timeout(self.health_check(), health_timeout)
        except Exception:
            ok = False
        if ok:
            return True
        logger.warning("%s: health check failed, attempting reconnect", self.provider_name)
        return await self.reconnect(timeout=reconnect_timeout)

    async def graceful_shutdown(
        self,
        *,
        drain: Optional[Callable[["OpsviDataProvider"], Awaitable[None] | None]] = None,
        deadline: float = 10.0,
    ) -> None:
        """Gracefully shutdown provider: optional drain then safe disconnect."""
        try:
            if drain:
                maybe = drain(self)
                if asyncio.iscoroutine(maybe):
                    await asyncio.wait_for(maybe, timeout=deadline)
        except Exception:
            logger.exception("%s: drain step failed", self.provider_name)
        finally:
            try:
                await asyncio.wait_for(self.disconnect_safely(), timeout=deadline)
            except asyncio.TimeoutError:
                logger.warning("%s: graceful shutdown timed out", self.provider_name)

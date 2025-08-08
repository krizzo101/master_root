"""Provider base classes for opsvi-auth.

Provides base classes for service providers.
"""

from abc import ABC, abstractmethod
from typing import Dict, Optional, Callable, Awaitable, Tuple, Type, TypeVar
import asyncio
import logging
import time
import random
from contextlib import contextmanager

from opsvi_auth.core.base import OpsviAuthManager
from opsvi_auth.config.settings import OpsviAuthConfig
from opsvi_auth.exceptions.base import OpsviAuthError

logger = logging.getLogger(__name__)

T = TypeVar("T")


class OpsviAuthProvider(OpsviAuthManager, ABC):
    """Base provider class for opsvi-auth.

    Subclasses should implement the connect, disconnect and health_check
    coroutines to interact with the underlying provider service.

    The base class provides helpers for lifecycle management, retries and
    simple metrics hooks.
    """

    def __init__(self, config: OpsviAuthConfig):
        super().__init__(config=config)
        self.provider_name = self.__class__.__name__
        self._connected: bool = False
        # simple in-memory metrics counters
        self._metrics: Dict[str, float] = {}

    @property
    def is_connected(self) -> bool:
        """Return True when the provider has an active connection."""
        return self._connected

    @abstractmethod
    async def connect(self) -> bool:
        """Connect to the provider service.

        Implementations should perform any network or IO work necessary to
        establish a connection or client handle.

        Returns:
            bool: True on success, False on failure.
        """

    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from the provider service.

        Implementations should gracefully close any underlying resources.
        """

    @abstractmethod
    async def health_check(self) -> bool:
        """Check provider health.

        Implementations should perform a lightweight check to assert the
        provider is healthy and responsive.

        Returns:
            bool: True if healthy, False otherwise.
        """

    # --- Lifecycle helpers ------------------------------------------------

    async def connect_with_retries(
        self,
        attempts: int = 3,
        delay: float = 0.5,
        backoff: float = 2.0,
        timeout: Optional[float] = None,
    ) -> bool:
        """Attempt to connect with retries and optional timeout.

        Args:
            attempts: number of attempts before giving up.
            delay: initial delay between attempts in seconds.
            backoff: multiplier applied to delay after each failed attempt.
            timeout: maximum seconds allowed for each connect attempt.

        Returns:
            bool: True if connected, False otherwise.

        Raises:
            OpsviAuthError: wraps underlying exceptions.
        """
        attempt = 0
        current_delay = delay

        while attempt < attempts and not self._connected:
            attempt += 1
            try:
                logger.debug(
                    "%s: connect attempt %d/%d",
                    self.provider_name,
                    attempt,
                    attempts,
                )
                if timeout is None:
                    result = await self.connect()
                else:
                    result = await asyncio.wait_for(self.connect(), timeout)

                if result:
                    self._connected = True
                    logger.info("%s: connected", self.provider_name)
                    return True
                # If implementation returns False, treat as failure and retry
                logger.warning(
                    "%s: connect attempt %d returned False",
                    self.provider_name,
                    attempt,
                )
            except asyncio.CancelledError:
                logger.info("%s: connect cancelled", self.provider_name)
                raise
            except Exception as exc:  # pragma: no cover - defensive
                logger.exception(
                    "%s: exception on connect attempt %d: %s",
                    self.provider_name,
                    attempt,
                    exc,
                )
            if attempt < attempts:
                await asyncio.sleep(current_delay)
                current_delay *= backoff

        raise OpsviAuthError(
            f"{self.provider_name}: failed to connect after {attempts} attempts"
        )

    async def ensure_connected(self) -> None:
        """Ensure the provider is connected; otherwise attempt to connect once.

        Raises:
            OpsviAuthError: if the single connect attempt fails.
        """
        if self._connected:
            return
        try:
            ok = await self.connect()
        except Exception as exc:
            raise OpsviAuthError(f"{self.provider_name}: connect failed: {exc}")
        if not ok:
            raise OpsviAuthError(f"{self.provider_name}: connect returned False")
        self._connected = True

    async def safe_disconnect(self) -> None:
        """Call disconnect and swallow/log exceptions.

        The internal connected flag will be cleared regardless of errors.
        """
        if not self._connected:
            return
        try:
            await self.disconnect()
        except Exception as exc:
            logger.exception("%s: error during disconnect: %s", self.provider_name, exc)
        finally:
            self._connected = False
            logger.info("%s: disconnected", self.provider_name)

    async def run_health_check(self, timeout: Optional[float] = 5.0) -> bool:
        """Run health_check with an optional timeout and basic error handling.

        Returns:
            bool: True if healthy, False otherwise.
        """
        try:
            if timeout is None:
                result = await self.health_check()
            else:
                result = await asyncio.wait_for(self.health_check(), timeout)
            # Normalize truthiness
            healthy = bool(result)
            logger.debug(
                "%s: health_check -> %s", self.provider_name, healthy
            )
            return healthy
        except asyncio.TimeoutError:
            logger.warning("%s: health_check timed out", self.provider_name)
            return False
        except Exception as exc:
            logger.exception("%s: health_check exception: %s", self.provider_name, exc)
            return False

    # --- Async context manager for convenience ----------------------------

    async def __aenter__(self) -> "OpsviAuthProvider":
        """Enter async context: ensure connection established."""
        await self.ensure_connected()
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:  # type: ignore
        """Exit async context: try to disconnect gracefully."""
        await self.safe_disconnect()

    # --- Simple metrics hooks --------------------------------------------

    def record_metric(self, name: str, value: float) -> None:
        """Record a numeric metric locally. Subclasses or runtime can
        override this to integrate with external monitoring systems.
        """
        self._metrics[name] = float(value)
        logger.debug("%s: metric recorded %s=%s", self.provider_name, name, value)

    def increment_metric(self, name: str, amount: float = 1.0) -> None:
        """Increment a numeric metric stored locally."""
        self._metrics[name] = self._metrics.get(name, 0.0) + float(amount)
        logger.debug(
            "%s: metric incremented %s by %s (new=%s)",
            self.provider_name,
            name,
            amount,
            self._metrics[name],
        )

    def get_metric(self, name: str) -> Optional[float]:
        """Fetch a previously recorded metric value, if present."""
        return self._metrics.get(name)

    # --- Provider-specific lifecycle helpers and metrics hooks ------------

    async def wait_ready(
        self,
        *,
        timeout: float = 10.0,
        interval: float = 0.5,
        require_connected: bool = True,
    ) -> bool:
        """Wait until the provider is healthy or timeout."""
        if require_connected:
            await self.ensure_connected()
        start = time.perf_counter()
        while True:
            healthy = await self.run_health_check(timeout=min(5.0, timeout))
            if healthy:
                return True
            if (time.perf_counter() - start) >= timeout:
                return False
            await asyncio.sleep(interval)

    async def execute(
        self,
        name: str,
        func: Callable[[], Awaitable[T]],
        *,
        timeout: Optional[float] = None,
        retries: int = 0,
        delay: float = 0.1,
        backoff: float = 2.0,
        retry_exceptions: Tuple[Type[BaseException], ...] = (Exception,),
        ensure_connected: bool = True,
        wrap_errors: bool = True,
        jitter: float = 0.1,
    ) -> T:
        """Execute an async provider operation with timing and retries."""
        if ensure_connected:
            await self.ensure_connected()

        attempt = 0
        current_delay = max(0.0, delay)
        while True:
            attempt += 1
            self.increment_metric(f"op.{name}.attempts", 1.0)
            started = time.perf_counter()
            try:
                if timeout is None:
                    result = await func()
                else:
                    result = await asyncio.wait_for(func(), timeout)
                elapsed_ms = (time.perf_counter() - started) * 1000.0
                self.record_metric(f"op.{name}.latency_ms", elapsed_ms)
                self.increment_metric(f"op.{name}.latency_ms_total", elapsed_ms)
                self.increment_metric(f"op.{name}.success", 1.0)
                return result
            except asyncio.CancelledError:
                # Do not treat as a retriable error
                self.increment_metric(f"op.{name}.errors", 1.0)
                raise
            except retry_exceptions as exc:  # type: ignore[misc]
                self.increment_metric(f"op.{name}.errors", 1.0)
                if attempt - 1 < retries:
                    # backoff with jitter
                    sleep_for = current_delay + (random.random() * current_delay * jitter)
                    logger.warning(
                        "%s: op '%s' failed (attempt %d/%d): %s; retrying in %.3fs",
                        self.provider_name,
                        name,
                        attempt,
                        retries + 1,
                        exc,
                        sleep_for,
                    )
                    await asyncio.sleep(max(0.0, sleep_for))
                    current_delay *= max(1.0, backoff)
                    continue
                # Exhausted retries
                msg = f"{self.provider_name}: operation '{name}' failed after {attempt} attempts"
                if wrap_errors:
                    raise OpsviAuthError(msg) from exc
                raise

    @contextmanager
    def record_time(self, name: str):
        """Sync context manager to record elapsed time in ms for a block."""
        start = time.perf_counter()
        try:
            yield
        finally:
            elapsed_ms = (time.perf_counter() - start) * 1000.0
            self.record_metric(f"op.{name}.latency_ms", elapsed_ms)
            self.increment_metric(f"op.{name}.latency_ms_total", elapsed_ms)

    def metrics_snapshot(self) -> Dict[str, float]:
        """Return a shallow copy of current metrics."""
        return dict(self._metrics)

    def clear_metrics(self) -> None:
        """Clear all stored metrics."""
        self._metrics.clear()

    async def status(self, sample_health: bool = False) -> Dict[str, object]:
        """Return provider status summary."""
        health: Optional[bool] = None
        if sample_health:
            health = await self.run_health_check(timeout=2.0)
        return {
            "provider": self.provider_name,
            "connected": self._connected,
            "healthy": health,
            "metrics": self.metrics_snapshot(),
        }

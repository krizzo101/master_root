"""opsvi-monitoring - Core opsvi-monitoring functionality.

Comprehensive opsvi-monitoring library for the OPSVI ecosystem
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Awaitable, Callable, Dict, List, Optional
import asyncio
import logging
import time

from opsvi_foundation import BaseComponent, ComponentError
from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)


class OpsviMonitoringManagerError(ComponentError):
    """Base exception for opsvi-monitoring errors."""
    pass


class OpsviMonitoringManagerConfigurationError(OpsviMonitoringManagerError):
    """Configuration-related errors in opsvi-monitoring."""
    pass


class OpsviMonitoringManagerInitializationError(OpsviMonitoringManagerError):
    """Initialization-related errors in opsvi-monitoring."""
    pass


class OpsviMonitoringManagerConfig(BaseSettings):
    """Configuration for opsvi-monitoring."""

    # Core configuration
    enabled: bool = True
    debug: bool = False
    log_level: str = "INFO"

    # Metrics buffer settings
    buffer_size: int = 1000
    flush_interval_seconds: float = 5.0

    class Config:
        env_prefix = "OPSVI_OPSVI_MONITORING__"


class MetricRecord(BaseSettings):
    """Simple metric record."""

    name: str
    value: float
    tags: Dict[str, str] = {}
    timestamp: float = 0.0


class OpsviMonitoringManager(BaseComponent):
    """Base class for opsvi-monitoring components.

    Provides base functionality for all opsvi-monitoring components
    """

    def __init__(
        self,
        config: Optional[OpsviMonitoringManagerConfig] = None,
        **kwargs: Any
    ) -> None:
        """Initialize OpsviMonitoringManager.

        Args:
            config: Configuration for the component
            **kwargs: Additional configuration parameters
        """
        cfg = config or OpsviMonitoringManagerConfig(**kwargs)
        super().__init__("opsvi-monitoring", cfg.dict())
        self.config = cfg
        self._initialized = False
        self._logger = logging.getLogger(f"{__name__}.opsvi-monitoring")

        # State
        self._queue: asyncio.Queue[MetricRecord] = asyncio.Queue(maxsize=max(self.config.buffer_size, 1))
        self._bg_task: Optional[asyncio.Task[None]] = None
        self._shutdown_event = asyncio.Event()

        # Configure logger level early
        try:
            level = getattr(logging, self.config.log_level.upper(), logging.INFO)
            self._logger.setLevel(level)
        except Exception:
            self._logger.setLevel(logging.INFO)

    async def initialize(self) -> None:
        """Initialize the component.

        Raises:
            OpsviMonitoringManagerInitializationError: If initialization fails
        """
        if self._initialized:
            return
        try:
            if not self.config.enabled:
                self._logger.info("opsvi-monitoring disabled by configuration")
                self._initialized = True
                return

            self._logger.info("Initializing opsvi-monitoring")
            self._shutdown_event.clear()
            self._bg_task = asyncio.create_task(self._flush_loop(), name="opsvi-monitoring-flusher")
            self._initialized = True
            self._logger.info("opsvi-monitoring initialized successfully")
        except Exception as e:
            self._logger.error(f"Failed to initialize opsvi-monitoring: {e}")
            raise OpsviMonitoringManagerInitializationError(f"Initialization failed: {e}") from e

    async def shutdown(self) -> None:
        """Shutdown the component.

        Raises:
            OpsviMonitoringManagerError: If shutdown fails
        """
        try:
            if not self._initialized:
                return
            self._logger.info("Shutting down opsvi-monitoring")
            self._shutdown_event.set()
            if self._bg_task:
                self._bg_task.cancel()
                try:
                    await self._bg_task
                except asyncio.CancelledError:
                    pass
                self._bg_task = None

            # Final flush
            await self._drain_and_flush()

            self._initialized = False
            self._logger.info("opsvi-monitoring shut down successfully")
        except Exception as e:
            self._logger.error(f"Failed to shutdown opsvi-monitoring: {e}")
            raise OpsviMonitoringManagerError(f"Shutdown failed: {e}") from e

    async def health_check(self) -> bool:
        """Perform health check.

        Returns:
            True if healthy, False otherwise
        """
        try:
            if not self._initialized:
                return False
            if not self.config.enabled:
                return True
            # basic check: background task alive and queue operational
            task_ok = self._bg_task is not None and not self._bg_task.done()
            return bool(task_ok)
        except Exception as e:
            self._logger.error(f"Health check failed: {e}")
            return False

    # Component-specific methods
    async def record_metric(self, name: str, value: float, tags: Optional[Dict[str, str]] = None) -> None:
        """Record a metric into the buffer."""
        if not self._initialized or not self.config.enabled:
            return
        rec = MetricRecord(name=name, value=float(value), tags=tags or {}, timestamp=time.time())
        try:
            self._queue.put_nowait(rec)
        except asyncio.QueueFull:
            # Drop oldest to make room (best-effort backpressure relief)
            try:
                _ = self._queue.get_nowait()
            except asyncio.QueueEmpty:
                pass
            try:
                self._queue.put_nowait(rec)
            except asyncio.QueueFull:
                if self.config.debug:
                    self._logger.warning("Metric queue full; dropping metric %s", name)

    async def gauge(self, name: str, value: float, tags: Optional[Dict[str, str]] = None) -> None:
        """Alias to record a gauge metric."""
        await self.record_metric(name, value, tags)

    async def increment(self, name: str, value: float = 1.0, tags: Optional[Dict[str, str]] = None) -> None:
        """Increment a counter metric."""
        await self.record_metric(name, value, tags)

    async def time_async(self, name: str, coro: Awaitable[Any], tags: Optional[Dict[str, str]] = None) -> Any:
        """Time an async operation and emit a metric."""
        start = time.perf_counter()
        try:
            return await coro
        finally:
            duration_ms = (time.perf_counter() - start) * 1000.0
            await self.record_metric(name, duration_ms, {**(tags or {}), "unit": "ms"})

    def timer(self, name: str, tags: Optional[Dict[str, str]] = None) -> "_TimerCtx":
        """Context manager for timing sync/async blocks."""
        return _TimerCtx(self, name, tags or {})

    # Internal flushing
    async def _flush_loop(self) -> None:
        interval = max(self.config.flush_interval_seconds, 0.1)
        try:
            while not self._shutdown_event.is_set():
                await asyncio.sleep(interval)
                await self._drain_and_flush()
        except asyncio.CancelledError:
            # On cancellation, just exit; shutdown will drain
            raise
        except Exception as e:
            self._logger.error("Flusher loop error: %s", e)

    async def _drain_and_flush(self) -> None:
        records: List[MetricRecord] = []
        try:
            while True:
                try:
                    rec = self._queue.get_nowait()
                except asyncio.QueueEmpty:
                    break
                else:
                    records.append(rec)
        except Exception as e:
            self._logger.error("Error draining metrics: %s", e)
            return

        if not records:
            return
        try:
            await self._flush(records)
        except Exception as e:
            # On failure, attempt to requeue a limited subset
            self._logger.error("Error flushing %d metrics: %s", len(records), e)
            for rec in records[-min(len(records), self._queue.maxsize) :]:
                try:
                    self._queue.put_nowait(rec)
                except asyncio.QueueFull:
                    break

    async def _flush(self, records: List[MetricRecord]) -> None:
        """Flush metrics. Default logs them; override to integrate sinks."""
        if self.config.debug:
            for r in records:
                self._logger.debug("metric name=%s value=%s tags=%s ts=%s", r.name, r.value, r.tags, int(r.timestamp))
        else:
            self._logger.info("Flushed %d metrics", len(records))


class _TimerCtx:
    """Timing context supporting sync and async usage."""

    def __init__(self, mgr: OpsviMonitoringManager, name: str, tags: Dict[str, str]) -> None:
        self._mgr = mgr
        self._name = name
        self._tags = tags
        self._start = 0.0

    def __enter__(self) -> "_TimerCtx":
        self._start = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        dur_ms = (time.perf_counter() - self._start) * 1000.0
        # fire and forget; safe if no loop
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self._mgr.record_metric(self._name, dur_ms, {**self._tags, "unit": "ms"}))
        except RuntimeError:
            # No running loop; do nothing
            pass

    async def __aenter__(self) -> "_TimerCtx":
        self._start = time.perf_counter()
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        dur_ms = (time.perf_counter() - self._start) * 1000.0
        await self._mgr.record_metric(self._name, dur_ms, {**self._tags, "unit": "ms"})

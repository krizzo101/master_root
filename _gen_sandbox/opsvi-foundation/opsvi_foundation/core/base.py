"""opsvi-foundation - Core opsvi-foundation functionality.

Comprehensive opsvi-foundation library for the OPSVI ecosystem
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Awaitable, Callable, Dict, Optional, Set

from opsvi_foundation import BaseComponent, ComponentError
from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)


class OpsviFoundationManagerError(ComponentError):
    """Base exception for opsvi-foundation errors."""


class OpsviFoundationManagerConfigurationError(OpsviFoundationManagerError):
    """Configuration-related errors in opsvi-foundation."""


class OpsviFoundationManagerInitializationError(OpsviFoundationManagerError):
    """Initialization-related errors in opsvi-foundation."""


class OpsviFoundationManagerConfig(BaseSettings):
    """Configuration for opsvi-foundation."""

    # Core configuration
    enabled: bool = True
    debug: bool = False
    log_level: str = "INFO"

    # Operational timings
    health_check_interval: float = 30.0
    startup_timeout: float = 10.0
    shutdown_timeout: float = 10.0

    class Config:
        env_prefix = "OPSVI_OPSVI_FOUNDATION__"


class OpsviFoundationManager(BaseComponent):
    """Base class for opsvi-foundation components.

    Provides base functionality for all opsvi-foundation components.
    """

    def __init__(
        self,
        config: Optional[OpsviFoundationManagerConfig] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize OpsviFoundationManager."""
        cfg = config or OpsviFoundationManagerConfig(**kwargs)
        super().__init__("opsvi-foundation", cfg.model_dump())
        self.config: OpsviFoundationManagerConfig = cfg
        self._initialized: bool = False
        self._health_ok: bool = False
        self._logger = logging.getLogger(f"{__name__}.opsvi-foundation")
        self._tasks: Set[asyncio.Task[None]] = set()
        self._state_lock = asyncio.Lock()
        self._started_event = asyncio.Event()

    # ----- lifecycle -----
    async def initialize(self) -> None:
        """Initialize the component."""
        async with self._state_lock:
            if self._initialized:
                return

            try:
                self._configure_logging()
                self._logger.info("Initializing opsvi-foundation (enabled=%s)", self.config.enabled)

                if not self.config.enabled:
                    self._health_ok = True
                    self._initialized = True
                    self._started_event.set()
                    self._logger.warning("opsvi-foundation is disabled by configuration")
                    return

                # Start periodic health check if configured
                if self.config.health_check_interval > 0:
                    self.start_background_task(
                        self._periodic_health_check(self.config.health_check_interval),
                        name="opsvi-foundation.health-check",
                    )

                self._initialized = True
                self._health_ok = True
                self._started_event.set()
                self._logger.info("opsvi-foundation initialized successfully")

            except Exception as e:  # pragma: no cover - defensive logging
                self._logger.error("Failed to initialize opsvi-foundation: %s", e)
                raise OpsviFoundationManagerInitializationError(f"Initialization failed: {e}") from e

    async def shutdown(self) -> None:
        """Shutdown the component."""
        async with self._state_lock:
            if not self._initialized:
                return

            self._logger.info("Shutting down opsvi-foundation")
            try:
                await self._cancel_tasks(timeout=self.config.shutdown_timeout)
            finally:
                self._initialized = False
                self._health_ok = False
                self._started_event.clear()
                self._logger.info("opsvi-foundation shut down successfully")

    async def __aenter__(self) -> "OpsviFoundationManager":
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.shutdown()

    # ----- health -----
    async def health_check(self) -> bool:
        """Perform health check."""
        try:
            return self._initialized
        except Exception as e:  # pragma: no cover - defensive logging
            self._logger.error("Health check failed: %s", e)
            return False

    async def wait_until_ready(self, timeout: Optional[float] = None) -> bool:
        """Wait until the manager has finished initialization."""
        try:
            await asyncio.wait_for(self._started_event.wait(), timeout=timeout)
            return True
        except asyncio.TimeoutError:
            return False

    def is_healthy(self) -> bool:
        """Return the last known health status."""
        return self._initialized and self._health_ok

    def require_healthy(self) -> None:
        """Raise if not healthy."""
        if not self.is_healthy():
            raise OpsviFoundationManagerError("Component is not healthy")

    # ----- background tasks -----
    def start_background_task(self, coro: Awaitable[None], *, name: Optional[str] = None) -> asyncio.Task[None]:
        """Start and track a background task."""
        task = asyncio.create_task(coro, name=name or "opsvi-foundation.task")
        self._tasks.add(task)

        def _done(t: asyncio.Task[None]) -> None:
            self._tasks.discard(t)
            try:
                exc = t.exception()
                if exc is not None:
                    self._logger.error("Background task %r failed: %s", t.get_name(), exc)
            except asyncio.CancelledError:
                pass
            except Exception as e:  # pragma: no cover - defensive logging
                self._logger.error("Error collecting task result: %s", e)

        task.add_done_callback(_done)
        return task

    async def _cancel_tasks(self, *, timeout: float) -> None:
        if not self._tasks:
            return
        for t in list(self._tasks):
            if not t.done():
                t.cancel()
        if not self._tasks:
            return
        try:
            await asyncio.wait(self._tasks, timeout=timeout)
        finally:
            # Any still-pending tasks will be logged
            for t in list(self._tasks):
                if not t.done():
                    self._logger.warning("Task %r did not finish before timeout", t.get_name())
                self._tasks.discard(t)

    async def _periodic_health_check(self, interval: float) -> None:
        try:
            while self._initialized:
                ok = await self.health_check()
                self._health_ok = ok
                await asyncio.sleep(max(0.1, interval))
        except asyncio.CancelledError:
            pass
        except Exception as e:  # pragma: no cover - defensive logging
            self._logger.error("Periodic health check crashed: %s", e)

    # ----- configuration / logging -----
    def _configure_logging(self) -> None:
        level_name = "DEBUG" if self.config.debug else (self.config.log_level or "INFO")
        level = getattr(logging, str(level_name).upper(), logging.INFO)
        self._logger.setLevel(level)
        logger.setLevel(level)

    def update_config(self, **kwargs: Any) -> OpsviFoundationManagerConfig:
        """Update runtime configuration and return the new config."""
        try:
            new_cfg = self.config.model_copy(update=kwargs)
        except Exception as e as e2:  # type: ignore
            # Handle potential validation errors from pydantic
            raise OpsviFoundationManagerConfigurationError(f"Invalid configuration: {e}") from e
        self.config = new_cfg
        self._configure_logging()
        return self.config

    # ----- inspection -----
    def status(self) -> Dict[str, Any]:
        """Return a status snapshot."""
        return {
            "name": "opsvi-foundation",
            "initialized": self._initialized,
            "healthy": self.is_healthy(),
            "tasks": [t.get_name() for t in self._tasks],
            "config": {
                "enabled": self.config.enabled,
                "debug": self.config.debug,
                "log_level": self.config.log_level,
                "health_check_interval": self.config.health_check_interval,
            },
        }

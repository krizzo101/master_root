"""opsvi-gateway - Core opsvi-gateway functionality.

Comprehensive opsvi-gateway library for the OPSVI ecosystem
"""

from __future__ import annotations

from typing import Any, Awaitable, Callable, Dict, Optional
import asyncio
import logging

from opsvi_foundation import BaseComponent, ComponentError
from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)


class OpsviGatewayManagerError(ComponentError):
    """Base exception for opsvi-gateway errors."""


class OpsviGatewayManagerConfigurationError(OpsviGatewayManagerError):
    """Configuration-related errors in opsvi-gateway."""


class OpsviGatewayManagerInitializationError(OpsviGatewayManagerError):
    """Initialization-related errors in opsvi-gateway."""


class OpsviGatewayManagerConfig(BaseSettings):
    """Configuration for opsvi-gateway."""

    # Core configuration
    enabled: bool = True
    debug: bool = False
    log_level: str = "INFO"

    # Component-specific configuration
    startup_timeout_s: float = 10.0
    shutdown_timeout_s: float = 10.0
    healthcheck_timeout_s: float = 3.0
    # Interval for internal periodic tasks (e.g., housekeeping)
    tick_interval_s: float = 30.0

    class Config:
        env_prefix = "OPSVI_OPSVI_GATEWAY__"


class OpsviGatewayManager(BaseComponent):
    """Base class for opsvi-gateway components.

    Provides base functionality for all opsvi-gateway components
    """

    def __init__(
        self,
        config: Optional[OpsviGatewayManagerConfig] = None,
        **kwargs: Any
    ) -> None:
        """Initialize OpsviGatewayManager.

        Args:
            config: Configuration for the component
            **kwargs: Additional configuration parameters
        """
        # Create config first to feed BaseComponent with a dict
        cfg = config or OpsviGatewayManagerConfig(**kwargs)
        super().__init__("opsvi-gateway", cfg.dict())
        self.config = cfg
        self._initialized = False
        self._logger = logging.getLogger(f"{__name__}.opsvi-gateway")

        # Component-specific initialization
        self._periodic_task: Optional[asyncio.Task[None]] = None
        self._stop_event = asyncio.Event()
        self._startup_hooks: list[Callable[[], Awaitable[None]]] = []
        self._shutdown_hooks: list[Callable[[], Awaitable[None]]] = []
        self._health_probes: list[Callable[[], Awaitable[bool]]] = []

        # Setup logging level from config
        level = getattr(logging, self.config.log_level.upper(), logging.INFO)
        self._logger.setLevel(level)

    def add_startup_hook(self, hook: Callable[[], Awaitable[None]]) -> None:
        """Register an async startup hook executed during initialize."""
        self._startup_hooks.append(hook)

    def add_shutdown_hook(self, hook: Callable[[], Awaitable[None]]) -> None:
        """Register an async shutdown hook executed during shutdown."""
        self._shutdown_hooks.append(hook)

    def add_health_probe(self, probe: Callable[[], Awaitable[bool]]) -> None:
        """Register an async health probe contributing to health_check."""
        self._health_probes.append(probe)

    async def _run_hooks(self, hooks: list[Callable[[], Awaitable[None]]], timeout: float, phase: str) -> None:
        async def run_with_guard(fn: Callable[[], Awaitable[None]]) -> None:
            await fn()

        if not hooks:
            return

        tasks = [asyncio.create_task(run_with_guard(h)) for h in hooks]
        try:
            await asyncio.wait_for(asyncio.gather(*tasks), timeout=timeout)
        except Exception as e:  # noqa: BLE001
            self._logger.exception("%s hooks failed", phase)
            raise

    async def _periodic(self) -> None:
        """Background periodic task to run lightweight maintenance."""
        interval = max(0.1, float(self.config.tick_interval_s))
        self._logger.debug("Starting periodic task with interval=%ss", interval)
        try:
            while not self._stop_event.is_set():
                try:
                    # Placeholder for housekeeping; override by registering hooks if needed
                    await asyncio.sleep(interval)
                except asyncio.CancelledError:
                    raise
                except Exception:  # noqa: BLE001
                    self._logger.exception("Periodic task loop error")
        finally:
            self._logger.debug("Periodic task exiting")

    async def initialize(self) -> None:
        """Initialize the component."""
        if self._initialized:
            return
        if not self.config.enabled:
            self._logger.info("opsvi-gateway disabled by configuration")
            self._initialized = True
            return

        try:
            self._logger.info("Initializing opsvi-gateway")
            await self._run_hooks(self._startup_hooks, self.config.startup_timeout_s, "Startup")

            # Start background task
            self._stop_event.clear()
            self._periodic_task = asyncio.create_task(self._periodic(), name="opsvi-gateway-periodic")

            self._initialized = True
            self._logger.info("opsvi-gateway initialized successfully")
        except Exception as e:  # noqa: BLE001
            self._logger.error("Failed to initialize opsvi-gateway: %s", e)
            # Ensure cleanup if periodic spawned
            await self._cancel_periodic()
            raise OpsviGatewayManagerInitializationError(f"Initialization failed: {e}") from e

    async def _cancel_periodic(self) -> None:
        task = self._periodic_task
        self._periodic_task = None
        if task and not task.done():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            except Exception:  # noqa: BLE001
                self._logger.exception("Error while cancelling periodic task")

    async def shutdown(self) -> None:
        """Shutdown the component."""
        try:
            self._logger.info("Shutting down opsvi-gateway")

            # Stop background task
            self._stop_event.set()
            await self._cancel_periodic()

            # Run shutdown hooks
            await self._run_hooks(self._shutdown_hooks, self.config.shutdown_timeout_s, "Shutdown")

            self._initialized = False
            self._logger.info("opsvi-gateway shut down successfully")
        except Exception as e:  # noqa: BLE001
            self._logger.error("Failed to shutdown opsvi-gateway: %s", e)
            raise OpsviGatewayManagerError(f"Shutdown failed: {e}") from e

    async def health_check(self) -> bool:
        """Perform health check."""
        if not self._initialized:
            return False

        try:
            # Periodic task should be alive when enabled
            if self.config.enabled:
                if self._periodic_task is None or self._periodic_task.done():
                    return False

            # Run probes with timeout; fail-fast on first False
            if not self._health_probes:
                return True

            async def run_probe(p: Callable[[], Awaitable[bool]]) -> bool:
                return await p()

            probes = [asyncio.create_task(run_probe(p)) for p in self._health_probes]
            try:
                results = await asyncio.wait_for(asyncio.gather(*probes, return_exceptions=True),
                                                 timeout=self.config.healthcheck_timeout_s)
            finally:
                # Ensure all tasks finished/cancelled
                for t in probes:
                    if not t.done():
                        t.cancel()
            for r in results:
                if isinstance(r, Exception) or r is False:
                    return False
            return True
        except asyncio.TimeoutError:
            self._logger.warning("Health check timed out")
            return False
        except Exception as e:  # noqa: BLE001
            self._logger.error("Health check failed: %s", e)
            return False

    # Convenience context manager helpers
    async def __aenter__(self) -> "OpsviGatewayManager":
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:  # noqa: ANN001
        await self.shutdown()

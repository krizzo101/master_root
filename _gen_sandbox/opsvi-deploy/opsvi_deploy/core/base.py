"""opsvi-deploy - Core opsvi-deploy functionality.

Comprehensive opsvi-deploy library for the OPSVI ecosystem
"""

from __future__ import annotations

from typing import Any, Awaitable, Callable, Coroutine, Dict, List, Optional
import asyncio
import logging

from opsvi_foundation import BaseComponent, ComponentError
from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)


class OpsviDeployManagerError(ComponentError):
    """Base exception for opsvi-deploy errors."""
    pass


class OpsviDeployManagerConfigurationError(OpsviDeployManagerError):
    """Configuration-related errors in opsvi-deploy."""
    pass


class OpsviDeployManagerInitializationError(OpsviDeployManagerError):
    """Initialization-related errors in opsvi-deploy."""
    pass


class OpsviDeployManagerConfig(BaseSettings):
    """Configuration for opsvi-deploy."""

    # Core configuration
    enabled: bool = True
    debug: bool = False
    log_level: str = "INFO"

    # Timeouts
    startup_timeout: float = 30.0
    shutdown_timeout: float = 30.0
    health_check_timeout: float = 5.0

    # Health monitoring
    auto_health_monitor: bool = False
    health_monitor_interval: float = 30.0

    # Optional name for logging context
    name: Optional[str] = None

    class Config:
        env_prefix = "OPSVI_OPSVI_DEPLOY__"


AsyncHook = Callable[[], Awaitable[None]]
HealthHook = Callable[[], Awaitable[bool]]


class OpsviDeployManager(BaseComponent):
    """Base class for opsvi-deploy components.

    Provides base functionality for all opsvi-deploy components
    """

    def __init__(
        self,
        config: Optional[OpsviDeployManagerConfig] = None,
        **kwargs: Any
    ) -> None:
        """Initialize OpsviDeployManager.

        Args:
            config: Configuration for the component
            **kwargs: Additional configuration parameters
        """
        # Defer to provided config or build from kwargs
        cfg = config or OpsviDeployManagerConfig(**kwargs)
        super().__init__(cfg.name or "opsvi-deploy", cfg.dict())
        self.config = cfg
        self._initialized: bool = False
        self._disabled: bool = not self.config.enabled
        self._logger = logging.getLogger(f"{__name__}.{self.config.name or 'opsvi-deploy'}")

        # Lifecycle hooks
        self._startup_hooks: List[AsyncHook] = []
        self._shutdown_hooks: List[AsyncHook] = []
        self._health_hooks: List[HealthHook] = []

        # Task management
        self._tasks: Dict[str, asyncio.Task[Any]] = {}
        self._health_monitor_task: Optional[asyncio.Task[None]] = None

    # ------------------------- public lifecycle -------------------------
    async def initialize(self) -> None:
        """Initialize the component."""
        try:
            self._configure_logging()
            self._logger.info("Initializing %s", self.name)

            if self._disabled:
                self._logger.warning("Component is disabled via configuration; skipping initialization")
                self._initialized = True
                return

            loop = asyncio.get_running_loop()
            loop.set_debug(self.config.debug)

            # Run startup hooks concurrently
            await self._run_hooks(self._startup_hooks, self.config.startup_timeout, "startup")

            # Optionally start health monitor
            if self.config.auto_health_monitor and self._health_hooks and not self._health_monitor_task:
                self._health_monitor_task = self.run_background(self._health_monitor_loop(), name="health-monitor")

            self._initialized = True
            self._logger.info("%s initialized successfully", self.name)

        except Exception as e:
            self._logger.error("Failed to initialize %s: %s", self.name, e)
            raise OpsviDeployManagerInitializationError(f"Initialization failed: {e}") from e

    async def shutdown(self) -> None:
        """Shutdown the component."""
        try:
            self._logger.info("Shutting down %s", self.name)

            # Stop health monitor first
            await self._cancel_task("health-monitor")

            # Run shutdown hooks
            await self._run_hooks(self._shutdown_hooks, self.config.shutdown_timeout, "shutdown")

            # Cancel all remaining background tasks
            await self._cancel_all_tasks()

            self._initialized = False
            self._logger.info("%s shut down successfully", self.name)

        except Exception as e:
            self._logger.error("Failed to shutdown %s: %s", self.name, e)
            raise OpsviDeployManagerError(f"Shutdown failed: {e}") from e

    async def health_check(self) -> bool:
        """Perform health check and return overall health state."""
        try:
            if not self._initialized:
                return False

            if not self._health_hooks:
                return True

            results = await asyncio.wait_for(
                asyncio.gather(*(hook() for hook in self._health_hooks), return_exceptions=True),
                timeout=self.config.health_check_timeout,
            )
            healthy = True
            for res in results:
                if isinstance(res, Exception):
                    self._logger.warning("Health hook exception: %s", res)
                    healthy = False
                elif not res:
                    healthy = False
            return healthy

        except asyncio.TimeoutError:
            self._logger.error("Health check timed out")
            return False
        except Exception as e:
            self._logger.error("Health check failed: %s", e)
            return False

    # ------------------------- hooks API -------------------------
    def register_startup_hook(self, hook: AsyncHook) -> None:
        """Register a coroutine function executed during initialize."""
        self._validate_async_callable(hook, "startup")
        self._startup_hooks.append(hook)

    def register_shutdown_hook(self, hook: AsyncHook) -> None:
        """Register a coroutine function executed during shutdown."""
        self._validate_async_callable(hook, "shutdown")
        self._shutdown_hooks.append(hook)

    def register_health_hook(self, hook: HealthHook) -> None:
        """Register a coroutine function that returns True if healthy."""
        self._validate_async_callable(hook, "health")
        self._health_hooks.append(hook)

    # ------------------------- task management -------------------------
    def run_background(self, coro: Coroutine[Any, Any, Any], name: Optional[str] = None) -> asyncio.Task[Any]:
        """Run and track a background task, logging exceptions."""
        if not asyncio.iscoroutine(coro):
            raise OpsviDeployManagerError("run_background requires a coroutine")

        task_name = self._unique_task_name(name or getattr(coro, "__name__", "task"))
        task = asyncio.create_task(coro, name=task_name)
        self._tasks[task_name] = task
        task.add_done_callback(lambda t, n=task_name: self._on_task_done(n, t))
        self._logger.debug("Started background task: %s", task_name)
        return task

    async def _cancel_task(self, name: str) -> None:
        task = self._tasks.pop(name, None)
        if task and not task.done():
            task.cancel()
            try:
                await asyncio.wait_for(task, timeout=self.config.shutdown_timeout)
            except asyncio.CancelledError:
                pass
            except asyncio.TimeoutError:
                self._logger.warning("Timeout while cancelling task: %s", name)
            except Exception as e:
                self._logger.warning("Error while cancelling task %s: %s", name, e)

    async def _cancel_all_tasks(self) -> None:
        names = list(self._tasks.keys())
        for name in names:
            await self._cancel_task(name)

    # ------------------------- internals -------------------------
    def _configure_logging(self) -> None:
        level = getattr(logging, str(self.config.log_level).upper(), None)
        if not isinstance(level, int):
            raise OpsviDeployManagerConfigurationError(
                f"Invalid log_level: {self.config.log_level}"
            )
        logging.getLogger().setLevel(level)
        self._logger.setLevel(level)

    def _validate_async_callable(self, fn: Callable[..., Any], kind: str) -> None:
        if not callable(fn) or not asyncio.iscoroutinefunction(fn):
            raise OpsviDeployManagerConfigurationError(
                f"{kind} hook must be an async function"
            )

    async def _run_hooks(self, hooks: List[AsyncHook], timeout: float, phase: str) -> None:
        if not hooks:
            return
        try:
            await asyncio.wait_for(
                asyncio.gather(*(h() for h in hooks), return_exceptions=False),
                timeout=timeout,
            )
        except asyncio.TimeoutError as te:
            raise OpsviDeployManagerInitializationError(f"{phase} hooks timed out") from te

    def _on_task_done(self, name: str, task: asyncio.Task[Any]) -> None:
        try:
            _ = task.result()
        except asyncio.CancelledError:
            self._logger.debug("Background task cancelled: %s", name)
        except Exception as e:
            self._logger.error("Background task '%s' failed: %s", name, e)
        finally:
            # Ensure removed from registry
            self._tasks.pop(name, None)

    def _unique_task_name(self, base: str) -> str:
        if base not in self._tasks:
            return base
        i = 1
        while f"{base}-{i}" in self._tasks:
            i += 1
        return f"{base}-{i}"

    async def _health_monitor_loop(self) -> None:
        interval = max(0.1, float(self.config.health_monitor_interval))
        while True:
            try:
                healthy = await self.health_check()
                if not healthy:
                    self._logger.warning("Health monitor detected unhealthy state")
            except asyncio.CancelledError:
                raise
            except Exception as e:
                self._logger.error("Health monitor error: %s", e)
            await asyncio.sleep(interval)

    # ------------------------- helpers -------------------------
    @property
    def initialized(self) -> bool:
        """True if initialize has completed."""
        return self._initialized

    @property
    def enabled(self) -> bool:
        """True if component is enabled by config."""
        return not self._disabled

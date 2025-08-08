"""opsvi-core - Core opsvi-core functionality.

Comprehensive opsvi-core library for the OPSVI ecosystem
"""

from __future__ import annotations

from typing import Any, Awaitable, Callable, Dict, Optional
import asyncio
import logging

from opsvi_foundation import BaseComponent, ComponentError
from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)


class OpsviCoreManagerError(ComponentError):
    """Base exception for opsvi-core errors."""


class OpsviCoreManagerConfigurationError(OpsviCoreManagerError):
    """Configuration-related errors in opsvi-core."""


class OpsviCoreManagerInitializationError(OpsviCoreManagerError):
    """Initialization-related errors in opsvi-core."""


class OpsviCoreManagerConfig(BaseSettings):
    """Configuration for opsvi-core."""

    # Core configuration
    enabled: bool = True
    debug: bool = False
    log_level: str = "INFO"

    # Async task management
    task_shutdown_timeout: float = 5.0
    restart_backoff_min: float = 0.1
    restart_backoff_max: float = 5.0

    class Config:
        env_prefix = "OPSVI_OPSVI_CORE__"


class OpsviCoreManager(BaseComponent):
    """Base class for opsvi-core components.

    Provides base functionality for all opsvi-core components
    """

    def __init__(
        self,
        config: Optional[OpsviCoreManagerConfig] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize OpsviCoreManager."""
        super().__init__("opsvi-core", (config.dict() if config else kwargs))
        self.config = config or OpsviCoreManagerConfig(**kwargs)
        self._initialized: bool = False
        self._shutdown: bool = False
        self._logger = logging.getLogger(f"{__name__}.opsvi-core")

        # Async task tracking
        self._tasks: Dict[str, asyncio.Task[Any]] = {}
        self._task_meta: Dict[str, Dict[str, Any]] = {}
        self._lock = asyncio.Lock()

    # ---- lifecycle ----
    async def initialize(self) -> None:
        """Initialize the component."""
        if self._initialized:
            return
        try:
            level_name = "DEBUG" if self.config.debug else self.config.log_level.upper()
            level = getattr(logging, level_name, logging.INFO)
            self._logger.setLevel(level)
            logger.setLevel(level)

            if not self.config.enabled:
                self._logger.info("opsvi-core is disabled by configuration; initialization will be minimal")

            # Component-specific init could be placed here
            # No heavy work by default to keep base lightweight

            self._initialized = True
            self._shutdown = False
            self._logger.info("opsvi-core initialized successfully")

        except Exception as e:
            self._logger.error(f"Failed to initialize opsvi-core: {e}")
            raise OpsviCoreManagerInitializationError(f"Initialization failed: {e}") from e

    async def shutdown(self) -> None:
        """Shutdown the component."""
        try:
            if self._shutdown:
                return
            self._logger.info("Shutting down opsvi-core")
            self._shutdown = True

            # Cancel and await tasks
            async with self._lock:
                for name, task in list(self._tasks.items()):
                    if not task.done():
                        self._logger.debug(f"Cancelling task: {name}")
                        task.cancel()

            await self._wait_for_tasks(self.config.task_shutdown_timeout)

            self._initialized = False
            self._logger.info("opsvi-core shut down successfully")

        except Exception as e:
            self._logger.error(f"Failed to shutdown opsvi-core: {e}")
            raise OpsviCoreManagerError(f"Shutdown failed: {e}") from e

    async def health_check(self) -> bool:
        """Perform health check."""
        try:
            if not self._initialized:
                return False
            if not self.config.enabled:
                return True

            # Healthy if no task has crashed
            async with self._lock:
                for name, task in self._tasks.items():
                    if task.done() and task.exception() is not None:
                        self._logger.error(
                            "Task '%s' failed with exception: %s", name, task.exception()
                        )
                        return False
            return True
        except Exception as e:
            self._logger.error(f"Health check failed: {e}")
            return False

    # ---- task management ----
    async def register_task(
        self,
        name: str,
        factory: Callable[[], Awaitable[Any]],
        *,
        restart: bool = False,
    ) -> asyncio.Task[Any]:
        """Register and start a background task from a factory.

        The factory is called to produce the coroutine when needed. If restart
        is True, the task will be restarted on exception with backoff.
        """
        if not callable(factory):
            raise OpsviCoreManagerError("factory must be callable")
        async with self._lock:
            if name in self._tasks:
                raise OpsviCoreManagerError(f"Task '{name}' already registered")
            runner = self._task_runner(name, factory, restart)
            task = asyncio.create_task(runner, name=f"opsvi-core:{name}")
            self._tasks[name] = task
            self._task_meta[name] = {"restart": restart, "failures": 0}
            self._logger.debug("Registered task '%s' (restart=%s)", name, restart)
            return task

    async def add_task(self, name: str, coro: Awaitable[Any]) -> asyncio.Task[Any]:
        """Add a one-off background coroutine as a task (no restart)."""
        if asyncio.iscoroutine(coro) is False:
            raise OpsviCoreManagerError("coro must be an awaitable")
        async with self._lock:
            if name in self._tasks:
                raise OpsviCoreManagerError(f"Task '{name}' already registered")
            task = asyncio.create_task(coro, name=f"opsvi-core:{name}")
            self._tasks[name] = task
            self._task_meta[name] = {"restart": False, "failures": 0}
            task.add_done_callback(lambda t, n=name: self._on_task_done(n, t))
            self._logger.debug("Added one-off task '%s'", name)
            return task

    async def cancel_task(self, name: str) -> None:
        """Cancel a registered task by name."""
        async with self._lock:
            task = self._tasks.get(name)
            if task is None:
                return
            if not task.done():
                task.cancel()
        try:
            await asyncio.wait_for(task, timeout=self.config.task_shutdown_timeout)
        except asyncio.CancelledError:
            pass
        except asyncio.TimeoutError:
            self._logger.warning("Timeout while cancelling task '%s'", name)
        finally:
            async with self._lock:
                self._tasks.pop(name, None)
                self._task_meta.pop(name, None)

    async def _wait_for_tasks(self, timeout: float) -> None:
        tasks: list[asyncio.Task[Any]]
        async with self._lock:
            tasks = list(self._tasks.values())
        if not tasks:
            return
        try:
            await asyncio.wait_for(asyncio.gather(*tasks, return_exceptions=True), timeout=timeout)
        except asyncio.TimeoutError:
            self._logger.warning("Timeout while awaiting background tasks to finish")

    def list_tasks(self) -> Dict[str, str]:
        """Get a map of task names to simple statuses."""
        out: Dict[str, str] = {}
        for name, task in list(self._tasks.items()):
            if task.cancelled():
                status = "cancelled"
            elif task.done():
                status = "error" if task.exception() else "finished"
            else:
                status = "running"
            out[name] = status
        return out

    # ---- helpers ----
    async def _task_runner(
        self,
        name: str,
        factory: Callable[[], Awaitable[Any]],
        restart: bool,
    ) -> None:
        failures = 0
        while True:
            try:
                # run task produced by factory
                await factory()
                # normal completion
                self._logger.debug("Task '%s' completed", name)
                break
            except asyncio.CancelledError:
                self._logger.debug("Task '%s' cancelled", name)
                raise
            except Exception as e:
                failures += 1
                async with self._lock:
                    if name in self._task_meta:
                        self._task_meta[name]["failures"] = failures
                self._logger.exception("Task '%s' failed (attempt %d): %s", name, failures, e)
                if not restart or self._shutdown:
                    break
                delay = min(self.config.restart_backoff_min * (2 ** (failures - 1)), self.config.restart_backoff_max)
                try:
                    await asyncio.sleep(delay)
                except asyncio.CancelledError:
                    raise
        # done: remove from registry on exit
        self._on_task_exit(name)

    def _on_task_exit(self, name: str) -> None:
        async def remove() -> None:
            async with self._lock:
                self._tasks.pop(name, None)
                # keep meta to reflect failures; do not remove
        asyncio.create_task(remove())

    def _on_task_done(self, name: str, task: asyncio.Task[Any]) -> None:
        try:
            _ = task.result()
        except asyncio.CancelledError:
            pass
        except Exception as e:
            self._logger.exception("One-off task '%s' raised: %s", name, e)
        finally:
            self._on_task_exit(name)

    # ---- misc ----
    @property
    def initialized(self) -> bool:
        return self._initialized

    @property
    def enabled(self) -> bool:
        return self.config.enabled

    def __repr__(self) -> str:  # pragma: no cover
        state = "initialized" if self._initialized else "not-initialized"
        return f"<OpsviCoreManager state={state} tasks={len(self._tasks)} enabled={self.config.enabled}>"

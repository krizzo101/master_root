"""opsvi-orchestration - Core opsvi-orchestration functionality.

Comprehensive opsvi-orchestration library for the OPSVI ecosystem
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Callable, Awaitable
import asyncio
import logging
from contextlib import AsyncExitStack

from opsvi_foundation import BaseComponent, ComponentError
from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)


class OpsviOrchestrationManagerError(ComponentError):
    """Base exception for opsvi-orchestration errors."""
    pass


class OpsviOrchestrationManagerConfigurationError(OpsviOrchestrationManagerError):
    """Configuration-related errors in opsvi-orchestration."""
    pass


class OpsviOrchestrationManagerInitializationError(OpsviOrchestrationManagerError):
    """Initialization-related errors in opsvi-orchestration."""
    pass


class OpsviOrchestrationManagerConfig(BaseSettings):
    """Configuration for opsvi-orchestration."""

    # Core configuration
    enabled: bool = True
    debug: bool = False
    log_level: str = "INFO"

    # Task execution parameters
    default_concurrency: int = 4
    graceful_shutdown_timeout_s: float = 10.0
    health_check_timeout_s: float = 2.0

    class Config:
        env_prefix = "OPSVI_OPSVI_ORCHESTRATION__"


class OpsviOrchestrationManager(BaseComponent):
    """Base class for opsvi-orchestration components.

    Provides orchestration primitives: async initialization, task submission,
    graceful shutdown, and health checks.
    """

    def __init__(
        self,
        config: Optional[OpsviOrchestrationManagerConfig] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize OpsviOrchestrationManager."""
        cfg = config or OpsviOrchestrationManagerConfig(**kwargs)
        super().__init__("opsvi-orchestration", cfg.dict())
        self.config = cfg
        self._initialized = False
        self._logger = logging.getLogger(f"{__name__}.opsvi-orchestration")

        # Runtime state
        self._exit_stack = AsyncExitStack()
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._task_semaphore = asyncio.Semaphore(self.config.default_concurrency)
        self._tasks: set[asyncio.Task[Any]] = set()
        self._healthy: bool = False

    async def initialize(self) -> None:
        """Initialize the component."""
        try:
            # Configure logging level dynamically
            level = getattr(logging, self.config.log_level.upper(), logging.INFO)
            self._logger.setLevel(level)
            logger.setLevel(level)

            if not self.config.enabled:
                self._logger.info("opsvi-orchestration is disabled by configuration")
                self._initialized = True
                self._healthy = True
                return

            self._logger.info("Initializing opsvi-orchestration")
            self._loop = asyncio.get_running_loop()

            # stack placeholder for future context resources
            await self._exit_stack.__aenter__()

            self._initialized = True
            self._healthy = True
            self._logger.info("opsvi-orchestration initialized successfully")
        except Exception as e:
            self._healthy = False
            self._logger.error(f"Failed to initialize opsvi-orchestration: {e}")
            raise OpsviOrchestrationManagerInitializationError(
                f"Initialization failed: {e}"
            ) from e

    async def shutdown(self) -> None:
        """Shutdown the component."""
        try:
            self._logger.info("Shutting down opsvi-orchestration")
            self._healthy = False

            # Cancel or await all managed tasks with timeout
            await self._drain_tasks(self.config.graceful_shutdown_timeout_s)

            # Close resources
            await self._exit_stack.aclose()

            self._initialized = False
            self._logger.info("opsvi-orchestration shut down successfully")
        except Exception as e:
            self._logger.error(f"Failed to shutdown opsvi-orchestration: {e}")
            raise OpsviOrchestrationManagerError(f"Shutdown failed: {e}") from e

    async def health_check(self) -> bool:
        """Perform health check."""
        try:
            if not self._initialized:
                return False

            async def _probe() -> bool:
                # simple event loop tick and semaphore check
                await asyncio.sleep(0)
                return self._healthy and self._task_semaphore.locked() is not None

            return await asyncio.wait_for(
                _probe(), timeout=self.config.health_check_timeout_s
            )
        except Exception as e:
            self._logger.error(f"Health check failed: {e}")
            return False

    # Orchestration helpers

    def submit(
        self,
        coro_func: Callable[..., Awaitable[Any]],
        /,
        *args: Any,
        name: Optional[str] = None,
        **kwargs: Any,
    ) -> asyncio.Task[Any]:
        """Submit an async callable for managed execution with concurrency limits."""
        if not self._initialized:
            raise OpsviOrchestrationManagerError("Manager not initialized")

        async def _runner() -> Any:
            async with self._task_semaphore:
                return await coro_func(*args, **kwargs)

        task = asyncio.create_task(_runner(), name=name)
        self._tasks.add(task)
        task.add_done_callback(lambda t: self._tasks.discard(t))
        return task

    async def gather(self) -> None:
        """Await all currently submitted tasks."""
        if not self._tasks:
            return
        await asyncio.gather(*list(self._tasks), return_exceptions=True)

    async def _drain_tasks(self, timeout: float) -> None:
        if not self._tasks:
            return
        pending = list(self._tasks)
        try:
            await asyncio.wait_for(asyncio.gather(*pending), timeout=timeout)
        except asyncio.TimeoutError:
            self._logger.warning("Graceful wait timed out; cancelling remaining tasks")
            for t in list(self._tasks):
                t.cancel()
            await asyncio.gather(*list(self._tasks), return_exceptions=True)

    # Convenience utility
    async def run_periodic(
        self,
        interval_s: float,
        worker: Callable[[], Awaitable[None]],
        *,
        stop_event: Optional[asyncio.Event] = None,
        name: Optional[str] = None,
    ) -> asyncio.Task[None]:
        """Run a worker periodically until stop_event is set or on shutdown."""
        if stop_event is None:
            stop_event = asyncio.Event()

        async def _loop() -> None:
            try:
                while self._healthy and not stop_event.is_set():
                    await worker()
                    await asyncio.wait(
                        [asyncio.create_task(stop_event.wait())],
                        timeout=interval_s,
                    )
            except asyncio.CancelledError:
                raise
            except Exception as e:
                self._logger.exception(f"Periodic worker crashed: {e}")
                self._healthy = False

        return self.submit(lambda: _loop(), name=name or "periodic-worker")

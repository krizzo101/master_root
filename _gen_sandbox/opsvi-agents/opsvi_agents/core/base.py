"""opsvi-agents - Core opsvi-agents functionality.

Comprehensive opsvi-agents library for the OPSVI ecosystem
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Awaitable, Callable, Dict, List, Optional

from opsvi_foundation import BaseComponent, ComponentError
from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)


class OpsviAgentsManagerError(ComponentError):
    """Base exception for opsvi-agents errors."""


class OpsviAgentsManagerConfigurationError(OpsviAgentsManagerError):
    """Configuration-related errors in opsvi-agents."""


class OpsviAgentsManagerInitializationError(OpsviAgentsManagerError):
    """Initialization-related errors in opsvi-agents."""


class OpsviAgentsManagerConfig(BaseSettings):
    """Configuration for opsvi-agents."""

    # Core configuration
    enabled: bool = True
    debug: bool = False
    log_level: str = "INFO"

    # Runtime behavior
    graceful_shutdown_timeout: float = 10.0
    periodic_error_backoff: float = 5.0

    class Config:
        env_prefix = "OPSVI_OPSVI_AGENTS__"


def _model_to_dict(model: BaseSettings) -> Dict[str, Any]:
    """Best-effort conversion of pydantic settings to dict (v1/v2)."""
    for attr in ("model_dump", "dict"):
        fn = getattr(model, attr, None)
        if callable(fn):
            try:
                return fn()  # type: ignore[misc]
            except Exception:  # pragma: no cover - fallback
                pass
    return {k: getattr(model, k) for k in model.__fields__}  # type: ignore[attr-defined]


class OpsviAgentsManager(BaseComponent):
    """Base class for opsvi-agents components."""

    def __init__(
        self,
        config: Optional[OpsviAgentsManagerConfig] = None,
        **kwargs: Any,
    ) -> None:
        cfg = config or OpsviAgentsManagerConfig(**kwargs)
        super().__init__("opsvi-agents", _model_to_dict(cfg))
        self.config: OpsviAgentsManagerConfig = cfg
        self._initialized: bool = False
        self._logger = logging.getLogger(f"{__name__}.opsvi-agents")
        self._shutdown_event: asyncio.Event = asyncio.Event()
        self._tasks: set[asyncio.Task[None]] = set()
        self._components: Dict[str, BaseComponent] = {}

    # ---------- lifecycle ----------
    async def initialize(self) -> None:
        """Initialize the component and registered subcomponents."""
        if self._initialized:
            return
        try:
            self._configure_logging()
            self._logger.info("Initializing opsvi-agents")
            if not self.config.enabled:
                self._logger.warning("opsvi-agents is disabled via configuration")
                self._initialized = True
                return

            # Initialize registered subcomponents
            for name, comp in self._components.items():
                await _maybe_await(getattr(comp, "initialize", None))
                self._logger.debug("Initialized subcomponent: %s", name)

            self._shutdown_event.clear()
            self._initialized = True
            self._logger.info("opsvi-agents initialized successfully")
        except Exception as e:  # pragma: no cover - safety
            self._logger.exception("Failed to initialize opsvi-agents: %s", e)
            raise OpsviAgentsManagerInitializationError(f"Initialization failed: {e}") from e

    async def shutdown(self) -> None:
        """Shutdown background tasks and subcomponents."""
        try:
            self._logger.info("Shutting down opsvi-agents")
            self._shutdown_event.set()

            # Wait for background tasks
            await _drain_tasks(self._tasks, self.config.graceful_shutdown_timeout, self._logger)

            # Shutdown subcomponents in reverse registration order
            for name, comp in reversed(list(self._components.items())):
                await _maybe_await(getattr(comp, "shutdown", None))
                self._logger.debug("Shut down subcomponent: %s", name)

            self._initialized = False
            self._logger.info("opsvi-agents shut down successfully")
        except Exception as e:  # pragma: no cover - safety
            self._logger.exception("Failed to shutdown opsvi-agents: %s", e)
            raise OpsviAgentsManagerError(f"Shutdown failed: {e}") from e

    async def health_check(self) -> bool:
        """Return True when initialized and subcomponents are healthy."""
        if not self._initialized:
            return False
        try:
            # Check subcomponents if they expose health_check
            checks: List[Awaitable[bool]] = []
            for comp in self._components.values():
                hc = getattr(comp, "health_check", None)
                if callable(hc):
                    res = hc()
                    if asyncio.iscoroutine(res):
                        checks.append(res)  # type: ignore[arg-type]
                    elif isinstance(res, bool):
                        checks.append(_wrap_bool(res))
            if checks:
                results = await asyncio.gather(*checks, return_exceptions=True)
                if not all(isinstance(r, bool) and r for r in results):
                    return False
            return True
        except Exception as e:  # pragma: no cover - safety
            self._logger.error("Health check failed: %s", e)
            return False

    # ---------- background tasks ----------
    def add_background_task(self, coro: Awaitable[None], *, name: Optional[str] = None) -> asyncio.Task[None]:
        """Add a tracked background task."""
        task = asyncio.create_task(coro, name=name)
        self._tasks.add(task)
        task.add_done_callback(lambda t: _on_task_done(t, self._tasks, self._logger))
        return task

    def schedule_periodic(
        self,
        func: Callable[[], Awaitable[None]] | Callable[["OpsviAgentsManager"], Awaitable[None]],
        interval: float,
        *,
        name: Optional[str] = None,
        initial_delay: float = 0.0,
        jitter: float = 0.0,
    ) -> asyncio.Task[None]:
        """Schedule a periodic async callable until shutdown."""

        async def _runner() -> None:
            if initial_delay > 0:
                try:
                    await asyncio.wait_for(self._shutdown_event.wait(), timeout=initial_delay)
                    return  # shutdown during initial delay
                except asyncio.TimeoutError:
                    pass
            while not self._shutdown_event.is_set():
                try:
                    await (func(self) if _accepts_manager(func) else func())  # type: ignore[arg-type]
                except asyncio.CancelledError:
                    raise
                except Exception as e:
                    self._logger.exception("Periodic task error: %s", e)
                    await _wait_or_shutdown(self._shutdown_event, self.config.periodic_error_backoff)
                # wait interval plus optional jitter
                if not self._shutdown_event.is_set():
                    delay = interval + (jitter * (0.5 - _random_uniform())) if jitter else interval
                    await _wait_or_shutdown(self._shutdown_event, max(0.0, delay))

        return self.add_background_task(_runner(), name=name or "periodic")

    # ---------- components registry ----------
    def register_component(self, name: str, component: BaseComponent) -> None:
        """Register a subcomponent managed by this manager."""
        if name in self._components:
            raise OpsviAgentsManagerConfigurationError(f"Component '{name}' already registered")
        self._components[name] = component

    def get_component(self, name: str) -> Optional[BaseComponent]:
        """Return a previously registered subcomponent by name."""
        return self._components.get(name)

    def list_components(self) -> List[str]:
        """List registered component names."""
        return list(self._components.keys())

    # ---------- helpers ----------
    def _configure_logging(self) -> None:
        level = getattr(logging, str(self.config.log_level).upper(), logging.INFO)
        self._logger.setLevel(level)
        if self.config.debug:
            self._logger.setLevel(logging.DEBUG)

    async def __aenter__(self) -> "OpsviAgentsManager":
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:  # type: ignore[override]
        await self.shutdown()


# --------- internal utilities ---------

def _on_task_done(task: asyncio.Task[None], bucket: set[asyncio.Task[None]], log: logging.Logger) -> None:
    bucket.discard(task)
    try:
        task.result()
    except asyncio.CancelledError:
        pass
    except Exception as e:  # pragma: no cover - background error reporting
        log.error("Background task failed: %s", e, exc_info=True)


async def _drain_tasks(tasks: set[asyncio.Task[None]], timeout: float, log: logging.Logger) -> None:
    if not tasks:
        return
    for t in list(tasks):
        t.cancel()
    try:
        await asyncio.wait_for(asyncio.gather(*tasks, return_exceptions=True), timeout=timeout)
    except asyncio.TimeoutError:  # pragma: no cover - best effort
        log.warning("Timeout waiting for background tasks; cancelling")
        for t in list(tasks):
            if not t.done():
                t.cancel()
    finally:
        tasks.clear()


async def _maybe_await(callable_attr: Any) -> None:
    if callable(callable_attr):
        res = callable_attr()
        if asyncio.iscoroutine(res):
            await res


async def _wait_or_shutdown(ev: asyncio.Event, timeout: float) -> None:
    try:
        await asyncio.wait_for(ev.wait(), timeout=timeout)
    except asyncio.TimeoutError:
        pass


def _wrap_bool(value: bool) -> "asyncio.Future[bool]":
    fut: asyncio.Future[bool] = asyncio.get_running_loop().create_future()
    fut.set_result(value)
    return fut


def _accepts_manager(func: Any) -> bool:
    try:
        from inspect import signature
        sig = signature(func)
        return len(sig.parameters) >= 1
    except Exception:
        return False


def _random_uniform() -> float:
    # Avoid importing random at module import for minimal footprint
    import random

    return random.uniform(0.0, 1.0)

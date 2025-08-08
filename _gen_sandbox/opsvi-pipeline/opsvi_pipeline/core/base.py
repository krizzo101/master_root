"""opsvi-pipeline - Core opsvi-pipeline functionality.

Comprehensive opsvi-pipeline library for the OPSVI ecosystem
"""

from __future__ import annotations

from typing import Any, Awaitable, Callable, Dict, Optional, Union, List
import asyncio
import logging
import time
import uuid

from opsvi_foundation import BaseComponent, ComponentError
from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)


class OpsviPipelineManagerError(ComponentError):
    """Base exception for opsvi-pipeline errors."""
    pass


class OpsviPipelineManagerConfigurationError(OpsviPipelineManagerError):
    """Configuration-related errors in opsvi-pipeline."""
    pass


class OpsviPipelineManagerInitializationError(OpsviPipelineManagerError):
    """Initialization-related errors in opsvi-pipeline."""
    pass


StepCallable = Callable[[Dict[str, Any]], Union[Dict[str, Any], Any, Awaitable[Union[Dict[str, Any], Any]]]]


class OpsviPipelineManagerConfig(BaseSettings):
    """Configuration for opsvi-pipeline."""

    # Core configuration
    enabled: bool = True
    debug: bool = False
    log_level: str = "INFO"

    # Pipeline execution configuration
    default_step_timeout: Optional[float] = None  # seconds; None means no timeout
    shutdown_grace_period: float = 5.0  # seconds

    class Config:
        env_prefix = "OPSVI_OPSVI_PIPELINE__"


class _RunState:
    """Internal structure to track a pipeline run."""

    __slots__ = (
        "run_id",
        "pipeline",
        "status",
        "started_at",
        "ended_at",
        "result",
        "error",
        "task",
        "cancel_event",
    )

    def __init__(self, run_id: str, pipeline: str) -> None:
        self.run_id = run_id
        self.pipeline = pipeline
        self.status: str = "PENDING"
        self.started_at: Optional[float] = None
        self.ended_at: Optional[float] = None
        self.result: Dict[str, Any] = {}
        self.error: Optional[str] = None
        self.task: Optional[asyncio.Task[None]] = None
        self.cancel_event: asyncio.Event = asyncio.Event()


class OpsviPipelineManager(BaseComponent):
    """Base class for opsvi-pipeline components.

    Manages registration and execution of simple async pipelines.
    """

    def __init__(self, config: Optional[OpsviPipelineManagerConfig] = None, **kwargs: Any) -> None:
        super().__init__("opsvi-pipeline", config.dict() if config else {})
        self.config = config or OpsviPipelineManagerConfig(**kwargs)
        self._initialized = False
        self._logger = logging.getLogger(f"{__name__}.opsvi-pipeline")

        self._pipelines: Dict[str, List[StepCallable]] = {}
        self._runs: Dict[str, _RunState] = {}
        self._lock = asyncio.Lock()

    async def initialize(self) -> None:
        """Initialize the component."""
        try:
            self._logger.setLevel(getattr(logging, (self.config.log_level or "INFO").upper(), logging.INFO))
            if self.config.debug:
                self._logger.debug("Debug mode enabled for opsvi-pipeline")

            if not self.config.enabled:
                self._logger.info("opsvi-pipeline is disabled by configuration")

            self._initialized = True
            self._logger.info("opsvi-pipeline initialized successfully")
        except Exception as e:
            self._logger.error(f"Failed to initialize opsvi-pipeline: {e}")
            raise OpsviPipelineManagerInitializationError(f"Initialization failed: {e}") from e

    async def shutdown(self) -> None:
        """Shutdown the component."""
        try:
            self._logger.info("Shutting down opsvi-pipeline")
            if not self._initialized:
                return

            # Signal cancellation to all running tasks
            async with self._lock:
                runs = list(self._runs.values())
            for rs in runs:
                if rs.task and not rs.task.done():
                    rs.cancel_event.set()

            # Await completion with grace period
            deadline = time.monotonic() + max(0.0, self.config.shutdown_grace_period)
            for rs in runs:
                if rs.task is None:
                    continue
                timeout = max(0.0, deadline - time.monotonic())
                try:
                    await asyncio.wait_for(asyncio.shield(rs.task), timeout=timeout)
                except Exception:
                    if not rs.task.done():
                        rs.task.cancel()

            self._initialized = False
            self._logger.info("opsvi-pipeline shut down successfully")
        except Exception as e:
            self._logger.error(f"Failed to shutdown opsvi-pipeline: {e}")
            raise OpsviPipelineManagerError(f"Shutdown failed: {e}") from e

    async def health_check(self) -> bool:
        """Perform health check."""
        try:
            if not self._initialized:
                return False
            # Consider unhealthy if any run has an unhandled exception
            async with self._lock:
                for rs in self._runs.values():
                    if rs.task and rs.task.done():
                        exc = rs.task.exception()
                        if exc is not None and rs.status not in {"FAILED", "CANCELLED"}:
                            return False
            return True
        except Exception as e:
            self._logger.error(f"Health check failed: {e}")
            return False

    # Pipeline registry management
    async def register_pipeline(self, name: str, steps: List[StepCallable]) -> None:
        """Register a pipeline by name with its steps."""
        if not name or not steps:
            raise OpsviPipelineManagerConfigurationError("Pipeline name and steps are required")
        async with self._lock:
            if name in self._pipelines:
                raise OpsviPipelineManagerConfigurationError(f"Pipeline '{name}' already exists")
            self._pipelines[name] = list(steps)
        self._logger.info("Registered pipeline '%s' with %d steps", name, len(steps))

    async def unregister_pipeline(self, name: str) -> None:
        """Remove a previously registered pipeline."""
        async with self._lock:
            self._pipelines.pop(name, None)
        self._logger.info("Unregistered pipeline '%s'", name)

    async def list_pipelines(self) -> List[str]:
        """List available pipeline names."""
        async with self._lock:
            return sorted(self._pipelines.keys())

    # Execution control
    async def run_pipeline(self, name: str, context: Optional[Dict[str, Any]] = None, run_id: Optional[str] = None) -> str:
        """Start executing a pipeline and return a run identifier."""
        if not self._initialized:
            raise OpsviPipelineManagerInitializationError("Manager not initialized")
        async with self._lock:
            steps = self._pipelines.get(name)
            if not steps:
                raise OpsviPipelineManagerConfigurationError(f"Unknown pipeline: {name}")
        rid = run_id or uuid.uuid4().hex
        rs = _RunState(rid, name)
        async with self._lock:
            if rid in self._runs:
                raise OpsviPipelineManagerError(f"Duplicate run_id: {rid}")
            self._runs[rid] = rs
        rs.task = asyncio.create_task(self._execute_pipeline(rs, list(steps), dict(context or {})))
        return rid

    async def await_pipeline(self, run_id: str, timeout: Optional[float] = None) -> Dict[str, Any]:
        """Wait for a pipeline run to complete and return its result context."""
        rs = await self._get_run(run_id)
        if rs.task is None:
            return rs.result
        try:
            await asyncio.wait_for(asyncio.shield(rs.task), timeout=timeout)
        except asyncio.TimeoutError:
            raise
        return rs.result

    async def cancel_pipeline(self, run_id: str) -> None:
        """Request cancellation of a running pipeline."""
        rs = await self._get_run(run_id)
        if rs.status in {"COMPLETED", "FAILED", "CANCELLED"}:
            return
        rs.cancel_event.set()
        if rs.task:
            with contextlib.suppress(Exception):
                await rs.task

    async def get_run_status(self, run_id: str) -> Dict[str, Any]:
        """Return status information for a pipeline run."""
        rs = await self._get_run(run_id)
        return {
            "run_id": rs.run_id,
            "pipeline": rs.pipeline,
            "status": rs.status,
            "started_at": rs.started_at,
            "ended_at": rs.ended_at,
            "error": rs.error,
        }

    async def list_runs(self) -> List[Dict[str, Any]]:
        """List all known runs and their statuses."""
        async with self._lock:
            runs = list(self._runs.values())
        return [
            {
                "run_id": r.run_id,
                "pipeline": r.pipeline,
                "status": r.status,
                "started_at": r.started_at,
                "ended_at": r.ended_at,
            }
            for r in runs
        ]

    async def _execute_pipeline(self, rs: _RunState, steps: List[StepCallable], context: Dict[str, Any]) -> None:
        rs.status = "RUNNING"
        rs.started_at = time.time()
        try:
            for idx, step in enumerate(steps):
                if rs.cancel_event.is_set():
                    rs.status = "CANCELLED"
                    raise asyncio.CancelledError()
                result = await self._invoke_step(step, context, self.config.default_step_timeout)
                if isinstance(result, dict):
                    context.update(result)
                else:
                    context["_last"] = result
                self._logger.debug("Step %d for run %s completed", idx + 1, rs.run_id)
            rs.result = context
            rs.status = "COMPLETED"
        except asyncio.CancelledError:
            rs.error = rs.error or "Cancelled"
            rs.status = "CANCELLED"
        except Exception as e:
            rs.error = f"{type(e).__name__}: {e}"
            rs.status = "FAILED"
            self._logger.exception("Pipeline run %s failed: %s", rs.run_id, e)
        finally:
            rs.ended_at = time.time()

    async def _invoke_step(self, step: StepCallable, context: Dict[str, Any], timeout: Optional[float]) -> Any:
        async def _call() -> Any:
            res = step(context)
            if asyncio.iscoroutine(res):
                return await res  # type: ignore[no-any-return]
            return res

        if timeout is None or timeout <= 0:
            return await _call()
        return await asyncio.wait_for(_call(), timeout=timeout)

    async def _get_run(self, run_id: str) -> _RunState:
        async with self._lock:
            rs = self._runs.get(run_id)
        if not rs:
            raise OpsviPipelineManagerError(f"Unknown run_id: {run_id}")
        return rs


# Keep module export surface small
__all__ = [
    "OpsviPipelineManager",
    "OpsviPipelineManagerConfig",
    "OpsviPipelineManagerError",
    "OpsviPipelineManagerInitializationError",
    "OpsviPipelineManagerConfigurationError",
]

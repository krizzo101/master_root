"""Workflow base for opsvi-orchestration.

Provides an asynchronous Workflow base class with simple state tracking,
step registration, execution, and basic compensation (rollback) support.
"""
from __future__ import annotations

import asyncio
from typing import Any, Awaitable, Callable, Dict, List, Optional, Tuple

StepFunc = Callable[[], Awaitable[Any]]
CompensateFunc = Callable[[], Awaitable[None]]


class WorkflowError(Exception):
    """Raised when a workflow fails during execution."""


class Workflow:
    """A minimal asynchronous workflow base class.

    Usage:
      wf = Workflow(name="example")
      wf.add_step("step1", step_func, compensate_func)
      await wf.run()

    The class records simple in-memory state and will attempt to run
    compensation functions in reverse order if a step raises.
    """

    def __init__(self, name: str = "workflow") -> None:
        self.name = name
        self._steps: List[Tuple[str, StepFunc, Optional[CompensateFunc]]] = []
        self._completed: List[str] = []
        self._state: Dict[str, Any] = {}
        self._lock = asyncio.Lock()

    def add_step(self, key: str, step: StepFunc, compensate: Optional[CompensateFunc] = None) -> None:
        """Register a step with an optional compensation function.

        Steps execute in the order they are added. If a step raises an
        exception, previously completed steps with compensation functions
        will be run in reverse order.
        """
        if any(k == key for k, _, _ in self._steps):
            raise ValueError(f"Step with key '{key}' already exists")
        self._steps.append((key, step, compensate))

    async def run(self, *, timeout: Optional[float] = None) -> Dict[str, Any]:
        """Execute the workflow.

        Returns the internal state mapping. If an exception occurs, compensation
        is attempted and the original exception is re-raised wrapped in
        WorkflowError.
        """
        async with self._lock:
            try:
                coro = self._run_internal()
                if timeout is not None:
                    return await asyncio.wait_for(coro, timeout)
                return await coro
            finally:
                # keep locking simple; lock is released by context manager
                pass

    async def _run_internal(self) -> Dict[str, Any]:
        self._completed.clear()
        self._state.clear()

        for key, step, _ in self._steps:
            try:
                result = await step()
                self._state[key] = result
                self._completed.append(key)
            except Exception as exc:  # pragma: no cover - preserve exception
                await self._compensate_on_failure()
                raise WorkflowError(f"Workflow '{self.name}' failed on step '{key}': {exc}") from exc
        return dict(self._state)

    async def _compensate_on_failure(self) -> None:
        # run compensate functions in reverse order for completed steps
        for key in reversed(self._completed):
            # find the step tuple
            for k, _, compensate in self._steps:
                if k == key and compensate is not None:
                    try:
                        await compensate()
                    except Exception:
                        # log or ignore: we keep compensation best-effort
                        pass
                    break

    def snapshot(self) -> Dict[str, Any]:
        """Return a shallow copy of the current state and completed steps."""
        return {"name": self.name, "state": dict(self._state), "completed": list(self._completed)}

    async def resume_from_snapshot(self, snapshot: Dict[str, Any]) -> None:
        """Load state from a snapshot. This does not re-run steps.

        Intended for simple in-memory persistence scenarios.
        """
        async with self._lock:
            self.name = snapshot.get("name", self.name)
            self._state = dict(snapshot.get("state", {}))
            self._completed = list(snapshot.get("completed", []))


# Example async helper for users: run a workflow and return result or error
async def run_workflow(workflow: Workflow, timeout: Optional[float] = None) -> Tuple[bool, Dict[str, Any]]:
    """Run workflow and return (success, snapshot_or_error).

    If success is True, snapshot_or_error is the workflow snapshot. If False,
    snapshot_or_error contains error details.
    """
    try:
        await workflow.run(timeout=timeout)
        return True, workflow.snapshot()
    except Exception as exc:
        return False, {"error": str(exc)}

"""Coordinator base for opsvi-gateway.

This module provides a lightweight asynchronous Coordinator base class
that builds on OpsviGatewayManager. It offers a structured async
coordinate() entrypoint and helper methods for simple scheduling and
contention resolution strategies. Concrete coordinators should subclass
Coordinator and override _plan() or _execute_plan().
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from opsvi_gateway.core.base import OpsviGatewayManager


@dataclass
class CoordinationTask:
    """Represents a single unit of coordinated work.

    Attributes:
        name: Human readable task name.
        payload: Arbitrary payload passed to the executor.
        priority: Lower numbers are higher priority.
    """

    name: str
    payload: Any = None
    priority: int = 100


class Coordinator(OpsviGatewayManager):
    """Async Coordinator base class.

    Subclasses can override _plan() to return a list of CoordinationTask
    items and _execute_task() to implement execution. The public
    coordinate() method runs the loop once and returns when tasks are
    complete. Simple contention resolution by priority is provided.
    """

    def __init__(self, *, concurrency: int = 4) -> None:
        super().__init__()
        self._concurrency = max(1, int(concurrency))
        self._shutdown = False
        self._lock = asyncio.Lock()

    async def coordinate(self) -> None:
        """Run a single coordination pass: plan tasks and execute them.

        This method is safe to call concurrently; internal locking
        ensures only one coordination pass happens at a time.
        """
        async with self._lock:
            if self._shutdown:
                return
            tasks = await self._plan()
            if not tasks:
                return
            # sort tasks by priority (lower first) and stable by name
            tasks = sorted(tasks, key=lambda t: (t.priority, t.name))
            await self._execute_plan(tasks)

    async def _plan(self) -> List[CoordinationTask]:
        """Produce a list of CoordinationTask to execute.

        Default implementation returns empty list. Subclasses should
        override to provide real work.
        """
        return []

    async def _execute_plan(self, tasks: List[CoordinationTask]) -> None:
        """Execute tasks with simple concurrency and contention resolution.

        Exceptions in task execution are gathered and raised as the first
        encountered exception after all tasks finish.
        """
        if not tasks:
            return

        semaphore = asyncio.Semaphore(self._concurrency)
        results: List[Optional[BaseException]] = [None] * len(tasks)

        async def _run_one(idx: int, task: CoordinationTask) -> None:
            nonlocal results
            async with semaphore:
                try:
                    await self._execute_task(task)
                except BaseException as exc:  # preserve exceptions for raising later
                    results[idx] = exc

        runners = [_run_one(i, t) for i, t in enumerate(tasks)]
        await asyncio.gather(*runners, return_exceptions=False)

        # If any task raised, re-raise the first one
        for exc in results:
            if exc is not None:
                raise exc

    async def _execute_task(self, task: CoordinationTask) -> None:
        """Execute a single CoordinationTask.

        Default implementation is a no-op; subclasses must override to do
        real work. Keep implementations cooperative and cancellable.
        """
        await asyncio.sleep(0)

    async def shutdown(self) -> None:
        """Request shutdown of the coordinator. Subsequent coordinate()
        calls will be no-ops.
        """
        async with self._lock:
            self._shutdown = True

    # Small helper for subclasses
    async def wait_for_condition(self, cond, timeout: Optional[float] = None) -> bool:
        """Wait until cond() returns True or timeout elapses.

        cond can be a synchronous callable or an awaitable returning bool.
        Returns True if condition met, False on timeout.
        """
        async def _poll() -> bool:
            while True:
                value = cond() if callable(cond) else await cond
                if asyncio.iscoroutine(value):
                    value = await value
                if value:
                    return True
                await asyncio.sleep(0.1)

        try:
            return bool(await asyncio.wait_for(_poll(), timeout=timeout))
        except asyncio.TimeoutError:
            return False

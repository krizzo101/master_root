"""Coordinator base for opsvi-pipeline.

Provides an abstract asynchronous coordination entrypoint for pipeline
executions. This module defines a Coordinator base class that other
coordinators can extend to implement scheduling and contention
resolution policies.
"""
from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from typing import Any, Callable, Coroutine, Optional, Set, TypeVar

from opsvi_pipeline.core.base import OpsviPipelineManager

# Generic result type of a task coroutine
TResult = TypeVar("TResult")

# A factory producing an awaitable task coroutine when invoked
TaskFactory = Callable[[], Coroutine[Any, Any, TResult]]


class Coordinator(OpsviPipelineManager, ABC):
    """Abstract base coordinator.

    Subclasses should implement _select_next to decide what to run next and
    may override _on_task_done for custom bookkeeping. The public
    coordinate method runs until stop() is called or an optional timeout
    elapses.
    """

    def __init__(self) -> None:
        super().__init__()
        self._running: bool = False
        self._stop_event: asyncio.Event = asyncio.Event()
        self._lock: asyncio.Lock = asyncio.Lock()
        self._tasks: Set[asyncio.Task[Any]] = set()

    @property
    def running(self) -> bool:
        """Indicates whether the coordinator loop is active."""
        return self._running

    async def coordinate(self, timeout: Optional[float] = None) -> None:
        """Run coordination loop until stopped or timeout.

        Args:
            timeout: optional maximum seconds to run; if None run until stop().
        """
        if self._running:
            return

        self._running = True
        self._stop_event.clear()
        try:
            await asyncio.wait_for(self._run_loop(), timeout=timeout)
        except asyncio.TimeoutError:
            # Timeout is a normal way to stop; ensure loop stops.
            await self.stop()
        finally:
            self._running = False

    async def stop(self) -> None:
        """Request the coordinator to stop and wait for loop to exit."""
        self._stop_event.set()

    async def _run_loop(self) -> None:
        """Internal loop that selects and runs tasks until stopped."""
        while not self._stop_event.is_set():
            try:
                task_fact = await self._select_next()
            except asyncio.CancelledError:
                break

            if task_fact is None:
                # Nothing to run right now; wait briefly to avoid busy spin.
                await asyncio.sleep(0.05)
                continue

            # Run the selected task in background and record completion.
            try:
                coro = task_fact()
            except Exception as exc:  # Guard against faulty factories
                loop = asyncio.get_running_loop()
                loop.call_exception_handler(
                    {"message": "TaskFactory raised before coroutine creation", "exception": exc}
                )
                await asyncio.sleep(0)
                continue

            task: asyncio.Task[Any] = asyncio.create_task(coro)
            self._tasks.add(task)

            def _finalize(t: asyncio.Task[Any]) -> None:
                # Remove from tracking set then delegate to hook
                self._tasks.discard(t)
                try:
                    self._on_task_done(t)
                except Exception as exc:  # Ensure callback errors don't crash loop
                    loop = t.get_loop()
                    loop.call_exception_handler(
                        {"message": "Coordinator _on_task_done raised", "exception": exc}
                    )

            task.add_done_callback(_finalize)

            # Yield control to allow other coroutines to proceed.
            await asyncio.sleep(0)

        # Optional: after stop, just return; tasks may continue or be cancelled by subclasses

    @abstractmethod
    async def _select_next(self) -> Optional[TaskFactory[Any]]:
        """Decide the next task to schedule.

        Should return a callable that when invoked returns a coroutine.
        Return None if there is nothing to run at the moment.
        """

    def _on_task_done(self, task: asyncio.Task[Any]) -> None:
        """Hook called when a scheduled task completes.

        Subclasses may override to inspect results, handle exceptions, or
        implement contention resolution. Default implementation simply
        suppresses unhandled exceptions by logging to the event loop.
        """
        try:
            exc = task.exception()
        except asyncio.CancelledError:
            return
        except Exception as exc:  # pragma: no cover - defensive
            # If retrieving the exception fails, surface that error instead
            loop = task.get_loop()
            loop.call_exception_handler(
                {"message": "Error reading task exception in Coordinator", "exception": exc}
            )
            return

        if exc is not None:
            loop = task.get_loop()
            loop.call_exception_handler({"message": "Task in Coordinator raised", "exception": exc})

"""Scheduler base for opsvi-agents.

Provides a simple asyncio-based priority scheduler with optional
retries and exponential backoff. This is intentionally lightweight and
usable as a base class for more specialized schedulers.
"""
from __future__ import annotations

import asyncio
import dataclasses
import heapq
import itertools
import random
import time
import uuid
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Dict, Optional, Set


@dataclass
class ScheduledTask:
    """Represents a scheduled task.

    coro_factory: a callable that when called returns an awaitable
    priority: lower numbers run first
    retries: max retry attempts (0 means no retries)
    base_backoff: seconds base for exponential backoff
    max_backoff: maximum backoff in seconds
    """

    id: str
    coro_factory: Callable[[], Awaitable[Any]]
    priority: int = 0
    retries: int = 3
    base_backoff: float = 1.0
    max_backoff: float = 60.0

    # internal state
    attempts: int = 0
    next_run: float = 0.0
    last_exception: Optional[BaseException] = None
    _done_event: asyncio.Event = dataclasses.field(default_factory=asyncio.Event)
    _result: Any = None
    _cancelled: bool = False

    def cancel(self) -> None:
        """Mark the task as cancelled. If already running, cancellation
        depends on the underlying coroutine respecting cancellation.
        """
        self._cancelled = True
        self._done_event.set()

    async def wait(self) -> Any:
        """Wait until the task completes (successfully or with final failure).

        Raises the final exception if task failed and exhausted retries.
        Returns the result otherwise.
        """
        await self._done_event.wait()
        if self._cancelled:
            raise asyncio.CancelledError()
        if self.last_exception is not None and self.attempts > self.retries:
            # task has exhausted retries
            raise self.last_exception
        return self._result


class Scheduler:
    """A simple asyncio priority scheduler with retry/backoff support.

    Usage:
      scheduler = Scheduler(max_workers=5)
      task = scheduler.add(lambda: coro(), priority=10)
      await task.wait()

    The scheduler runs a background worker loop once started. Tasks are
    scheduled by calling add(). start() is called automatically on first add.
    """

    def __init__(self, *, max_workers: int = 3) -> None:
        self._max_workers = max_workers
        self._queue: list = []  # heap of (next_run, priority, counter, ScheduledTask)
        self._counter = itertools.count()
        self._new_task = asyncio.Event()
        self._running_tasks: Set[asyncio.Task] = set()
        self._stop = False
        self._bg_task: Optional[asyncio.Task] = None
        self._semaphore = asyncio.Semaphore(max_workers)
        self._tasks_by_id: Dict[str, ScheduledTask] = {}

    def _ensure_started(self) -> None:
        if self._bg_task is None or self._bg_task.done():
            self._stop = False
            self._bg_task = asyncio.create_task(self.schedule())

    def add(
        self,
        coro_factory: Callable[[], Awaitable[Any]],
        *,
        priority: int = 0,
        retries: int = 3,
        base_backoff: float = 1.0,
        max_backoff: float = 60.0,
    ) -> ScheduledTask:
        """Add a coroutine factory to the scheduling queue.

        coro_factory must be callable with zero args and return an awaitable
        (the coroutine to be executed). Returns a ScheduledTask which can be
        awaited with .wait() or cancelled.
        """
        self._ensure_started()
        task_id = str(uuid.uuid4())
        now = time.monotonic()
        st = ScheduledTask(
            id=task_id,
            coro_factory=coro_factory,
            priority=priority,
            retries=retries,
            base_backoff=base_backoff,
            max_backoff=max_backoff,
            attempts=0,
            next_run=now,
        )
        count = next(self._counter)
        heapq.heappush(self._queue, (st.next_run, st.priority, count, st))
        self._tasks_by_id[task_id] = st
        self._new_task.set()
        return st

    async def schedule(self) -> None:
        """Background loop that dispatches due tasks respecting priority
        and max_workers. This method is intended to be run as a background
        task (it is started automatically by add())."""
        try:
            while not self._stop:
                if not self._queue:
                    # wait until a new task arrives or stop is requested
                    self._new_task.clear()
                    await self._new_task.wait()
                    continue

                now = time.monotonic()
                next_run, _, _, st = self._queue[0]
                delay = max(0.0, next_run - now)
                if delay > 0:
                    # wait for the earliest of new task arrival or the next_run
                    self._new_task.clear()
                    try:
                        await asyncio.wait_for(self._new_task.wait(), timeout=delay)
                        continue
                    except asyncio.TimeoutError:
                        pass

                # Pop all due tasks (but respect semaphore when running)
                _, _, _, st = heapq.heappop(self._queue)
                if st._cancelled:
                    # task was cancelled before it ran
                    st._done_event.set()
                    continue

                # Acquire worker slot and run task in background
                await self._semaphore.acquire()

                t = asyncio.create_task(self._run_st_task(st))

                # track running tasks so we can await them on shutdown
                self._running_tasks.add(t)
                t.add_done_callback(self._on_task_done)
        finally:
            # on exit, attempt to cancel running worker tasks gracefully
            for t in list(self._running_tasks):
                t.cancel()
            if self._running_tasks:
                await asyncio.gather(*self._running_tasks, return_exceptions=True)

    def _on_task_done(self, t: asyncio.Task) -> None:
        self._running_tasks.discard(t)
        # release semaphore if not already released by the worker
        if not self._semaphore.locked():
            # if semaphore isn't locked, nothing to release; otherwise release once
            pass

    async def _run_st_task(self, st: ScheduledTask) -> None:
        """Wrap running of a ScheduledTask and handle backoff/retries."""
        try:
            st.attempts += 1
            try:
                coro = st.coro_factory()
                st._result = await coro
                st.last_exception = None
                st._done_event.set()
            except asyncio.CancelledError:
                # propagate cancellation
                st._cancelled = True
                st._done_event.set()
                raise
            except Exception as exc:  # pylint: disable=broad-except
                st.last_exception = exc
                if st.attempts <= st.retries:
                    # compute backoff and reschedule
                    backoff = st.base_backoff * (2 ** (st.attempts - 1))
                    backoff = min(backoff, st.max_backoff)
                    # add small jitter to avoid thundering herd
                    jitter = random.uniform(0, backoff * 0.1)
                    st.next_run = time.monotonic() + backoff + jitter
                    count = next(self._counter)
                    heapq.heappush(self._queue, (st.next_run, st.priority, count, st))
                    self._new_task.set()
                else:
                    # exhausted retries
                    st._done_event.set()
        finally:
            # release the worker slot
            try:
                self._semaphore.release()
            except ValueError:
                # semaphore already released or inconsistent state
                pass

    async def stop(self, *, wait: bool = True) -> None:
        """Stop the scheduler. If wait is True (default) wait for running
        tasks to finish gracefully.
        """
        self._stop = True
        self._new_task.set()
        if self._bg_task is not None:
            # wait for background loop to exit
            try:
                await self._bg_task
            except asyncio.CancelledError:
                pass
        if wait and self._running_tasks:
            await asyncio.gather(*self._running_tasks, return_exceptions=True)

    def cancel(self, task_id: str) -> bool:
        """Cancel a scheduled task by id. Returns True if cancelled."""
        st = self._tasks_by_id.get(task_id)
        if st is None:
            return False
        st.cancel()
        # Note: we don't attempt to remove from heap because it's O(n).
        # It will be skipped when popped.
        self._new_task.set()
        return True

    def stats(self) -> Dict[str, Any]:
        """Return simple statistics about the scheduler."""
        return {
            "queued": len(self._queue),
            "running": len(self._running_tasks),
            "max_workers": self._max_workers,
        }


__all__ = ["Scheduler", "ScheduledTask"]

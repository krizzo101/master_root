"""Scheduler base for opsvi-orchestration.

Provides an abstract asynchronous scheduler that supports task registration,
priority ordering, exponential backoff for retries, and graceful shutdown.
"""
from __future__ import annotations

import asyncio
import heapq
import time
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Dict, Optional, Tuple

TaskCallable = Callable[[], Awaitable[Any]]


@dataclass(order=True)
class _ScheduledItem:
    priority: int
    scheduled_at: float = field(compare=False)
    id: int = field(compare=False)
    coro_factory: TaskCallable = field(compare=False)
    attempt: int = field(default=0, compare=False)
    backoff_base: float = field(default=1.0, compare=False)
    max_backoff: float = field(default=60.0, compare=False)


class Scheduler:
    """Async scheduler supporting priorities and exponential backoff.

    Usage: create a Scheduler, register tasks via schedule_call, then
    run schedule() to process tasks until stopped. Tasks are coroutines
    produced by callables (so they are created on demand). Higher priority
    means earlier execution (larger integer = higher priority).
    """

    def __init__(self) -> None:
        self._queue: list[_ScheduledItem] = []
        self._counter = 0
        self._lock = asyncio.Lock()
        self._stop = asyncio.Event()
        self._active: Dict[int, asyncio.Task] = {}

    async def schedule(self, concurrency: int = 4) -> None:
        """Run the scheduler until stop() is called.

        concurrency: number of worker coroutines processing the queue.
        """
        workers = [asyncio.create_task(self._worker(i)) for i in range(concurrency)]
        try:
            await self._stop.wait()
        finally:
            # signal workers to exit and wait for them
            for w in workers:
                w.cancel()
            await asyncio.gather(*workers, return_exceptions=True)
            # cancel any active tasks spawned
            for t in list(self._active.values()):
                t.cancel()
            await asyncio.gather(*self._active.values(), return_exceptions=True)

    async def _worker(self, worker_id: int) -> None:
        while True:
            item = await self._pop_next()
            if item is None:
                # nothing immediately available; sleep briefly
                await asyncio.sleep(0.1)
                continue
            now = time.time()
            if item.scheduled_at > now:
                # not ready yet, push back and sleep until ready
                await self._push_item(item)
                await asyncio.sleep(min(item.scheduled_at - now, 1.0))
                continue

            # create the coroutine and run it
            try:
                coro = item.coro_factory()
            except Exception as exc:
                # scheduling failed to create coroutine; schedule retry
                await self._handle_failure(item, exc)
                continue

            task = asyncio.create_task(self._run_task(item, coro))
            self._active[item.id] = task
            # detach and continue; completion handled in _run_task

    async def _run_task(self, item: _ScheduledItem, coro: Awaitable[Any]) -> None:
        try:
            await coro
        except asyncio.CancelledError:
            # propagate cancellation
            raise
        except Exception as exc:
            await self._handle_failure(item, exc)
        finally:
            self._active.pop(item.id, None)

    async def _handle_failure(self, item: _ScheduledItem, exc: Exception) -> None:
        # increment attempt count and compute exponential backoff
        item.attempt += 1
        delay = min(item.backoff_base * (2 ** (item.attempt - 1)), item.max_backoff)
        item.scheduled_at = time.time() + delay
        # degrade priority slightly to avoid starving others
        item.priority = max(0, item.priority - 1)
        await self._push_item(item)

    async def _push_item(self, item: _ScheduledItem) -> None:
        async with self._lock:
            # use negative priority because heapq is min-heap; we want max-priority
            heapq.heappush(self._queue, _HeapEntry(-item.priority, item.scheduled_at, item.id, item))

    async def _pop_next(self) -> Optional[_ScheduledItem]:
        async with self._lock:
            while self._queue:
                entry = heapq.heappop(self._queue)
                item = entry.item
                return item
            return None

    async def schedule_call(
        self,
        coro_factory: TaskCallable,
        *,
        priority: int = 0,
        delay: float = 0.0,
        backoff_base: float = 1.0,
        max_backoff: float = 60.0,
    ) -> int:
        """Register a coroutine factory to be scheduled.

        Returns an integer id for the scheduled item.
        """
        now = time.time()
        self._counter += 1
        item = _ScheduledItem(
            priority=priority,
            scheduled_at=now + max(0.0, delay),
            id=self._counter,
            coro_factory=coro_factory,
            attempt=0,
            backoff_base=backoff_base,
            max_backoff=max_backoff,
        )
        await self._push_item(item)
        return item.id

    async def cancel(self, item_id: int) -> bool:
        """Attempt to cancel a scheduled or running task by id.

        Returns True if cancelled or removed; False if not found.
        """
        async with self._lock:
            # remove from queue
            for i, entry in enumerate(self._queue):
                if entry.item.id == item_id:
                    # remove entry
                    self._queue.pop(i)
                    heapq.heapify(self._queue)
                    return True
        # if running, cancel active task
        t = self._active.get(item_id)
        if t is not None:
            t.cancel()
            return True
        return False

    def stop(self) -> None:
        """Signal the scheduler to stop processing after current work."""
        self._stop.set()


@dataclass(order=True)
class _HeapEntry:
    sort_key: Tuple[int, float, int] = field(init=False)
    priority_key: int = field(compare=False)
    scheduled_at: float = field(compare=False)
    id: int = field(compare=False)
    item: _ScheduledItem = field(compare=False)

    def __init__(self, priority_key: int, scheduled_at: float, id: int, item: _ScheduledItem):
        # priority_key: negative of priority so higher priority sorts first
        self.priority_key = priority_key
        self.scheduled_at = scheduled_at
        self.id = id
        self.item = item
        # sort by priority_key, then scheduled_at, then id
        self.sort_key = (priority_key, scheduled_at, id)

    def __lt__(self, other: object) -> bool:  # pragma: no cover - simple comparator
        if not isinstance(other, _HeapEntry):
            return NotImplemented
        return self.sort_key < other.sort_key

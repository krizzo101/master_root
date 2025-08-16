"""Scheduler base for opsvi-gateway.

This module provides an asyncio-based Scheduler that supports prioritized tasks
and basic exponential backoff retry semantics. It is intended to be a general
purpose building block that other components in the package can reuse or
subclass.

Usage (simple):
    sched = Scheduler()
    await sched.start()
    fut = await sched.schedule(some_coroutine_fn, 1, priority=5, retries=2)
    result = await fut  # await the task result
    await sched.stop()

Notes:
- Lower numeric priority values are executed first (0 is higher priority than 5).
- schedule accepts either an awaitable/coroutine object, a coroutine function,
  or a regular callable (sync). Sync callables run in the default executor.
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Optional, Union
import itertools

CallableOrAwaitable = Union[Callable[..., Any], Awaitable[Any]]


@dataclass(order=True)
class _Job:
    # The ordering fields: priority first, then sequence to preserve FIFO for equal priorities
    priority: int
    seq: int = field(compare=True)
    func: CallableOrAwaitable = field(compare=False)
    args: tuple = field(default_factory=tuple, compare=False)
    kwargs: dict = field(default_factory=dict, compare=False)
    future: asyncio.Future = field(default=None, compare=False)
    retries_remaining: int = field(default=0, compare=False)
    retry_backoff: float = field(default=0.5, compare=False)
    backoff_factor: float = field(default=2.0, compare=False)


class Scheduler:
    """Asynchronous prioritized scheduler with simple retry/backoff.

    The scheduler runs a small pool of worker tasks that consume a priority
    queue. Tasks can be scheduled with a numeric priority (lower runs first),
    optional retries, and backoff parameters.

    Methods:
        start(): start background workers
        stop(): stop workers and cancel pending delayed reschedules
        schedule(): add a task to the scheduler and get back a Future
    """

    def __init__(self, worker_count: int = 1) -> None:
        self._loop = asyncio.get_event_loop()
        self._queue: asyncio.PriorityQueue[_Job] = asyncio.PriorityQueue()
        self._workers: list[asyncio.Task] = []
        self._delayed_tasks: set[asyncio.Task] = set()
        self._seq_counter = itertools.count()
        self._worker_count = max(1, worker_count)
        self._stopping = False

    async def start(self) -> None:
        """Start background worker tasks. Safe to call multiple times."""
        if self._workers:
            return
        self._stopping = False
        for _ in range(self._worker_count):
            t = self._loop.create_task(self._worker())
            self._workers.append(t)

    async def stop(self, wait: bool = True) -> None:
        """Signal workers to stop and optionally wait until they finish.

        Any pending scheduled-but-not-yet-executed jobs will have their futures
        cancelled.
        """
        self._stopping = True

        # Cancel delayed reschedules
        for dt in list(self._delayed_tasks):
            dt.cancel()
        self._delayed_tasks.clear()

        # Wake up workers by putting sentinel jobs equal to number of workers
        for _ in self._workers:
            # Use highest priority to ensure immediate pickup
            seq = next(self._seq_counter)
            stopper = _Job(priority=10**9, seq=seq, func=self._noop, args=(), kwargs={}, future=None)
            await self._queue.put(stopper)

        if wait and self._workers:
            await asyncio.gather(*self._workers, return_exceptions=True)

        # Cancel any remaining items in queue
        while not self._queue.empty():
            try:
                job = self._queue.get_nowait()
            except asyncio.QueueEmpty:
                break
            if job.future and not job.future.done():
                job.future.cancel()

        self._workers.clear()

    async def schedule(
        self,
        func: CallableOrAwaitable,
        *args: Any,
        priority: int = 0,
        retries: int = 0,
        retry_backoff: float = 0.5,
        backoff_factor: float = 2.0,
        delay: float = 0.0,
    ) -> asyncio.Future:
        """Schedule a callable/coroutine for execution.

        - func can be a coroutine function, coroutine object, or sync callable.
        - returns an asyncio.Future that can be awaited for the result.
        - priority: lower values are executed earlier.
        - retries: number of times to retry on exception.
        - retry_backoff: initial delay before retrying (seconds).
        - backoff_factor: multiplicative factor for exponential backoff.
        - delay: optional initial delay before placing the job in the queue.
        """
        if self._stopping:
            raise RuntimeError("Scheduler is stopping; cannot schedule new tasks")

        future: asyncio.Future = self._loop.create_future()
        seq = next(self._seq_counter)
        job = _Job(
            priority=priority,
            seq=seq,
            func=func,
            args=args,
            kwargs={},
            future=future,
            retries_remaining=retries,
            retry_backoff=retry_backoff,
            backoff_factor=backoff_factor,
        )

        if delay and delay > 0:
            # Schedule a delayed put into the queue
            t = self._loop.create_task(self._delayed_put(job, delay))
            self._delayed_tasks.add(t)

            def _on_done(_t: asyncio.Task) -> None:
                self._delayed_tasks.discard(_t)
                # Propagate exceptions to job future
                try:
                    _t.result()
                except asyncio.CancelledError:
                    if not future.done():
                        future.cancel()
                except Exception as exc:  # pragma: no cover - defensive
                    if not future.done():
                        future.set_exception(exc)

            t.add_done_callback(_on_done)
        else:
            await self._queue.put(job)

        return future

    async def _delayed_put(self, job: _Job, delay: float) -> None:
        try:
            await asyncio.sleep(delay)
            if not self._stopping:
                await self._queue.put(job)
            else:
                if job.future and not job.future.done():
                    job.future.cancel()
        except asyncio.CancelledError:
            # If cancelled, ensure the future is cancelled as well
            if job.future and not job.future.done():
                job.future.cancel()
            raise

    async def _reschedule_with_backoff(self, job: _Job, delay: float) -> None:
        try:
            await asyncio.sleep(delay)
            if not self._stopping:
                # Decrement priority tie-breaker to keep ordering stable
                job.seq = next(self._seq_counter)
                await self._queue.put(job)
            else:
                if job.future and not job.future.done():
                    job.future.cancel()
        except asyncio.CancelledError:
            if job.future and not job.future.done():
                job.future.cancel()
            raise

    async def _worker(self) -> None:
        while not self._stopping:
            try:
                job = await self._queue.get()
            except asyncio.CancelledError:
                break

            # _noop sentinel handling
            if job.func is self._noop:
                break

            fut = job.future
            if fut is None or fut.done():
                # Nothing to do
                continue

            try:
                result = await self._run_callable(job.func, *job.args, **job.kwargs)
            except Exception as exc:  # Task raised
                if job.retries_remaining > 0 and not self._stopping:
                    job.retries_remaining -= 1
                    # compute next delay
                    next_delay = job.retry_backoff
                    job.retry_backoff = job.retry_backoff * job.backoff_factor
                    t = self._loop.create_task(self._reschedule_with_backoff(job, next_delay))
                    self._delayed_tasks.add(t)

                    def _on_done(_t: asyncio.Task) -> None:
                        self._delayed_tasks.discard(_t)
                        # If the delayed task itself errored, surface that
                        try:
                            _t.result()
                        except asyncio.CancelledError:
                            if not fut.done():
                                fut.cancel()
                        except Exception as e:  # pragma: no cover - defensive
                            if not fut.done():
                                fut.set_exception(e)

                    t.add_done_callback(_on_done)
                else:
                    if not fut.done():
                        fut.set_exception(exc)
            else:
                if not fut.done():
                    fut.set_result(result)

    async def _run_callable(self, func: CallableOrAwaitable, *args: Any, **kwargs: Any) -> Any:
        # If func is an awaitable/coroutine object, await it directly
        if asyncio.iscoroutine(func) or asyncio.isfuture(func):
            return await func

        # If func is a coroutine function, call it to get coroutine then await
        if asyncio.iscoroutinefunction(func):
            coro = func(*args, **kwargs)
            return await coro

        # Otherwise treat as a regular callable and run in default executor
        return await self._loop.run_in_executor(None, lambda: func(*args, **kwargs))

    async def _noop(self) -> None:
        """No-op sentinel used to wake/stop workers."""
        return None


__all__ = ["Scheduler"]

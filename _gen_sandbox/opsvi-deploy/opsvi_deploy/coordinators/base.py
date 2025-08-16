"""Coordinator base for opsvi-deploy.

This module provides a small asyncio-friendly coordinator base class that can
accept coroutine callables (or coroutine objects) and schedule their
execution according to a simple priority queue and a concurrency limit.

Subclasses can override coordinate() to implement different high-level
coordination policies while reusing the submit/shutdown primitives.
"""
from __future__ import annotations

import asyncio
import heapq
import itertools
from typing import Any, Awaitable, Callable, Optional, Set, Tuple

from opsvi_deploy.core.base import OpsviDeployManager

# A coroutine factory (callable returning an awaitable) or an already-created awaitable
TaskFactory = Callable[..., Awaitable[Any]]


class Coordinator(OpsviDeployManager):
    """Asynchronous coordinator that schedules coroutine work.

    Features:
    - Priority scheduling (lower numeric priority value runs first).
    - Concurrency limiting via asyncio.Semaphore.
    - Submit returns an asyncio.Future that will be set with the task result/exception.
    - Simple lifecycle: start/coordinate and shutdown.

    This is a small, well-tested building block intended to be extended by
    real coordinators that implement domain-specific policies.
    """

    def __init__(self, *, concurrency: int = 5) -> None:
        super().__init__()
        if concurrency <= 0:
            raise ValueError("concurrency must be a positive integer")

        self._concurrency = concurrency
        self._semaphore = asyncio.Semaphore(concurrency)

        # Priority queue implemented with heapq. Items are tuples of
        # (priority, seq, (factory_or_coro, args, kwargs, future))
        self._pq: list[Tuple[int, int, Tuple[Any, tuple, dict, asyncio.Future]]] = []
        self._pq_lock = asyncio.Lock()
        self._seq = itertools.count()

        # Running tasks tracked so we can wait for them on shutdown
        self._running: Set[asyncio.Task] = set()

        # Background loop control
        self._loop_task: Optional[asyncio.Task] = None
        self._stop = False
        self._idle_event = asyncio.Event()
        self._idle_event.set()  # initially idle

    async def coordinate(self, *, run_until_empty: bool = False) -> None:
        """Start scheduling loop and wait until stopped.

        By default this method starts the background scheduling loop and
        returns immediately. If run_until_empty=True it will block until the
        queue is empty and all running tasks complete.

        Subclasses may override to implement different behaviors, but should
        call super().coordinate() or reuse the start/shutdown primitives.
        """
        self.start()
        if run_until_empty:
            # Wait until there is nothing left to do
            await self.wait_for_idle()

    def start(self) -> None:
        """Start the background scheduling loop (idempotent)."""
        if self._loop_task is None or self._loop_task.done():
            self._stop = False
            self._loop_task = asyncio.create_task(self._scheduler_loop())

    async def shutdown(self, *, cancel_pending: bool = True, wait_running: bool = True) -> None:
        """Stop accepting new work and tear down background processing.

        If cancel_pending is True, queued tasks that have not started will be
        cancelled (their futures will be set with CancelledError). If
        wait_running is True, waits for currently running tasks to complete.
        """
        self._stop = True

        # Cancel scheduler loop if running
        if self._loop_task is not None:
            self._loop_task.cancel()
            try:
                await self._loop_task
            except asyncio.CancelledError:
                pass
            self._loop_task = None

        # Handle pending queue
        if cancel_pending:
            async with self._pq_lock:
                while self._pq:
                    _, _, (_, _, _, fut) = heapq.heappop(self._pq)
                    if not fut.done():
                        fut.cancel()

        # Optionally wait for running tasks to finish
        if wait_running:
            running = list(self._running)
            if running:
                await asyncio.wait(running)

    def submit(self, factory_or_coro: Any, *args: Any, priority: int = 0, **kwargs: Any) -> asyncio.Future:
        """Submit a coroutine factory or coroutine to be scheduled.

        factory_or_coro may be:
        - A callable that returns an awaitable when called with (*args, **kwargs), or
        - An already-created awaitable (coroutine object). In that case args/kwargs are ignored.

        Returns an asyncio.Future that will hold the result or exception.
        """
        loop = asyncio.get_running_loop()
        fut: asyncio.Future = loop.create_future()

        if self._stop:
            fut.set_exception(RuntimeError("Coordinator is stopped and not accepting new tasks"))
            return fut

        seq = next(self._seq)
        item = (factory_or_coro, args, kwargs, fut)
        # push into priority queue
        async def _put():
            async with self._pq_lock:
                heapq.heappush(self._pq, (priority, seq, item))
                self._idle_event.clear()

        # schedule the push; caller likely expects immediate return
        asyncio.create_task(_put())
        return fut

    async def _scheduler_loop(self) -> None:
        """Background scheduler that pulls from the priority queue and starts tasks."""
        try:
            while not self._stop:
                next_item = None
                async with self._pq_lock:
                    if self._pq:
                        _, _, next_item = heapq.heappop(self._pq)

                if next_item is None:
                    # No work queued. If stop requested, break; otherwise wait a bit for new submissions.
                    if self._stop:
                        break
                    # mark idle and wait for either new work or stop
                    self._idle_event.set()
                    await asyncio.sleep(0.1)
                    continue

                factory_or_coro, args, kwargs, fut = next_item

                # Wait for concurrency slot and start the task
                await self._semaphore.acquire()

                # create task to run the job
                task = asyncio.create_task(self._run_task(factory_or_coro, args, kwargs, fut))
                self._running.add(task)

                # when done remove from running set
                def _on_done(t: asyncio.Task) -> None:
                    self._running.discard(t)

                task.add_done_callback(_on_done)
        except asyncio.CancelledError:
            # Allow cancellation to bubble up for graceful shutdown
            raise
        finally:
            # If we exit scheduler loop, mark idle
            self._idle_event.set()

    async def _run_task(self, factory_or_coro: Any, args: tuple, kwargs: dict, fut: asyncio.Future) -> None:
        """Execute a submitted coroutine and propagate result/exception to fut."""
        try:
            # Obtain an awaitable
            if asyncio.iscoroutine(factory_or_coro):
                coro = factory_or_coro
            elif callable(factory_or_coro):
                coro = factory_or_coro(*args, **kwargs)
            else:
                raise TypeError("Submitted object must be a coroutine or callable returning a coroutine")

            result = await coro
            if not fut.done():
                fut.set_result(result)
        except asyncio.CancelledError:
            # propagate cancellation to the future if not set
            if not fut.done():
                fut.cancel()
            raise
        except Exception as exc:  # pylint: disable=broad-except
            if not fut.done():
                fut.set_exception(exc)
        finally:
            try:
                self._semaphore.release()
            except Exception:
                # ignore release errors
                pass

    async def wait_for_idle(self, timeout: Optional[float] = None) -> None:
        """Wait until there is no queued work and no running tasks.

        If timeout is provided, raises asyncio.TimeoutError when exceeded.
        """
        async def _idle_condition() -> None:
            while True:
                async with self._pq_lock:
                    queued = bool(self._pq)
                running = bool(self._running)
                if not queued and not running:
                    return
                await asyncio.sleep(0.05)

        await asyncio.wait_for(_idle_condition(), timeout=timeout)

    async def __aenter__(self) -> "Coordinator":
        self.start()
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.shutdown()

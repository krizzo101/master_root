"""Scheduler base for opsvi-deploy.

Provides a small, asyncio-based priority scheduler with backoff and retry
semantics. This is intended as a reusable base for higher-level schedulers in
opsvi-deploy.
"""
from __future__ import annotations

import asyncio
import heapq
import logging
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Optional

_logger = logging.getLogger(__name__)

CallableOrAwaitable = Callable[..., Any]


@dataclass(order=True)
class _ScheduledItem:
    # ordering fields for heapq: smaller priority value = higher priority
    priority: int
    counter: int
    func: CallableOrAwaitable = field(compare=False)
    args: tuple = field(compare=False, default_factory=tuple)
    kwargs: dict = field(compare=False, default_factory=dict)
    retries: int = field(compare=False, default=0)
    backoff_base: float = field(compare=False, default=0.5)
    backoff_factor: float = field(compare=False, default=2.0)
    future: asyncio.Future = field(compare=False, default=None)


class Scheduler:
    """Asynchronous priority scheduler with retries and exponential backoff.

    Usage:
      scheduler = Scheduler(concurrency=4)
      scheduler.start()
      fut = scheduler.enqueue(my_coroutine, arg1, priority=10)
      await fut  # result or exception
      await scheduler.stop()

    Notes:
      - Lower numeric priority value is handled before higher values (0 is
        highest priority).
      - Functions passed to enqueue may be sync or async. Sync functions are
        executed in the default executor.
    """

    def __init__(
        self,
        concurrency: int = 1,
        default_retries: int = 3,
        default_backoff_base: float = 0.5,
        default_backoff_factor: float = 2.0,
    ) -> None:
        self._concurrency = max(1, int(concurrency))
        self._default_retries = int(default_retries)
        self._default_backoff_base = float(default_backoff_base)
        self._default_backoff_factor = float(default_backoff_factor)

        self._queue: list[_ScheduledItem] = []
        self._queue_lock = asyncio.Lock()
        self._counter = 0

        self._running = False
        self._workers: list[asyncio.Task] = []
        self._semaphore = asyncio.Semaphore(self._concurrency)

        self._loop = asyncio.get_event_loop()
        self._stopped = asyncio.Event()

    def start(self) -> None:
        """Start worker tasks that will process the queue.

        Safe to call multiple times; subsequent calls have no effect if already
        running.
        """
        if self._running:
            return
        self._running = True
        self._stopped.clear()
        for _ in range(self._concurrency):
            t = self._loop.create_task(self._worker_loop())
            self._workers.append(t)
        _logger.debug("Scheduler started with concurrency=%s", self._concurrency)

    async def stop(self, cancel_pending: bool = False) -> None:
        """Stop the scheduler and wait for workers to finish.

        If cancel_pending is True, pending queued items will be cancelled and
        their futures will be set with CancelledError.
        """
        if not self._running:
            return
        self._running = False

        if cancel_pending:
            async with self._queue_lock:
                while self._queue:
                    item = heapq.heappop(self._queue)
                    if item.future and not item.future.done():
                        item.future.cancel()

        # Wake workers by releasing semaphores in case they're blocked waiting
        # for an item.
        for _ in range(self._concurrency):
            # create dummy tasks to ensure workers break out if waiting on queue
            pass

        # Wait for worker tasks to finish
        await asyncio.gather(*self._workers, return_exceptions=True)
        self._workers.clear()
        self._stopped.set()
        _logger.debug("Scheduler stopped")

    async def _worker_loop(self) -> None:
        """Continuously take items from the priority queue and execute them."""
        try:
            while self._running or self._has_pending():
                item = await self._pop_item()
                if item is None:
                    # No item available; yield control briefly
                    await asyncio.sleep(0.05)
                    continue
                await self._semaphore.acquire()
                # Run the item in a background task so this loop can continue
                # and respect concurrency via semaphore.
                self._loop.create_task(self._run_item(item))
        except asyncio.CancelledError:
            _logger.debug("Worker loop cancelled")
        finally:
            # Ensure semaphore counts are balanced on exit
            try:
                while self._semaphore._value < self._concurrency:  # type: ignore
                    self._semaphore.release()
            except Exception:
                pass

    async def _pop_item(self) -> Optional[_ScheduledItem]:
        async with self._queue_lock:
            if not self._queue:
                return None
            item = heapq.heappop(self._queue)
            return item

    def _has_pending(self) -> bool:
        return bool(self._queue)

    def enqueue(
        self,
        func: CallableOrAwaitable,
        *args: Any,
        priority: int = 0,
        retries: Optional[int] = None,
        backoff_base: Optional[float] = None,
        backoff_factor: Optional[float] = None,
        **kwargs: Any,
    ) -> asyncio.Future:
        """Schedule a callable/coroutine to run.

        Returns an asyncio.Future that will be completed with the function's
        result or exception.
        """
        if retries is None:
            retries = self._default_retries
        if backoff_base is None:
            backoff_base = self._default_backoff_base
        if backoff_factor is None:
            backoff_factor = self._default_backoff_factor

        fut: asyncio.Future = self._loop.create_future()
        async def _ensure_future_done(f: asyncio.Future) -> None:
            # placeholder to keep reference alive; no-op
            return

        item = _ScheduledItem(
            priority=priority,
            counter=self._counter,
            func=func,
            args=args,
            kwargs=kwargs,
            retries=retries,
            backoff_base=backoff_base,
            backoff_factor=backoff_factor,
            future=fut,
        )
        self._counter += 1

        # push into queue
        async def _push() -> None:
            async with self._queue_lock:
                heapq.heappush(self._queue, item)

        # schedule the push on loop
        asyncio.run_coroutine_threadsafe(_push(), self._loop)
        # keep a reference (no-op) so tools don't garbage collect fut prematurely
        asyncio.run_coroutine_threadsafe(_ensure_future_done(fut), self._loop)
        return fut

    async def _run_item(self, item: _ScheduledItem) -> None:
        """Execute a scheduled item with retry/backoff semantics."""
        try:
            attempt = 0
            while True:
                attempt += 1
                try:
                    result = await self._maybe_await(item.func, *item.args, **item.kwargs)
                    if not item.future.done():
                        item.future.set_result(result)
                    return
                except asyncio.CancelledError:
                    # propagate cancellations
                    if not item.future.done():
                        item.future.cancel()
                    raise
                except Exception as exc:  # pylint: disable=broad-except
                    _logger.debug(
                        "Task failed attempt=%s/%s priority=%s exc=%s",
                        attempt,
                        item.retries + 1,
                        item.priority,
                        exc,
                    )
                    if attempt > item.retries:
                        if not item.future.done():
                            item.future.set_exception(exc)
                        return
                    # compute backoff and sleep
                    backoff = item.backoff_base * (item.backoff_factor ** (attempt - 1))
                    # jitter small randomization would be nice but keep deterministic
                    await asyncio.sleep(backoff)
        finally:
            # release semaphore slot for this run
            try:
                self._semaphore.release()
            except Exception:
                pass

    async def _maybe_await(self, func: CallableOrAwaitable, *args: Any, **kwargs: Any) -> Any:
        """Call func; if it returns an awaitable, await it, otherwise run in
        executor.
        """
        try:
            result = func(*args, **kwargs)
        except Exception:
            # If calling the function raises synchronously, re-raise so caller
            # can handle retries.
            raise
        if asyncio.iscoroutine(result) or isinstance(result, Awaitable):
            return await result
        # synchronous result: return directly (could also run in executor if
        # desired; here we run in default executor to avoid blocking event loop)
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: result)


# Minimal test routine when run as script (not executed on import)
if __name__ == "__main__":
    import time

    async def main():
        async def job(n):
            await asyncio.sleep(0.1)
            return f"done {n}"

        s = Scheduler(concurrency=2)
        s.start()
        futs = [s.enqueue(job, i, priority=i % 3) for i in range(6)]
        res = await asyncio.gather(*futs)
        print(res)
        await s.stop()

    asyncio.run(main())

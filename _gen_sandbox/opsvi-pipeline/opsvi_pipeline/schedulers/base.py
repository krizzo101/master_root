"""Scheduler base for opsvi-pipeline.

Provides an abstract asyncio-friendly scheduler with optional priorities and
exponential backoff helpers. Concrete schedulers should override `schedule`
and may use `should_retry` and `next_backoff` utilities.
"""
from __future__ import annotations

import asyncio
import inspect
import time
from typing import Any, Awaitable, Callable, Iterable, List, Optional, TypeVar, Union

__all__ = ["Scheduler"]

T = TypeVar("T")


class Scheduler:
    """Base scheduler coordinating execution and retry/backoff logic.

    This class is lightweight and intended to be extended. It provides:
    - an async `schedule` method to be implemented by subclasses;
    - a simple priority comparator helper;
    - exponential backoff computation and retry decision helper.

    Usage: subclass and override `schedule`. Use `should_retry` and
    `next_backoff` when implementing retries.
    """

    def __init__(self, *, max_retries: int = 3, base_backoff: float = 0.5, max_backoff: float = 30.0):
        """Create a Scheduler.

        Args:
            max_retries: default maximum number of retry attempts (>= 0).
            base_backoff: initial backoff in seconds (> 0).
            max_backoff: maximum backoff in seconds (> 0).
        """
        if max_retries < 0:
            raise ValueError("max_retries must be >= 0")
        if base_backoff <= 0:
            raise ValueError("base_backoff must be > 0")
        if max_backoff <= 0:
            raise ValueError("max_backoff must be > 0")

        self.max_retries = max_retries
        self.base_backoff = base_backoff
        self.max_backoff = max_backoff

    async def schedule(self) -> None:
        """Perform scheduled work (override in subclasses)."""
        await asyncio.sleep(0)

    @staticmethod
    def priority_key(item: Any) -> int:
        """Return integer priority for sorting; lower values are higher priority.

        Accepts either an int or an object with a `priority` attribute that
        can be converted to int. If neither, returns 0.
        """
        if isinstance(item, int):
            return item
        if hasattr(item, "priority"):
            try:
                return int(getattr(item, "priority"))
            except Exception:
                return 0
        return 0

    def next_backoff(self, attempt: int) -> float:
        """Compute exponential backoff (seconds) for the given 1-based attempt.

        Includes up to 10% positive jitter based on local time to reduce
        synchronization effects. The value is capped by `max_backoff`.
        """
        if attempt <= 0:
            return 0.0
        backoff = self.base_backoff * (2 ** (attempt - 1))
        if backoff > self.max_backoff:
            backoff = self.max_backoff
        # small jitter in [0, 0.1*backoff)
        jitter = (time.time() % 1.0) * 0.1 * backoff
        return backoff + jitter

    def should_retry(self, attempt: int, exception: Optional[BaseException] = None) -> bool:
        """Return True to retry given the attempt number and optional exception.

        Default policy: retry while 1-based attempt <= max_retries. Subclasses
        may override to inspect `exception` and customize behavior.
        """
        return attempt <= self.max_retries

    async def run_with_retries(
        self,
        func: Callable[..., Union[Awaitable[T], T]],
        *args: Any,
        **kwargs: Any,
    ) -> T:
        """Run a callable (sync or async) with retries and backoff.

        Raises the last exception if retries are exhausted.
        """
        attempt = 1
        while True:
            try:
                result = func(*args, **kwargs)
                if inspect.isawaitable(result):  # coroutine, Task, or Awaitable
                    return await result  # type: ignore[return-value]
                return result  # type: ignore[return-value]
            except Exception as exc:  # noqa: BLE001 intentional for retry policy
                if not self.should_retry(attempt, exc):
                    raise
                delay = self.next_backoff(attempt)
                await asyncio.sleep(delay)
                attempt += 1

    async def run_many_with_retries(
        self,
        funcs: Iterable[Callable[[], Union[Awaitable[T], T]]],
        *,
        concurrency: int = 5,
        return_exceptions: bool = False,
    ) -> List[Union[T, BaseException]]:
        """Run multiple callables with retries, bounded concurrency, preserving order.

        Args:
            funcs: iterable of zero-arg callables (sync or async) to execute.
            concurrency: maximum concurrent executions (>= 1).
            return_exceptions: if True, collect exceptions instead of raising.
        """
        func_list = list(funcs)
        if not func_list:
            return []

        sem = asyncio.Semaphore(max(1, int(concurrency)))

        async def _run_one(ix: int, f: Callable[[], Union[Awaitable[T], T]]):
            async with sem:
                try:
                    res = await self.run_with_retries(f)
                    return ix, res  # type: ignore[misc]
                except Exception as e:  # noqa: BLE001
                    if return_exceptions:
                        return ix, e
                    raise

        tasks = [asyncio.create_task(_run_one(i, f)) for i, f in enumerate(func_list)]
        try:
            pairs = await asyncio.gather(*tasks)
        except Exception:
            # ensure all tasks are cancelled and awaited
            for t in tasks:
                if not t.done():
                    t.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)
            raise

        results: List[Union[T, BaseException]] = [None] * len(func_list)  # type: ignore[list-item]
        for ix, value in pairs:
            results[ix] = value
        return results

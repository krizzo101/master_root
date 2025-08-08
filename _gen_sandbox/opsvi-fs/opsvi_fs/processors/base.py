"""FS processors base for opsvi-fs.

Defines async-aware base classes and small utilities for file processing
pipelines: FileProcessor, CompositeProcessor to fan-out to multiple
processors, BatchProcessor to accumulate paths and process in batches,
and a simple ErrorHandlingProcessor wrapper to convert exceptions into
callbacks or suppression. All implementations are lightweight and typed.
"""
from __future__ import annotations

import asyncio
from typing import (
    Any,
    Awaitable,
    Callable,
    Iterable,
    List,
    Optional,
    Sequence,
)

__all__ = [
    "FileProcessor",
    "CompositeProcessor",
    "BatchProcessor",
    "ErrorHandlingProcessor",
]


class FileProcessor:
    """Abstract base class for processors that handle file paths.

    Subclasses should implement :meth:`process` to perform I/O or
    CPU-bound work for the given file path. Implementations may be
    asynchronous.
    """

    async def process(self, path: str) -> None:  # pragma: no cover - abstract
        """Process a single file path.

        Args:
            path: filesystem path to process.
        """
        raise NotImplementedError

    async def aclose(self) -> None:
        """Close and release resources. Default is a no-op."""
        return None

    async def __aenter__(self) -> "FileProcessor":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> Optional[bool]:
        await self.aclose()
        return None


class CompositeProcessor(FileProcessor):
    """Fan-out processor that forwards the same path to multiple
    underlying processors concurrently.
    """

    def __init__(self, processors: Sequence[FileProcessor]) -> None:
        self._processors = list(processors)

    async def process(self, path: str) -> None:
        if not self._processors:
            return
        tasks = [asyncio.create_task(p.process(path)) for p in self._processors]
        try:
            results = await asyncio.gather(*tasks, return_exceptions=True)
        finally:
            # Ensure tasks are settled; gather already awaits above.
            pass
        for r in results:
            if isinstance(r, BaseException):
                raise r

    async def aclose(self) -> None:
        # Propagate close to children that implement it
        if not self._processors:
            return
        tasks = [asyncio.create_task(p.aclose()) for p in self._processors]
        await asyncio.gather(*tasks, return_exceptions=True)


class BatchProcessor(FileProcessor):
    """Accumulates paths and calls a batch handler periodically or when
    a capacity is reached.

    The batch handler receives a list of paths and may be async or sync.
    """

    def __init__(
        self,
        handler: Callable[[List[str]], Optional[Awaitable[None]]],
        capacity: int = 100,
        flush_interval: float = 1.0,
    ) -> None:
        self._handler = handler
        self._capacity = max(1, int(capacity))
        # Non-positive interval disables periodic flush
        self._flush_interval = float(flush_interval)
        self._buffer: List[str] = []
        self._lock = asyncio.Lock()
        self._flush_task: Optional[asyncio.Task[Any]] = None
        self._closed = False

    async def _ensure_flush_task(self) -> None:
        if self._flush_interval <= 0:
            return
        if self._flush_task is None or self._flush_task.done():
            self._flush_task = asyncio.create_task(self._periodic_flush())

    async def _periodic_flush(self) -> None:
        try:
            while not self._closed:
                # Use a minimal positive delay to avoid busy-looping
                delay = self._flush_interval if self._flush_interval > 0 else 0.05
                try:
                    await asyncio.sleep(delay)
                except asyncio.CancelledError:
                    # Allow graceful final flush via finally
                    raise
                await self._flush_locked()
        finally:
            # Final flush on exit
            await self._flush_locked()

    async def _flush_locked(self) -> None:
        async with self._lock:
            if not self._buffer:
                return
            batch = list(self._buffer)
            self._buffer.clear()
        result = self._handler(batch)
        if isinstance(result, Awaitable):
            await result

    async def flush(self) -> None:
        """Flush buffered items immediately."""
        await self._flush_locked()

    async def process(self, path: str) -> None:
        if self._closed:
            raise RuntimeError("BatchProcessor is closed")
        async with self._lock:
            self._buffer.append(path)
            size = len(self._buffer)
        if size >= self._capacity:
            await self._flush_locked()
        else:
            await self._ensure_flush_task()

    async def close(self) -> None:
        """Flush remaining items and stop background flush task."""
        self._closed = True
        if self._flush_task:
            self._flush_task.cancel()
            try:
                await self._flush_task
            except asyncio.CancelledError:
                pass
        await self._flush_locked()

    async def aclose(self) -> None:
        await self.close()

    @property
    def pending_count(self) -> int:
        """Number of items currently buffered (approximate)."""
        return len(self._buffer)


class ErrorHandlingProcessor(FileProcessor):
    """Wraps another processor and handles exceptions.

    If on_error is provided it will be called with (path, exception)
    and may be sync or async. If on_error is None exceptions are
    suppressed.
    """

    def __init__(
        self,
        processor: FileProcessor,
        on_error: Optional[Callable[[str, Exception], Optional[Awaitable[None]]]] = None,
    ) -> None:
        self._processor = processor
        self._on_error = on_error

    async def process(self, path: str) -> None:
        try:
            await self._processor.process(path)
        except Exception as exc:  # noqa: BLE001 - deliberately broad to wrap
            if self._on_error is None:
                return
            result = self._on_error(path, exc)
            if isinstance(result, Awaitable):
                await result

    async def aclose(self) -> None:
        await self._processor.aclose()

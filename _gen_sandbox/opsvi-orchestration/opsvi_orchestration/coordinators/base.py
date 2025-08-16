from __future__ import annotations

"""Coordinator base for opsvi-orchestration.

This module provides an abstract Coordinator with a simple async
coordination loop. Subclasses should override `coordinate` to implement
specific coordination policies. A helper `run` method is provided to
manage lifecycle and cancellation.
"""
from typing import Optional
import asyncio

from opsvi_orchestration.core.base import OpsviOrchestrationManager


class Coordinator(OpsviOrchestrationManager):
    """Base coordinator.

    Subclasses can implement `coordinate` to perform periodic coordination
    work. The `run` coroutine will repeatedly call `coordinate` until
    cancelled. A configurable `interval` controls the wait between
    iterations.
    """

    def __init__(self, interval: float = 1.0, *, loop: Optional[asyncio.AbstractEventLoop] = None) -> None:
        """Initialize the coordinator.

        Args:
            interval: seconds to sleep between coordination iterations.
            loop: optional event loop to bind to; if None uses asyncio.get_event_loop().
        """
        super().__init__()
        if interval <= 0:
            raise ValueError("interval must be positive")
        self.interval = interval
        self._loop = loop or asyncio.get_event_loop()
        self._task: Optional[asyncio.Task[None]] = None
        self._stopped = asyncio.Event()

    async def coordinate(self) -> None:
        """Perform one coordination step.

        Default implementation is a no-op. Subclasses should override this
        coroutine to implement actual coordination logic.
        """
        return None

    async def _run_loop(self) -> None:
        """Internal run loop calling `coordinate` periodically until cancelled."""
        try:
            while True:
                # Allow subclasses to implement their own coordination step.
                await self.coordinate()
                # Wait interval, but be responsive to cancellation.
                await asyncio.sleep(self.interval)
        except asyncio.CancelledError:
            # Graceful exit on cancellation
            raise
        finally:
            self._stopped.set()

    def start(self) -> None:
        """Start the coordinator in the background.

        Multiple calls to start are idempotent.
        """
        if self._task is None or self._task.done():
            self._stopped.clear()
            self._task = self._loop.create_task(self._run_loop())

    async def stop(self, timeout: Optional[float] = None) -> None:
        """Stop the coordinator and wait for termination.

        Args:
            timeout: optional seconds to wait for graceful shutdown. If None,
                     wait indefinitely.
        """
        if self._task is None:
            return
        self._task.cancel()
        try:
            await asyncio.wait_for(self._stopped.wait(), timeout=timeout)
        except asyncio.TimeoutError:
            # If forced to timeout, ensure task is cancelled.
            if not self._task.done():
                self._task.cancel()
                # Let the task run to cancellation in background.
        finally:
            self._task = None

    async def run(self) -> None:
        """Convenience coroutine: start and await task completion.

        This will run until cancelled externally.
        """
        self.start()
        assert self._task is not None
        try:
            await self._task
        finally:
            # Ensure stopped event is set
            self._stopped.set()

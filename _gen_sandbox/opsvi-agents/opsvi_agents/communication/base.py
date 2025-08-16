"""Communication base for opsvi-agents.

Provides an asynchronous Communicator that serializes string messages
and delivers them to a pluggable Transport. Supports optional
backpressure via a bounded queue and runs a background worker to
flush messages to the transport.
"""
from __future__ import annotations

import asyncio
import json
import logging
from typing import Awaitable, Callable, Optional, Protocol

logger = logging.getLogger(__name__)


class Transport(Protocol):
    """Protocol for transports used by Communicator.

    Implementors should provide an async send method that accepts raw
    bytes and delivers them to the intended destination.
    """

    async def send(self, data: bytes) -> None:  # pragma: no cover - protocol
        ...


class InMemoryTransport:
    """A simple transport that stores sent messages in memory.

    Useful for testing and examples. Messages are stored as bytes in
    the .sent list.
    """

    def __init__(self) -> None:
        self.sent: list[bytes] = []

    async def send(self, data: bytes) -> None:
        # Simulate async delivery (very small sleep to allow scheduling)
        await asyncio.sleep(0)
        self.sent.append(data)


class Communicator:
    """Asynchronous communicator that serializes string messages and
    forwards them to a Transport.

    If max_queue_size is provided and > 0, messages are enqueued and a
    background worker flushes them to the transport (bounded backpressure).
    Otherwise send() performs an immediate await transport.send(...).
    """

    def __init__(
        self,
        transport: Transport,
        serializer: Optional[Callable[[str], bytes]] = None,
        *,
        max_queue_size: int = 0,
    ) -> None:
        self._transport = transport
        # Default serializer: JSON-encode the string message to a bytes payload.
        self._serializer = serializer or (lambda s: json.dumps(s).encode("utf-8"))
        self._max_queue_size = max_queue_size

        self._queue: Optional[asyncio.Queue] = (
            asyncio.Queue(maxsize=max_queue_size) if max_queue_size > 0 else None
        )
        self._worker_task: Optional[asyncio.Task[None]] = None
        self._stopping = False
        # sentinel object to signal worker shutdown
        self._SENTINEL = object()

    async def send(self, message: str) -> None:
        """Send a message asynchronously.

        If a bounded queue is configured, this will enqueue the message and
        may block (await) when the queue is full, providing backpressure to
        callers. If no queue is configured, the message is serialized and
        sent directly to the transport.
        """
        if self._stopping:
            raise RuntimeError("Communicator is stopping and cannot accept messages")

        data = self._serializer(message)

        if self._queue is None:
            # No queue configured: send directly and await completion.
            await self._safe_send(data)
            return

        # Ensure worker is running
        if self._worker_task is None or self._worker_task.done():
            self._start_worker()

        # Put data into the bounded queue; this will await if the queue
        # is full, providing backpressure.
        await self._queue.put(data)

    async def _safe_send(self, data: bytes) -> None:
        try:
            await self._transport.send(data)
        except Exception:
            logger.exception("Error sending data via transport")

    def _start_worker(self) -> None:
        if self._worker_task is not None and not self._worker_task.done():
            return
        loop = asyncio.get_running_loop()
        self._worker_task = loop.create_task(self._worker())

    async def _worker(self) -> None:
        assert self._queue is not None
        try:
            while True:
                item = await self._queue.get()
                try:
                    if item is self._SENTINEL:
                        # sentinel indicates shutdown
                        return
                    await self._safe_send(item)
                finally:
                    # Mark task done so queue.join() can work correctly.
                    try:
                        self._queue.task_done()
                    except Exception:
                        # task_done may not be necessary in some unforeseen states
                        pass
        except asyncio.CancelledError:
            # Allow cancellation to propagate silently.
            logger.debug("Communicator worker cancelled")
        except Exception:
            logger.exception("Unexpected exception in communicator worker")

    async def close(self) -> None:
        """Stop the communicator and wait for queued messages to be flushed.

        This method returns after the background worker has finished. It
        is safe to call multiple times.
        """
        if self._stopping:
            return
        self._stopping = True

        if self._queue is None:
            # Nothing to flush; nothing to do.
            return

        # Put sentinel into the queue to tell the worker to stop after
        # processing already-enqueued items.
        await self._queue.put(self._SENTINEL)

        # Wait for the worker to finish processing the current queue.
        if self._worker_task is not None:
            try:
                await self._worker_task
            except Exception:
                logger.exception("Error while waiting for communicator worker to finish")

    async def __aenter__(self) -> "Communicator":
        # No-op: worker will lazily start on first send.
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.close()


# Small example transport to demonstrate non-network behavior.
class PrintTransport:
    """Transport that prints and yields briefly to the event loop."""

    async def send(self, data: bytes) -> None:
        # Keep this non-blocking; allow immediate scheduling of other tasks.
        print(data.decode("utf-8", errors="replace"))
        await asyncio.sleep(0)

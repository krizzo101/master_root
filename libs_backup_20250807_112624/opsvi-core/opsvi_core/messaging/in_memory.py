"""
In-memory message broker implementation.

Provides a simple in-memory message broker for testing and single-node deployments.
"""

from __future__ import annotations

import asyncio
import contextlib
from collections import defaultdict
from collections.abc import Callable
from typing import Any

from opsvi_foundation import get_logger, sanitize_input

from .base import Message, MessageBroker, MessagingError

logger = get_logger(__name__)


class InMemoryBroker(MessageBroker):
    """Simple FIFO in-memory broker with pub/sub semantics."""

    def __init__(self, *, encryption_key: bytes | None = None, max_queue: int = 1000):
        super().__init__(encryption_key=encryption_key)
        self._queues: dict[str, asyncio.Queue[Message]] = defaultdict(
            lambda: asyncio.Queue(maxsize=max_queue)
        )
        self._tasks: list[asyncio.Task[Any]] = []

    async def _start(self) -> None:
        logger.info("InMemoryBroker started")

    async def _stop(self) -> None:
        logger.info(
            "InMemoryBroker stopping – cancelling %d consumer tasks", len(self._tasks)
        )
        for task in self._tasks:
            task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await task
        self._tasks.clear()

    async def publish(self, message: Message) -> None:
        """Publish a message to a topic."""
        self._encrypt_if_needed(message)
        topic = sanitize_input(message.route.topic)
        try:
            await self._queues[topic].put(message)
            logger.debug(
                "Published message %s to topic '%s'", message.message_id, topic
            )
        except asyncio.QueueFull as exc:
            raise MessagingError("Queue is full") from exc

    async def subscribe(
        self,
        topic: str,
        *,
        callback: Callable[[Message], Any],
        group: str | None = None,  # noqa: ARG002 – not used in in-mem broker
    ) -> None:
        """Subscribe to messages on a topic."""
        queue = self._queues[sanitize_input(topic)]
        logger.info("Subscriber registered on topic '%s'", topic)

        async def _consumer() -> None:
            while True:
                msg = await queue.get()
                self._decrypt_if_needed(msg)
                try:
                    await callback(msg)
                except Exception:  # noqa: BLE001
                    logger.exception("Callback failed – will retry after delay")
                    await asyncio.sleep(self.RETRY_DELAY)
                    await queue.put(msg)  # re-queue for retry

        task = asyncio.create_task(_consumer(), name=f"consumer:{topic}")
        self._tasks.append(task)

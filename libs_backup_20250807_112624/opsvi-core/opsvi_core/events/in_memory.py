"""
In-memory event bus implementation.

Provides a simple in-memory event bus for testing and single-node deployments.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable
from typing import Any

from opsvi_foundation import get_logger

from ..messaging import InMemoryBroker, Message, MessageRoute
from ..messaging.base import QoSLevel
from .base import Event, EventBus

logger = get_logger(__name__)


class InMemoryEventBus(EventBus):
    """
    Process-local EventBus leveraging the in-memory broker.
    """

    def __init__(self, broker: InMemoryBroker | None = None) -> None:
        super().__init__()
        self._broker = broker or InMemoryBroker()
        self._handlers: dict[str, list[Callable[[Event], Any]]] = defaultdict(list)

    async def _start(self) -> None:
        await self._broker.start()

    async def _stop(self) -> None:
        await self._broker.stop()

    async def publish(self, event: Event) -> None:
        """Publish an event to all subscribers."""
        topic = f"event.{event.name}"
        msg = Message(
            payload=event.__dict__,
            route=MessageRoute(source="event_bus", destination=None, topic=topic),
            qos=QoSLevel.AT_LEAST_ONCE,
        )
        await self._broker.publish(msg)
        self._store_event(event)

    async def subscribe(self, event_name: str, handler: Callable[[Event], Any]) -> None:
        """Subscribe to events of a specific type."""

        async def _callback(msg: Message) -> None:
            data = msg.payload
            event = Event(
                event_id=data["event_id"],
                name=data["name"],
                payload=data["payload"],
                metadata=data["metadata"],
                timestamp=data["timestamp"],
                source=data["source"],
                correlation_id=data.get("correlation_id"),
                version=data.get("version", "1.0"),
            )
            try:
                await handler(event)
            except Exception:  # noqa: BLE001
                logger.exception("Event handler failed")

        topic = f"event.{event_name}"
        await self._broker.subscribe(topic, callback=_callback)
        logger.info("Event handler registered for '%s'", event_name)

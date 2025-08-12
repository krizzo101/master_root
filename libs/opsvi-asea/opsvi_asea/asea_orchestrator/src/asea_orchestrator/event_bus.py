from typing import Callable, List, Dict, Any
import asyncio

from .plugins.types import Event

Handler = Callable[[Event], None]


class EventBus:
    """
    A simple in-memory event bus for asynchronous communication.
    """

    def __init__(self):
        self._handlers: Dict[str, List[Handler]] = {}

    def subscribe(self, event_type: str, handler: Handler):
        """
        Subscribes a handler to a specific event type.
        """
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)
        print(f"Handler subscribed to event type: {event_type}")

    async def publish(self, event_type: str, payload: Dict[str, Any]):
        """
        Publishes an event to all subscribed handlers.
        """
        print(f"Publishing event: {event_type}")
        event = Event(event_type=event_type, payload=payload)
        if event_type in self._handlers:
            for handler in self._handlers[event_type]:
                if asyncio.iscoroutinefunction(handler):
                    # Schedule coroutine handlers to run concurrently
                    asyncio.create_task(handler(event))
                else:
                    # Execute regular function handlers directly
                    handler(event)

"""
Base event system for OPSVI Core.

Provides event bus interface, event types, and event handling mechanisms.
"""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from opsvi_foundation import BaseComponent, ComponentError, get_logger
from pydantic import BaseModel

logger = get_logger(__name__)


class EventError(ComponentError):
    """Raised when event operations fail."""

    pass


@dataclass
class Event:
    """Event structure for system-wide event distribution."""

    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = field(default="")
    payload: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    source: str = field(default="unknown")
    correlation_id: Optional[str] = None
    version: str = field(default="1.0")


class EventHandler(BaseModel):
    """Event handler configuration."""

    name: str
    handler: Callable[[Event], Any]
    event_types: List[str] = []
    priority: int = 0
    enabled: bool = True


class EventBus(BaseComponent, ABC):
    """Abstract event bus interface.

    Provides event publishing and subscription capabilities with support for:
    - Event filtering and routing
    - Handler priority and ordering
    - Event persistence and replay
    - Error handling and recovery
    """

    def __init__(self):
        super().__init__()
        self._handlers: Dict[str, List[EventHandler]] = {}
        self._event_history: List[Event] = []

    @abstractmethod
    async def publish(self, event: Event) -> None:
        """Publish an event to all subscribers."""
        pass

    @abstractmethod
    async def subscribe(self, event_name: str, handler: Callable[[Event], Any]) -> None:
        """Subscribe to events of a specific type."""
        pass

    async def _handle_event(self, event: Event) -> None:
        """Handle an event by calling all registered handlers."""
        handlers = self._handlers.get(event.name, [])
        if not handlers:
            logger.debug("No handlers registered for event: %s", event.name)
            return

        # Sort handlers by priority (higher priority first)
        sorted_handlers = sorted(handlers, key=lambda h: h.priority, reverse=True)

        for handler_config in sorted_handlers:
            if not handler_config.enabled:
                continue

            try:
                await handler_config.handler(event)
                logger.debug(
                    "Event %s handled by %s", event.event_id, handler_config.name
                )
            except Exception as e:
                logger.error(
                    "Handler %s failed for event %s: %s",
                    handler_config.name,
                    event.event_id,
                    str(e),
                )
                # Continue processing other handlers
                continue

    def _store_event(self, event: Event) -> None:
        """Store event in history for replay capabilities."""
        self._event_history.append(event)
        # Keep only last 1000 events to prevent memory issues
        if len(self._event_history) > 1000:
            self._event_history = self._event_history[-1000:]


class EventFilter(BaseComponent):
    """Event filtering and routing."""

    def __init__(self):
        super().__init__()
        self._filters: Dict[str, Callable[[Event], bool]] = {}

    def add_filter(self, name: str, filter_func: Callable[[Event], bool]) -> None:
        """Add an event filter."""
        self._filters[name] = filter_func
        logger.info("Added event filter: %s", name)

    def remove_filter(self, name: str) -> None:
        """Remove an event filter."""
        self._filters.pop(name, None)
        logger.info("Removed event filter: %s", name)

    def should_process(self, event: Event) -> bool:
        """Check if an event should be processed based on filters."""
        for filter_name, filter_func in self._filters.items():
            try:
                if not filter_func(event):
                    logger.debug("Event %s filtered out by %s", event.event_id, filter_name)
                    return False
            except Exception as e:
                logger.error("Filter %s failed: %s", filter_name, str(e))
                # Default to allowing the event if filter fails
                continue
        return True


class EventReplay(BaseComponent):
    """Event replay and history management."""

    def __init__(self, event_bus: EventBus):
        super().__init__()
        self.event_bus = event_bus
        self._replay_buffer: List[Event] = []

    async def replay_events(
        self, event_types: Optional[List[str]] = None, since: Optional[datetime] = None
    ) -> None:
        """Replay events from history."""
        events = self.event_bus._event_history

        if event_types:
            events = [e for e in events if e.name in event_types]

        if since:
            events = [e for e in events if e.timestamp >= since]

        logger.info("Replaying %d events", len(events))

        for event in events:
            try:
                await self.event_bus.publish(event)
            except Exception as e:
                logger.error("Failed to replay event %s: %s", event.event_id, str(e))

    def store_for_replay(self, event: Event) -> None:
        """Store event for future replay."""
        self._replay_buffer.append(event)
        # Keep only last 100 events in replay buffer
        if len(self._replay_buffer) > 100:
            self._replay_buffer = self._replay_buffer[-100:]

    async def replay_buffer(self) -> None:
        """Replay events from the replay buffer."""
        logger.info("Replaying %d events from buffer", len(self._replay_buffer))

        for event in self._replay_buffer:
            try:
                await self.event_bus.publish(event)
            except Exception as e:
                logger.error("Failed to replay buffered event %s: %s", event.event_id, str(e))

        self._replay_buffer.clear()

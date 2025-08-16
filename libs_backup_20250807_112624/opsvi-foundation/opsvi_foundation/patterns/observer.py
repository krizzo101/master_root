"""
Observer pattern implementation for OPSVI Foundation.

Provides a robust event-driven communication system for decoupled components.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class EventPriority(Enum):
    """Event priority levels for observer pattern."""

    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class Event:
    """Event data structure for observer pattern."""

    event_type: str
    data: Any
    timestamp: datetime = field(default_factory=datetime.now)
    priority: EventPriority = EventPriority.NORMAL
    source: str | None = None
    correlation_id: str | None = None


class Observer(ABC):
    """Abstract base class for observers."""

    @abstractmethod
    async def on_event(self, event: Event) -> None:
        """Handle an event."""


class Subject(ABC):
    """Abstract base class for subjects that can be observed."""

    def __init__(self) -> None:
        self._observers: dict[str, set[Observer]] = {}
        self._async_observers: dict[str, set[Callable]] = {}

    def attach(self, event_type: str, observer: Observer) -> None:
        """Attach an observer to an event type."""
        if event_type not in self._observers:
            self._observers[event_type] = set()
        self._observers[event_type].add(observer)
        logger.debug(f"Attached observer {observer} to event type {event_type}")

    def detach(self, event_type: str, observer: Observer) -> None:
        """Detach an observer from an event type."""
        if event_type in self._observers:
            self._observers[event_type].discard(observer)
            if not self._observers[event_type]:
                del self._observers[event_type]
            logger.debug(f"Detached observer {observer} from event type {event_type}")

    async def notify(self, event: Event) -> None:
        """Notify all observers of an event."""
        observers = self._observers.get(event.event_type, set())
        async_observers = self._async_observers.get(event.event_type, set())

        # Notify synchronous observers
        for observer in observers:
            try:
                await observer.on_event(event)
            except Exception as e:
                logger.error(f"Error in observer {observer}: {e}")

        # Notify async observers
        tasks = []
        for async_observer in async_observers:
            try:
                task = asyncio.create_task(async_observer(event))
                tasks.append(task)
            except Exception as e:
                logger.error(f"Error creating async observer task: {e}")

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)


class EventBus:
    """Centralized event bus for application-wide event management."""

    def __init__(self) -> None:
        self._subjects: dict[str, Subject] = {}
        self._global_observers: dict[str, set[Observer]] = {}
        self._event_history: list[Event] = []
        self._max_history: int = 1000

    def register_subject(self, name: str, subject: Subject) -> None:
        """Register a subject with the event bus."""
        self._subjects[name] = subject
        logger.info(f"Registered subject: {name}")

    def unregister_subject(self, name: str) -> None:
        """Unregister a subject from the event bus."""
        if name in self._subjects:
            del self._subjects[name]
            logger.info(f"Unregistered subject: {name}")

    def subscribe(self, event_type: str, observer: Observer) -> None:
        """Subscribe to events globally."""
        if event_type not in self._global_observers:
            self._global_observers[event_type] = set()
        self._global_observers[event_type].add(observer)
        logger.debug(f"Global subscription: {observer} -> {event_type}")

    def unsubscribe(self, event_type: str, observer: Observer) -> None:
        """Unsubscribe from global events."""
        if event_type in self._global_observers:
            self._global_observers[event_type].discard(observer)
            if not self._global_observers[event_type]:
                del self._global_observers[event_type]
            logger.debug(f"Global unsubscription: {observer} -> {event_type}")

    async def publish(self, event: Event) -> None:
        """Publish an event to all relevant observers."""
        # Store in history
        self._event_history.append(event)
        if len(self._event_history) > self._max_history:
            self._event_history.pop(0)

        # Notify global observers
        global_observers = self._global_observers.get(event.event_type, set())
        for observer in global_observers:
            try:
                await observer.on_event(event)
            except Exception as e:
                logger.error(f"Error in global observer {observer}: {e}")

        # Notify subject-specific observers
        for subject in self._subjects.values():
            await subject.notify(event)

        logger.debug(f"Published event: {event.event_type}")

    def get_event_history(self, event_type: str | None = None) -> list[Event]:
        """Get event history, optionally filtered by type."""
        if event_type is None:
            return self._event_history.copy()
        return [
            event for event in self._event_history if event.event_type == event_type
        ]

    def clear_history(self) -> None:
        """Clear event history."""
        self._event_history.clear()
        logger.info("Event history cleared")


# Global event bus instance
event_bus = EventBus()

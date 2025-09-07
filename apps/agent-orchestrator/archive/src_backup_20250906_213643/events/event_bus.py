"""
Event Bus Implementation

Core publish/subscribe event system for agent coordination.
Provides reliable, fast event delivery with ordering guarantees.
"""

import asyncio
import json
import logging
import time
from collections import defaultdict
from dataclasses import asdict
from typing import Any, Callable, Dict, List, Optional, Set

from .event_types import BaseEvent, EventType, Priority

logger = logging.getLogger(__name__)


class EventSubscription:
    """Represents a subscription to events"""

    def __init__(
        self,
        callback: Callable[[BaseEvent], None],
        event_types: Optional[List[EventType]] = None,
        agent_filter: Optional[str] = None,
        priority_filter: Optional[Priority] = None,
    ):
        self.callback = callback
        self.event_types = set(event_types) if event_types else None
        self.agent_filter = agent_filter
        self.priority_filter = priority_filter
        self.subscription_id = f"sub_{int(time.time() * 1000000)}"
        self.active = True

    def matches_event(self, event: BaseEvent) -> bool:
        """Check if this subscription should receive the event"""
        if not self.active:
            return False

        # Filter by event type
        if self.event_types and event.event_type not in self.event_types:
            return False

        # Filter by agent
        if self.agent_filter and event.source_agent_id != self.agent_filter:
            return False

        # Filter by priority (receive this priority and higher)
        if self.priority_filter and event.priority.value < self.priority_filter.value:
            return False

        return True


class EventBus:
    """High-performance event bus for agent coordination"""

    def __init__(self, max_event_history: int = 10000):
        self.subscriptions: List[EventSubscription] = []
        self.event_history: List[BaseEvent] = []
        self.max_event_history = max_event_history
        self.event_count = 0
        self.lock = asyncio.Lock()

        # Performance metrics
        self.metrics = {
            "events_published": 0,
            "events_delivered": 0,
            "delivery_errors": 0,
            "avg_delivery_time_ms": 0.0,
        }

        logger.info("EventBus initialized")

    async def publish(self, event: BaseEvent) -> None:
        """Publish an event to all matching subscribers"""
        start_time = time.time()

        async with self.lock:
            # Add to history
            self.event_history.append(event)
            if len(self.event_history) > self.max_event_history:
                self.event_history = self.event_history[-self.max_event_history :]

            self.event_count += 1
            self.metrics["events_published"] += 1

            logger.debug(
                f"Publishing event {event.event_id} of type "
                f"{event.event_type} from {event.source_agent_id}"
            )

        # Deliver to subscribers (outside of lock for performance)
        delivery_count = await self._deliver_event(event)

        # Update metrics
        delivery_time_ms = (time.time() - start_time) * 1000
        async with self.lock:
            self.metrics["events_delivered"] += delivery_count

            # Update average delivery time
            current_avg = self.metrics["avg_delivery_time_ms"]
            total_events = self.metrics["events_published"]
            self.metrics["avg_delivery_time_ms"] = (
                current_avg * (total_events - 1) + delivery_time_ms
            ) / total_events

        logger.debug(
            f"Event {event.event_id} delivered to {delivery_count} "
            f"subscribers in {delivery_time_ms:.2f}ms"
        )

    async def _deliver_event(self, event: BaseEvent) -> int:
        """Deliver event to all matching subscribers"""
        delivery_count = 0
        delivery_tasks = []

        # Create delivery tasks for all matching subscriptions
        for subscription in self.subscriptions:
            if subscription.matches_event(event):
                task = asyncio.create_task(self._safe_deliver(subscription, event))
                delivery_tasks.append(task)
                delivery_count += 1

        # Wait for all deliveries to complete
        if delivery_tasks:
            await asyncio.gather(*delivery_tasks, return_exceptions=True)

        return delivery_count

    async def _safe_deliver(
        self, subscription: EventSubscription, event: BaseEvent
    ) -> None:
        """Safely deliver event to a subscription with error handling"""
        try:
            # For async callbacks
            if asyncio.iscoroutinefunction(subscription.callback):
                await subscription.callback(event)
            else:
                # For sync callbacks, run in thread pool to avoid blocking
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, subscription.callback, event)

        except Exception as e:
            logger.error(
                f"Error delivering event {event.event_id} to subscription "
                f"{subscription.subscription_id}: {e}"
            )
            async with self.lock:
                self.metrics["delivery_errors"] += 1

    def subscribe(
        self,
        callback: Callable[[BaseEvent], None],
        event_types: Optional[List[EventType]] = None,
        agent_filter: Optional[str] = None,
        priority_filter: Optional[Priority] = None,
    ) -> str:
        """Subscribe to events"""
        subscription = EventSubscription(
            callback=callback,
            event_types=event_types,
            agent_filter=agent_filter,
            priority_filter=priority_filter,
        )

        self.subscriptions.append(subscription)

        logger.info(
            f"New subscription {subscription.subscription_id} added "
            f"for events: {event_types}, agent: {agent_filter}, "
            f"priority: {priority_filter}"
        )

        return subscription.subscription_id

    def unsubscribe(self, subscription_id: str) -> bool:
        """Unsubscribe from events"""
        for subscription in self.subscriptions:
            if subscription.subscription_id == subscription_id:
                subscription.active = False
                self.subscriptions.remove(subscription)
                logger.info(f"Unsubscribed {subscription_id}")
                return True
        return False

    async def get_event_history(
        self,
        limit: Optional[int] = None,
        event_types: Optional[List[EventType]] = None,
        agent_filter: Optional[str] = None,
        since_timestamp: Optional[float] = None,
    ) -> List[BaseEvent]:
        """Get filtered event history"""
        async with self.lock:
            events = self.event_history[:]

        # Apply filters
        filtered_events = []
        for event in events:
            # Time filter
            if since_timestamp and event.timestamp < since_timestamp:
                continue

            # Event type filter
            if event_types and event.event_type not in event_types:
                continue

            # Agent filter
            if agent_filter and event.source_agent_id != agent_filter:
                continue

            filtered_events.append(event)

        # Sort by timestamp (newest first) and apply limit
        filtered_events.sort(key=lambda e: e.timestamp, reverse=True)
        if limit:
            filtered_events = filtered_events[:limit]

        return filtered_events

    async def get_metrics(self) -> Dict[str, Any]:
        """Get event bus performance metrics"""
        async with self.lock:
            return {
                **self.metrics,
                "active_subscriptions": len(self.subscriptions),
                "event_history_size": len(self.event_history),
                "total_events": self.event_count,
            }

    async def clear_history(self) -> None:
        """Clear event history"""
        async with self.lock:
            self.event_history.clear()
            logger.info("Event history cleared")

    def get_subscriber_count(self) -> int:
        """Get number of active subscriptions"""
        return len([s for s in self.subscriptions if s.active])


# Global event bus instance
_global_event_bus: Optional[EventBus] = None


def get_global_event_bus() -> EventBus:
    """Get or create the global event bus instance"""
    global _global_event_bus
    if _global_event_bus is None:
        _global_event_bus = EventBus()
    return _global_event_bus


def set_global_event_bus(event_bus: EventBus) -> None:
    """Set the global event bus instance"""
    global _global_event_bus
    _global_event_bus = event_bus


# Convenience functions for common operations


async def publish_event(event: BaseEvent, event_bus: Optional[EventBus] = None) -> None:
    """Publish an event using the global or provided event bus"""
    bus = event_bus or get_global_event_bus()
    await bus.publish(event)


def subscribe_to_events(
    callback: Callable[[BaseEvent], None],
    event_types: Optional[List[EventType]] = None,
    agent_filter: Optional[str] = None,
    priority_filter: Optional[Priority] = None,
    event_bus: Optional[EventBus] = None,
) -> str:
    """Subscribe to events using the global or provided event bus"""
    bus = event_bus or get_global_event_bus()
    return bus.subscribe(
        callback=callback,
        event_types=event_types,
        agent_filter=agent_filter,
        priority_filter=priority_filter,
    )

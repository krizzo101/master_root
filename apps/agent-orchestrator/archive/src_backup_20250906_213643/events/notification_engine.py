"""
Notification Engine

Smart notification system that routes relevant events to interested agents
based on context, preferences, and relevance scoring.
"""

import asyncio
import logging
import time
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

from .event_bus import EventBus, get_global_event_bus
from .event_types import BaseEvent, EventType, Priority

logger = logging.getLogger(__name__)


class NotificationMethod(Enum):
    """Notification delivery methods"""

    DIRECT_MESSAGE = "direct_message"
    BROADCAST = "broadcast"
    WEBHOOK = "webhook"
    EMAIL = "email"
    PUSH = "push"


@dataclass
class NotificationRule:
    """Rule for filtering and routing notifications"""

    rule_id: str
    agent_id: str
    event_types: List[EventType]
    priority_threshold: Priority = Priority.NORMAL
    keywords: List[str] = field(default_factory=list)
    source_agents: List[str] = field(default_factory=list)
    notification_methods: List[NotificationMethod] = field(
        default_factory=lambda: [NotificationMethod.DIRECT_MESSAGE]
    )
    enabled: bool = True
    created_at: float = field(default_factory=time.time)

    def matches_event(self, event: BaseEvent) -> bool:
        """Check if this rule matches the given event"""
        if not self.enabled:
            return False

        # Check event type
        if event.event_type not in self.event_types:
            return False

        # Check priority
        if event.priority.value < self.priority_threshold.value:
            return False

        # Check source agents
        if self.source_agents and event.source_agent_id not in self.source_agents:
            return False

        # Check keywords in event content
        if self.keywords:
            event_text = self._extract_event_text(event)
            if not any(
                keyword.lower() in event_text.lower() for keyword in self.keywords
            ):
                return False

        return True

    def _extract_event_text(self, event: BaseEvent) -> str:
        """Extract searchable text from an event"""
        text_parts = []

        # Include basic event data
        event_dict = event.to_dict()
        for key, value in event_dict.items():
            if isinstance(value, str):
                text_parts.append(value)
            elif isinstance(value, dict):
                text_parts.extend(str(v) for v in value.values() if isinstance(v, str))

        return " ".join(text_parts)


@dataclass
class NotificationPreferences:
    """Agent notification preferences"""

    agent_id: str
    max_notifications_per_hour: int = 50
    quiet_hours_start: Optional[int] = None  # Hour of day (0-23)
    quiet_hours_end: Optional[int] = None
    priority_filter: Priority = Priority.LOW
    consolidate_similar: bool = True
    delay_seconds: int = 0  # Delay before sending notifications

    def should_send_now(self, priority: Priority) -> bool:
        """Check if notification should be sent now based on preferences"""
        # Check priority filter
        if priority.value < self.priority_filter.value:
            return False

        # Check quiet hours
        if self.quiet_hours_start is not None and self.quiet_hours_end is not None:
            current_hour = time.localtime().tm_hour

            if self.quiet_hours_start <= self.quiet_hours_end:
                # Normal range (e.g., 22-06)
                if self.quiet_hours_start <= current_hour <= self.quiet_hours_end:
                    return priority == Priority.CRITICAL
            else:
                # Across midnight (e.g., 22-06)
                if (
                    current_hour >= self.quiet_hours_start
                    or current_hour <= self.quiet_hours_end
                ):
                    return priority == Priority.CRITICAL

        return True


@dataclass
class PendingNotification:
    """A notification waiting to be sent"""

    notification_id: str
    event: BaseEvent
    target_agent_id: str
    methods: List[NotificationMethod]
    scheduled_time: float
    attempts: int = 0
    max_attempts: int = 3


class NotificationEngine:
    """Intelligent notification routing and delivery system"""

    def __init__(self, event_bus: Optional[EventBus] = None):
        self.event_bus = event_bus or get_global_event_bus()
        self.rules: Dict[str, List[NotificationRule]] = defaultdict(list)
        self.preferences: Dict[str, NotificationPreferences] = {}
        self.pending_notifications: Dict[str, PendingNotification] = {}
        self.notification_history: List[Dict[str, Any]] = []
        self.handlers: Dict[NotificationMethod, Callable] = {}

        # Rate limiting
        self.notification_counts: Dict[str, List[float]] = defaultdict(list)

        # Subscribe to all events for notification processing
        self.event_bus.subscribe(self._process_event_for_notifications)

        # Start notification processor
        self._processor_task = None
        self._running = False

        logger.info("NotificationEngine initialized")

    async def start(self) -> None:
        """Start the notification processing loop"""
        if self._running:
            return

        self._running = True
        self._processor_task = asyncio.create_task(self._notification_processor())
        logger.info("NotificationEngine started")

    async def stop(self) -> None:
        """Stop the notification processing loop"""
        if not self._running:
            return

        self._running = False
        if self._processor_task:
            self._processor_task.cancel()
            try:
                await self._processor_task
            except asyncio.CancelledError:
                pass
        logger.info("NotificationEngine stopped")

    def register_handler(
        self,
        method: NotificationMethod,
        handler: Callable[[str, BaseEvent, Dict[str, Any]], None],
    ) -> None:
        """Register a notification delivery handler"""
        self.handlers[method] = handler
        logger.info(f"Registered handler for {method.value}")

    def add_notification_rule(self, rule: NotificationRule) -> None:
        """Add a notification rule for an agent"""
        self.rules[rule.agent_id].append(rule)
        logger.info(f"Added notification rule {rule.rule_id} for agent {rule.agent_id}")

    def remove_notification_rule(self, agent_id: str, rule_id: str) -> bool:
        """Remove a notification rule"""
        if agent_id in self.rules:
            self.rules[agent_id] = [
                rule for rule in self.rules[agent_id] if rule.rule_id != rule_id
            ]
            logger.info(f"Removed notification rule {rule_id} for agent {agent_id}")
            return True
        return False

    def set_preferences(self, preferences: NotificationPreferences) -> None:
        """Set notification preferences for an agent"""
        self.preferences[preferences.agent_id] = preferences
        logger.info(f"Set notification preferences for agent {preferences.agent_id}")

    def get_preferences(self, agent_id: str) -> NotificationPreferences:
        """Get notification preferences for an agent"""
        return self.preferences.get(
            agent_id, NotificationPreferences(agent_id=agent_id)
        )

    async def _process_event_for_notifications(self, event: BaseEvent) -> None:
        """Process an event to determine notifications to send"""
        try:
            notifications_to_schedule = []

            # Check all agents' notification rules
            for agent_id, agent_rules in self.rules.items():
                # Skip self-notifications unless explicitly configured
                if agent_id == event.source_agent_id:
                    continue

                for rule in agent_rules:
                    if rule.matches_event(event):
                        # Check rate limiting
                        if not await self._check_rate_limit(agent_id):
                            logger.debug(f"Rate limit exceeded for agent {agent_id}")
                            continue

                        # Get agent preferences
                        prefs = self.get_preferences(agent_id)

                        # Check if we should send now or delay
                        send_time = time.time()
                        if prefs.delay_seconds > 0:
                            send_time += prefs.delay_seconds

                        # Create pending notification
                        notification = PendingNotification(
                            notification_id=f"notif_{int(time.time() * 1000000)}",
                            event=event,
                            target_agent_id=agent_id,
                            methods=rule.notification_methods,
                            scheduled_time=send_time,
                        )

                        notifications_to_schedule.append(notification)
                        break  # One notification per agent per event

            # Schedule notifications
            for notification in notifications_to_schedule:
                self.pending_notifications[notification.notification_id] = notification

                logger.debug(
                    f"Scheduled notification {notification.notification_id} "
                    f"for agent {notification.target_agent_id}"
                )

        except Exception as e:
            logger.error(
                f"Error processing event {event.event_id} for notifications: {e}"
            )

    async def _check_rate_limit(self, agent_id: str) -> bool:
        """Check if agent is within rate limits"""
        prefs = self.get_preferences(agent_id)
        current_time = time.time()
        hour_ago = current_time - 3600

        # Clean old entries
        self.notification_counts[agent_id] = [
            timestamp
            for timestamp in self.notification_counts[agent_id]
            if timestamp > hour_ago
        ]

        # Check if under limit
        count = len(self.notification_counts[agent_id])
        return count < prefs.max_notifications_per_hour

    async def _notification_processor(self) -> None:
        """Background task to process pending notifications"""
        while self._running:
            try:
                current_time = time.time()
                notifications_to_send = []

                # Find notifications ready to send
                for notif_id, notification in list(self.pending_notifications.items()):
                    if notification.scheduled_time <= current_time:
                        notifications_to_send.append(notification)
                        del self.pending_notifications[notif_id]

                # Send notifications
                for notification in notifications_to_send:
                    await self._send_notification(notification)

                # Sleep briefly before next check
                await asyncio.sleep(0.1)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in notification processor: {e}")
                await asyncio.sleep(1)

    async def _send_notification(self, notification: PendingNotification) -> None:
        """Send a notification using configured methods"""
        try:
            # Check preferences one more time
            prefs = self.get_preferences(notification.target_agent_id)
            if not prefs.should_send_now(notification.event.priority):
                logger.debug(
                    f"Skipping notification due to preferences: {notification.notification_id}"
                )
                return

            # Record notification count
            self.notification_counts[notification.target_agent_id].append(time.time())

            # Send via each method
            success = False
            for method in notification.methods:
                if method in self.handlers:
                    try:
                        handler = self.handlers[method]

                        # Prepare notification data
                        notification_data = {
                            "notification_id": notification.notification_id,
                            "event_type": notification.event.event_type.value,
                            "priority": notification.event.priority.value,
                            "source_agent": notification.event.source_agent_id,
                            "timestamp": notification.event.timestamp,
                            "event_data": notification.event.to_dict(),
                        }

                        # Call handler
                        if asyncio.iscoroutinefunction(handler):
                            await handler(
                                notification.target_agent_id,
                                notification.event,
                                notification_data,
                            )
                        else:
                            handler(
                                notification.target_agent_id,
                                notification.event,
                                notification_data,
                            )

                        success = True
                        logger.debug(
                            f"Sent notification {notification.notification_id} "
                            f"via {method.value} to {notification.target_agent_id}"
                        )

                    except Exception as e:
                        logger.error(
                            f"Failed to send notification {notification.notification_id} "
                            f"via {method.value}: {e}"
                        )
                else:
                    logger.warning(f"No handler registered for method {method.value}")

            # Record in history
            self.notification_history.append(
                {
                    "notification_id": notification.notification_id,
                    "target_agent_id": notification.target_agent_id,
                    "event_id": notification.event.event_id,
                    "event_type": notification.event.event_type.value,
                    "sent_at": time.time(),
                    "success": success,
                    "attempts": notification.attempts + 1,
                }
            )

            # Keep history size manageable
            if len(self.notification_history) > 1000:
                self.notification_history = self.notification_history[-1000:]

        except Exception as e:
            logger.error(
                f"Error sending notification {notification.notification_id}: {e}"
            )

            # Retry if under max attempts
            notification.attempts += 1
            if notification.attempts < notification.max_attempts:
                notification.scheduled_time = time.time() + (notification.attempts * 30)
                self.pending_notifications[notification.notification_id] = notification
                logger.info(
                    f"Retrying notification {notification.notification_id} in {notification.attempts * 30}s"
                )

    async def send_direct_notification(
        self, agent_id: str, event: BaseEvent, methods: List[NotificationMethod] = None
    ) -> None:
        """Send a direct notification bypassing rules"""
        methods = methods or [NotificationMethod.DIRECT_MESSAGE]

        notification = PendingNotification(
            notification_id=f"direct_{int(time.time() * 1000000)}",
            event=event,
            target_agent_id=agent_id,
            methods=methods,
            scheduled_time=time.time(),
        )

        await self._send_notification(notification)

    def get_agent_notification_stats(self, agent_id: str) -> Dict[str, Any]:
        """Get notification statistics for an agent"""
        history = [
            notif
            for notif in self.notification_history
            if notif["target_agent_id"] == agent_id
        ]

        if not history:
            return {"total_notifications": 0}

        recent_history = [
            notif for notif in history if notif["sent_at"] > time.time() - 3600
        ]

        return {
            "total_notifications": len(history),
            "recent_notifications": len(recent_history),
            "success_rate": len([n for n in history if n["success"]]) / len(history),
            "most_common_event_types": self._get_most_common_event_types(history),
            "pending_notifications": len(
                [
                    n
                    for n in self.pending_notifications.values()
                    if n.target_agent_id == agent_id
                ]
            ),
        }

    def _get_most_common_event_types(self, history: List[Dict[str, Any]]) -> List[str]:
        """Get most common event types from notification history"""
        event_counts = defaultdict(int)
        for notif in history:
            event_counts[notif["event_type"]] += 1

        return sorted(event_counts.keys(), key=event_counts.get, reverse=True)[:5]

    def get_system_stats(self) -> Dict[str, Any]:
        """Get overall notification system statistics"""
        return {
            "total_rules": sum(len(rules) for rules in self.rules.values()),
            "active_agents": len(self.rules),
            "pending_notifications": len(self.pending_notifications),
            "total_notifications_sent": len(self.notification_history),
            "registered_handlers": list(self.handlers.keys()),
            "running": self._running,
        }


# Default notification handlers


async def default_direct_message_handler(
    agent_id: str, event: BaseEvent, notification_data: Dict[str, Any]
) -> None:
    """Default handler for direct messages"""
    logger.info(
        f"NOTIFICATION for {agent_id}: {event.event_type.value} "
        f"from {event.source_agent_id}"
    )


def create_default_notification_engine(
    event_bus: Optional[EventBus] = None,
) -> NotificationEngine:
    """Create a notification engine with default handlers"""
    engine = NotificationEngine(event_bus)

    # Register default handlers
    engine.register_handler(
        NotificationMethod.DIRECT_MESSAGE, default_direct_message_handler
    )

    return engine

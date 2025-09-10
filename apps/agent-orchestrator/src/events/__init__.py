"""
Event-Driven Coordination System

This module provides the core event infrastructure for real-time agent
coordination and collaboration.
"""

from .event_bus import EventBus, get_global_event_bus
from .event_history import EventHistory
from .event_processors import EventProcessor
from .event_types import (
    CoordinationEvent,
    DiscoveryEvent,
    ErrorEvent,
    ProgressEvent,
    SystemEvent,
)
from .notification_engine import NotificationEngine

__all__ = [
    "EventBus",
    "get_global_event_bus",
    "CoordinationEvent",
    "DiscoveryEvent",
    "ErrorEvent",
    "ProgressEvent",
    "SystemEvent",
    "NotificationEngine",
    "EventHistory",
    "EventProcessor",
]

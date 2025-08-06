"""
Events module for opsvi-core.

Provides event bus implementations, event handling, and event replay capabilities.
"""

from opsvi_foundation import (
    BaseComponent,
    ComponentError,
    get_logger,
)

# Base event infrastructure
from .base import (
    Event,
    EventBus,
    EventError,
    EventFilter,
    EventHandler,
    EventReplay,
)

# Event bus implementations
from .in_memory import InMemoryEventBus

__all__ = [
    # Base classes
    "Event",
    "EventBus",
    "EventError",
    "EventFilter",
    "EventHandler",
    "EventReplay",
    # Implementations
    "InMemoryEventBus",
]

__version__ = "1.0.0"

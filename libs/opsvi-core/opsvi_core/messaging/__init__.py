"""
Messaging module for opsvi-core.

Provides message broker implementations, routing, and queue management.
"""

from opsvi_foundation import (
    BaseComponent,
    ComponentError,
    get_logger,
)

# Base messaging infrastructure
from .base import (
    Message,
    MessageBroker,
    MessageQueue,
    MessageRoute,
    MessageRouter,
    MessagingError,
    QoSLevel,
)

# Message broker implementations
from .in_memory import InMemoryBroker

__all__ = [
    # Base classes
    "Message",
    "MessageBroker",
    "MessageQueue",
    "MessageRoute",
    "MessageRouter",
    "MessagingError",
    "QoSLevel",
    # Implementations
    "InMemoryBroker",
]

__version__ = "1.0.0"

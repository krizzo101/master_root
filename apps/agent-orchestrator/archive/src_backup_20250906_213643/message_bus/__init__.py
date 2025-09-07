"""
Message Bus Module for Agent-to-Agent Communication

High-performance Redis-based pub/sub system for real-time agent collaboration.
Provides point-to-point, broadcast, group, and topic-based messaging capabilities.
"""

from .admin.admin_interface import MessageBusAdmin
from .client.agent_client import AgentMessageClient
from .core.message_bus import MessageBus
from .core.message_types import Message, MessagePriority, MessageType
from .routing.message_router import MessageRouter

__all__ = [
    "MessageBus",
    "Message",
    "MessageType",
    "MessagePriority",
    "AgentMessageClient",
    "MessageRouter",
    "MessageBusAdmin",
]

__version__ = "1.0.0"

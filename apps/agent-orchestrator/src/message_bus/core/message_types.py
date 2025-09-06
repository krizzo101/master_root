"""
Core message types and data structures for the message bus system.
"""

import json
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class MessageType(Enum):
    """Types of messages supported by the message bus"""

    POINT_TO_POINT = "point_to_point"  # agent A -> agent B
    BROADCAST = "broadcast"  # agent A -> all agents
    GROUP = "group"  # agent A -> group members
    TOPIC = "topic"  # agent A -> topic subscribers
    SYSTEM = "system"  # system messages
    HEARTBEAT = "heartbeat"  # connection health checks


class MessagePriority(Enum):
    """Message priority levels"""

    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3


@dataclass
class Message:
    """Core message structure for agent communication"""

    # Core message identification
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    message_type: MessageType = MessageType.POINT_TO_POINT
    priority: MessagePriority = MessagePriority.NORMAL

    # Routing information
    sender_id: str = ""
    recipient_id: Optional[str] = None  # For point-to-point
    group_id: Optional[str] = None  # For group messages
    topic: Optional[str] = None  # For topic messages

    # Message content
    payload: Dict[str, Any] = field(default_factory=dict)
    content_type: str = "application/json"

    # Metadata
    timestamp: float = field(default_factory=time.time)
    ttl_seconds: Optional[int] = None  # Time to live
    correlation_id: Optional[str] = None  # For request/response patterns
    reply_to: Optional[str] = None  # Return address for responses

    # Delivery tracking
    delivery_attempts: int = 0
    max_delivery_attempts: int = 3
    requires_ack: bool = False  # Delivery confirmation required
    persistent: bool = False  # Should survive restarts

    # Processing metadata (set by message bus)
    received_timestamp: Optional[float] = None
    processed_timestamp: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary for serialization"""
        return {
            "message_id": self.message_id,
            "message_type": self.message_type.value,
            "priority": self.priority.value,
            "sender_id": self.sender_id,
            "recipient_id": self.recipient_id,
            "group_id": self.group_id,
            "topic": self.topic,
            "payload": self.payload,
            "content_type": self.content_type,
            "timestamp": self.timestamp,
            "ttl_seconds": self.ttl_seconds,
            "correlation_id": self.correlation_id,
            "reply_to": self.reply_to,
            "delivery_attempts": self.delivery_attempts,
            "max_delivery_attempts": self.max_delivery_attempts,
            "requires_ack": self.requires_ack,
            "persistent": self.persistent,
            "received_timestamp": self.received_timestamp,
            "processed_timestamp": self.processed_timestamp,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Message":
        """Create message from dictionary"""
        # Convert enum values
        message_type = MessageType(data.get("message_type", "point_to_point"))
        priority = MessagePriority(data.get("priority", 1))

        return cls(
            message_id=data.get("message_id", str(uuid.uuid4())),
            message_type=message_type,
            priority=priority,
            sender_id=data.get("sender_id", ""),
            recipient_id=data.get("recipient_id"),
            group_id=data.get("group_id"),
            topic=data.get("topic"),
            payload=data.get("payload", {}),
            content_type=data.get("content_type", "application/json"),
            timestamp=data.get("timestamp", time.time()),
            ttl_seconds=data.get("ttl_seconds"),
            correlation_id=data.get("correlation_id"),
            reply_to=data.get("reply_to"),
            delivery_attempts=data.get("delivery_attempts", 0),
            max_delivery_attempts=data.get("max_delivery_attempts", 3),
            requires_ack=data.get("requires_ack", False),
            persistent=data.get("persistent", False),
            received_timestamp=data.get("received_timestamp"),
            processed_timestamp=data.get("processed_timestamp"),
        )

    def to_json(self) -> str:
        """Convert message to JSON string"""
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str: str) -> "Message":
        """Create message from JSON string"""
        data = json.loads(json_str)
        return cls.from_dict(data)

    def is_expired(self) -> bool:
        """Check if message has expired based on TTL"""
        if self.ttl_seconds is None:
            return False
        return time.time() > (self.timestamp + self.ttl_seconds)

    def can_retry(self) -> bool:
        """Check if message can be retried"""
        return self.delivery_attempts < self.max_delivery_attempts

    def increment_delivery_attempts(self) -> None:
        """Increment delivery attempt counter"""
        self.delivery_attempts += 1

    def mark_received(self) -> None:
        """Mark message as received"""
        self.received_timestamp = time.time()

    def mark_processed(self) -> None:
        """Mark message as processed"""
        self.processed_timestamp = time.time()


@dataclass
class MessageAck:
    """Acknowledgment message for delivery confirmation"""

    message_id: str
    recipient_id: str
    status: str  # "delivered", "processed", "failed"
    timestamp: float = field(default_factory=time.time)
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "message_id": self.message_id,
            "recipient_id": self.recipient_id,
            "status": self.status,
            "timestamp": self.timestamp,
            "error_message": self.error_message,
        }


@dataclass
class MessageStats:
    """Statistics for message delivery and processing"""

    total_sent: int = 0
    total_received: int = 0
    total_processed: int = 0
    total_failed: int = 0
    total_expired: int = 0
    average_delivery_time_ms: float = 0.0
    average_processing_time_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_sent": self.total_sent,
            "total_received": self.total_received,
            "total_processed": self.total_processed,
            "total_failed": self.total_failed,
            "total_expired": self.total_expired,
            "average_delivery_time_ms": self.average_delivery_time_ms,
            "average_processing_time_ms": self.average_processing_time_ms,
        }

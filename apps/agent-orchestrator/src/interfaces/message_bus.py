"""
Message Bus Interface for dependency injection
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set


class MessageType(Enum):
    """Types of messages"""

    DIRECT = "direct"
    BROADCAST = "broadcast"
    COORDINATION = "coordination"
    STATUS_UPDATE = "status_update"
    ERROR = "error"
    HANDOFF = "handoff"


class Priority(Enum):
    """Message priority levels"""

    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4


@dataclass
class Message:
    """Standard message structure"""

    message_type: MessageType
    sender: str
    recipient: Optional[str]  # None for broadcast
    payload: Dict[str, Any]
    priority: Priority = Priority.NORMAL
    correlation_id: Optional[str] = None
    requires_response: bool = False


class IMessageBus(ABC):
    """
    Abstract interface for message bus implementations.
    Provides pub/sub messaging for inter-component communication.
    """

    @abstractmethod
    async def connect(self) -> None:
        """
        Connect to the message bus.

        Raises:
            ConnectionError: If connection fails
        """
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """
        Disconnect from the message bus.
        """
        pass

    @abstractmethod
    async def publish(self, message: Message) -> str:
        """
        Publish a message to the bus.

        Args:
            message: Message to publish

        Returns:
            Message ID

        Raises:
            RuntimeError: If not connected
            ValueError: If message is invalid
        """
        pass

    @abstractmethod
    async def subscribe(
        self,
        topics: List[str],
        handler: Callable[[Message], None],
        subscriber_id: Optional[str] = None,
    ) -> str:
        """
        Subscribe to message topics.

        Args:
            topics: List of topics to subscribe to
            handler: Callback function for messages
            subscriber_id: Optional subscriber identifier

        Returns:
            Subscription ID

        Raises:
            RuntimeError: If not connected
        """
        pass

    @abstractmethod
    async def unsubscribe(self, subscription_id: str) -> None:
        """
        Unsubscribe from messages.

        Args:
            subscription_id: Subscription to cancel
        """
        pass

    @abstractmethod
    async def send_direct(
        self,
        recipient: str,
        payload: Dict[str, Any],
        priority: Priority = Priority.NORMAL,
    ) -> str:
        """
        Send a direct message to a specific recipient.

        Args:
            recipient: Target recipient ID
            payload: Message payload
            priority: Message priority

        Returns:
            Message ID

        Raises:
            RuntimeError: If not connected
            ValueError: If recipient not found
        """
        pass

    @abstractmethod
    async def broadcast(
        self, payload: Dict[str, Any], priority: Priority = Priority.NORMAL
    ) -> str:
        """
        Broadcast a message to all subscribers.

        Args:
            payload: Message payload
            priority: Message priority

        Returns:
            Message ID

        Raises:
            RuntimeError: If not connected
        """
        pass

    @abstractmethod
    async def request_response(
        self,
        recipient: str,
        payload: Dict[str, Any],
        timeout: float = 30.0,
    ) -> Optional[Message]:
        """
        Send a request and wait for response.

        Args:
            recipient: Target recipient ID
            payload: Request payload
            timeout: Response timeout in seconds

        Returns:
            Response message or None if timeout

        Raises:
            RuntimeError: If not connected
            TimeoutError: If no response within timeout
        """
        pass

    @abstractmethod
    async def get_subscribers(self) -> Set[str]:
        """
        Get list of active subscribers.

        Returns:
            Set of subscriber IDs
        """
        pass

    @abstractmethod
    async def get_metrics(self) -> Dict:
        """
        Get message bus metrics.

        Returns:
            Dictionary containing messaging metrics
        """
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """
        Check health status of message bus.

        Returns:
            True if healthy, False otherwise
        """
        pass

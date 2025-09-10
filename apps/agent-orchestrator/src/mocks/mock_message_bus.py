"""
Mock MessageBus implementation for testing
"""

import asyncio
import uuid
from collections import defaultdict, deque
from typing import Any, Callable, Dict, List, Optional, Set

from ..interfaces.message_bus import IMessageBus, Message, MessageType, Priority


class MockMessageBus(IMessageBus):
    """
    Mock implementation of IMessageBus for testing.
    Simulates message passing in memory without external dependencies.
    """

    def __init__(
        self,
        simulate_delays: bool = False,
        failure_rate: float = 0.0,
        message_loss_rate: float = 0.0,
    ):
        """
        Initialize mock message bus.

        Args:
            simulate_delays: Add realistic delays to operations
            failure_rate: Probability of operations failing (0.0-1.0)
            message_loss_rate: Probability of messages being lost (0.0-1.0)
        """
        self.connected = False
        self.simulate_delays = simulate_delays
        self.failure_rate = failure_rate
        self.message_loss_rate = message_loss_rate

        # Message storage and routing
        self.message_queue: deque = deque()
        self.subscriptions: Dict[str, Dict] = {}  # subscription_id -> config
        self.subscribers: Set[str] = set()
        self.topic_handlers: Dict[str, List[Callable]] = defaultdict(list)

        # Tracking for assertions
        self.published_messages: List[Message] = []
        self.delivered_messages: List[Dict] = []
        self.lost_messages: List[Message] = []
        self.connection_count = 0
        self.disconnection_count = 0

    async def _maybe_fail(self):
        """Simulate random failures for testing error handling"""
        import random

        if random.random() < self.failure_rate:
            raise RuntimeError("Simulated message bus failure")

    async def _maybe_delay(self, min_ms: int = 5, max_ms: int = 30):
        """Add realistic delays if configured"""
        if self.simulate_delays:
            import random

            delay = random.randint(min_ms, max_ms) / 1000
            await asyncio.sleep(delay)

    async def _maybe_lose_message(self, message: Message) -> bool:
        """Simulate message loss for testing reliability"""
        import random

        if random.random() < self.message_loss_rate:
            self.lost_messages.append(message)
            return True
        return False

    async def connect(self) -> None:
        """Connect to mock message bus"""
        await self._maybe_delay(10, 50)
        await self._maybe_fail()

        if self.connected:
            raise ConnectionError("Already connected to message bus")

        self.connected = True
        self.connection_count += 1

    async def disconnect(self) -> None:
        """Disconnect from mock message bus"""
        await self._maybe_delay(5, 20)

        if self.connected:
            self.connected = False
            self.disconnection_count += 1

    async def publish(self, message: Message) -> str:
        """Publish message to mock bus"""
        await self._maybe_delay()
        await self._maybe_fail()

        if not self.connected:
            raise RuntimeError("Not connected to message bus")

        # Generate message ID if not present
        message_id = f"msg_{uuid.uuid4().hex[:8]}"

        # Track published message
        self.published_messages.append(message)

        # Simulate message loss
        if await self._maybe_lose_message(message):
            return message_id

        # Route message based on type
        if message.message_type == MessageType.DIRECT and message.recipient:
            # Direct message - deliver to specific recipient
            await self._deliver_to_recipient(message, message.recipient)
        else:
            # Broadcast or topic-based message
            await self._deliver_to_subscribers(message)

        return message_id

    async def _deliver_to_recipient(self, message: Message, recipient: str):
        """Deliver message to specific recipient"""
        for sub_id, config in self.subscriptions.items():
            if config.get("subscriber_id") == recipient:
                handler = config["handler"]
                await self._invoke_handler(handler, message, sub_id)
                break

    async def _deliver_to_subscribers(self, message: Message):
        """Deliver message to all relevant subscribers"""
        message_type_str = message.message_type.value

        for sub_id, config in self.subscriptions.items():
            topics = config.get("topics", [])

            # Check if subscriber is interested in this message type
            if message_type_str in topics or "broadcast" in topics:
                handler = config["handler"]
                await self._invoke_handler(handler, message, sub_id)

    async def _invoke_handler(
        self, handler: Callable, message: Message, subscription_id: str
    ):
        """Invoke message handler with tracking"""
        try:
            await self._maybe_delay(2, 10)

            # Call handler
            result = handler(message)
            if asyncio.iscoroutine(result):
                await result

            # Track delivery
            self.delivered_messages.append(
                {
                    "message": message,
                    "subscription_id": subscription_id,
                    "success": True,
                }
            )
        except Exception as e:
            self.delivered_messages.append(
                {
                    "message": message,
                    "subscription_id": subscription_id,
                    "success": False,
                    "error": str(e),
                }
            )

    async def subscribe(
        self,
        topics: List[str],
        handler: Callable[[Message], None],
        subscriber_id: Optional[str] = None,
    ) -> str:
        """Subscribe to mock message topics"""
        await self._maybe_delay()
        await self._maybe_fail()

        if not self.connected:
            raise RuntimeError("Not connected to message bus")

        subscription_id = f"sub_{uuid.uuid4().hex[:8]}"
        subscriber_id = subscriber_id or f"subscriber_{uuid.uuid4().hex[:8]}"

        self.subscriptions[subscription_id] = {
            "topics": topics,
            "handler": handler,
            "subscriber_id": subscriber_id,
        }

        self.subscribers.add(subscriber_id)

        return subscription_id

    async def unsubscribe(self, subscription_id: str) -> None:
        """Unsubscribe from mock messages"""
        await self._maybe_delay()

        if subscription_id in self.subscriptions:
            config = self.subscriptions[subscription_id]
            del self.subscriptions[subscription_id]

            # Remove subscriber if no more subscriptions
            subscriber_id = config["subscriber_id"]
            has_other_subs = any(
                s["subscriber_id"] == subscriber_id for s in self.subscriptions.values()
            )
            if not has_other_subs:
                self.subscribers.discard(subscriber_id)

    async def send_direct(
        self,
        recipient: str,
        payload: Dict[str, Any],
        priority: Priority = Priority.NORMAL,
    ) -> str:
        """Send direct message in mock bus"""
        message = Message(
            message_type=MessageType.DIRECT,
            sender="mock_sender",
            recipient=recipient,
            payload=payload,
            priority=priority,
        )

        return await self.publish(message)

    async def broadcast(
        self, payload: Dict[str, Any], priority: Priority = Priority.NORMAL
    ) -> str:
        """Broadcast message in mock bus"""
        message = Message(
            message_type=MessageType.BROADCAST,
            sender="mock_sender",
            recipient=None,
            payload=payload,
            priority=priority,
        )

        return await self.publish(message)

    async def request_response(
        self,
        recipient: str,
        payload: Dict[str, Any],
        timeout: float = 30.0,
    ) -> Optional[Message]:
        """Mock request-response pattern"""
        await self._maybe_delay(10, 50)
        await self._maybe_fail()

        if not self.connected:
            raise RuntimeError("Not connected to message bus")

        # Send request
        correlation_id = f"req_{uuid.uuid4().hex[:8]}"
        request = Message(
            message_type=MessageType.DIRECT,
            sender="mock_sender",
            recipient=recipient,
            payload=payload,
            priority=Priority.NORMAL,
            correlation_id=correlation_id,
            requires_response=True,
        )

        await self.publish(request)

        # Simulate response (mock always responds unless timeout is very short)
        if timeout < 0.1:
            raise TimeoutError(f"No response within {timeout} seconds")

        await self._maybe_delay(20, 100)

        # Create mock response
        response = Message(
            message_type=MessageType.DIRECT,
            sender=recipient,
            recipient="mock_sender",
            payload={"response": "Mock response", "original_payload": payload},
            priority=Priority.NORMAL,
            correlation_id=correlation_id,
        )

        return response

    async def get_subscribers(self) -> Set[str]:
        """Get mock subscribers"""
        await self._maybe_delay(5, 10)
        return self.subscribers.copy()

    async def get_metrics(self) -> Dict:
        """Get mock metrics for testing"""
        await self._maybe_delay(5, 10)

        return {
            "connected": self.connected,
            "total_subscriptions": len(self.subscriptions),
            "total_subscribers": len(self.subscribers),
            "published_messages": len(self.published_messages),
            "delivered_messages": len(self.delivered_messages),
            "lost_messages": len(self.lost_messages),
            "connection_count": self.connection_count,
            "disconnection_count": self.disconnection_count,
            "message_loss_rate": self.message_loss_rate,
            "failure_rate": self.failure_rate,
            "simulated_delays": self.simulate_delays,
        }

    async def health_check(self) -> bool:
        """Mock health check"""
        await self._maybe_delay(5, 10)

        # Simulate unhealthy if not connected or high failure rate
        if not self.connected:
            return False
        if self.failure_rate > 0.5:
            return False

        return True

    # Testing utility methods

    def reset(self):
        """Reset mock to initial state for testing"""
        self.connected = False
        self.message_queue.clear()
        self.subscriptions.clear()
        self.subscribers.clear()
        self.topic_handlers.clear()
        self.published_messages.clear()
        self.delivered_messages.clear()
        self.lost_messages.clear()
        self.connection_count = 0
        self.disconnection_count = 0

    def get_published_messages(self) -> List[Message]:
        """Get all published messages for assertions"""
        return self.published_messages.copy()

    def get_delivered_messages(self) -> List[Dict]:
        """Get all delivered messages for assertions"""
        return self.delivered_messages.copy()

    def get_lost_messages(self) -> List[Message]:
        """Get all lost messages for debugging"""
        return self.lost_messages.copy()

    def simulate_incoming_message(self, message: Message):
        """Simulate an incoming message for testing handlers"""
        if self.connected:
            asyncio.create_task(self._deliver_to_subscribers(message))

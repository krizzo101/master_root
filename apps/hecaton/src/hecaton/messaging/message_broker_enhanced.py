"""
Enhanced message broker with backpressure and cancellation support
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Set
from uuid import uuid4

from ..core.schemas import Message, MessageType, TaskStatus

logger = logging.getLogger(__name__)


@dataclass
class BrokerConfig:
    """Configuration for message broker"""

    max_queue_size: int = 100
    max_topics: int = 50
    dead_letter_enabled: bool = True
    timeout_seconds: int = 300


class MessageBrokerEnhanced:
    """
    Enhanced message broker with backpressure and cancellation.

    Features:
    - Bounded queues with backpressure
    - Graceful cancellation on teardown
    - Dead letter queue for failed messages
    - Metrics tracking
    """

    def __init__(self, config: Optional[BrokerConfig] = None):
        self.config = config or BrokerConfig()
        self._topic_queues: Dict[str, asyncio.Queue] = {}
        self._subscribers: Dict[str, List[Callable]] = {}
        self._direct_queues: Dict[str, asyncio.Queue] = {}
        self._dead_letter_queue: asyncio.Queue = asyncio.Queue()
        self._lock = asyncio.Lock()
        self._running = False
        self._tasks: Set[asyncio.Task] = set()
        self._metrics = {
            "messages_published": 0,
            "messages_delivered": 0,
            "messages_failed": 0,
            "messages_deadlettered": 0,
        }

    async def start(self) -> None:
        """Start the message broker"""
        async with self._lock:
            if self._running:
                logger.warning("Broker already running")
                return

            self._running = True
            logger.info("Message broker started")

            # Start dead letter processor if enabled
            if self.config.dead_letter_enabled:
                task = asyncio.create_task(self._process_dead_letters())
                self._tasks.add(task)

    async def stop(self) -> None:
        """Stop broker with graceful cancellation"""
        async with self._lock:
            if not self._running:
                return

            logger.info("Stopping message broker...")
            self._running = False

            # Cancel all subscriber tasks
            for task in self._tasks:
                if not task.done():
                    task.cancel()

            # Wait for cancellation with timeout
            if self._tasks:
                try:
                    await asyncio.wait_for(
                        asyncio.gather(*self._tasks, return_exceptions=True), timeout=5.0
                    )
                except asyncio.TimeoutError:
                    logger.warning("Some tasks didn't cancel gracefully")

            # Drain remaining messages to dead letter queue
            for topic, queue in self._topic_queues.items():
                count = 0
                while not queue.empty():
                    try:
                        msg = queue.get_nowait()
                        await self._dead_letter_queue.put(msg)
                        count += 1
                    except asyncio.QueueEmpty:
                        break
                if count > 0:
                    logger.info(f"Moved {count} unprocessed messages from {topic} to dead letter")

            # Clear state
            self._topic_queues.clear()
            self._subscribers.clear()
            self._direct_queues.clear()
            self._tasks.clear()

            logger.info(f"Broker stopped. Metrics: {self._metrics}")

    async def publish(self, topic: str, message: Message) -> bool:
        """
        Publish message with backpressure handling.

        Returns:
            True if published, False if queue full
        """
        if not self._running:
            raise RuntimeError("Broker not running")

        message.validate()

        async with self._lock:
            # Check topic limit
            if topic not in self._topic_queues:
                if len(self._topic_queues) >= self.config.max_topics:
                    logger.error(f"Topic limit reached ({self.config.max_topics})")
                    return False

                # Create bounded queue
                self._topic_queues[topic] = asyncio.Queue(maxsize=self.config.max_queue_size)

            queue = self._topic_queues[topic]

        # Try to put with backpressure
        try:
            queue.put_nowait(message)
            self._metrics["messages_published"] += 1

            # Trigger subscribers
            await self._notify_subscribers(topic, message)

            return True

        except asyncio.QueueFull:
            logger.warning(f"Queue full for topic {topic}, applying backpressure")
            self._metrics["messages_failed"] += 1

            # Send to dead letter if enabled
            if self.config.dead_letter_enabled:
                await self._dead_letter_queue.put(message)
                self._metrics["messages_deadlettered"] += 1

            return False

    async def subscribe(self, topic: str, handler: Callable) -> str:
        """
        Subscribe to topic with handler.

        Returns:
            Subscription ID for unsubscribe
        """
        async with self._lock:
            if topic not in self._subscribers:
                self._subscribers[topic] = []

            self._subscribers[topic].append(handler)
            sub_id = f"{topic}_{uuid4().hex[:8]}"

            # Start consumer task
            task = asyncio.create_task(self._consume_topic(topic, handler, sub_id))
            self._tasks.add(task)
            task.add_done_callback(self._tasks.discard)

            logger.info(f"Subscribed to {topic} with ID {sub_id}")
            return sub_id

    async def unsubscribe(self, topic: str, sub_id: str) -> None:
        """Unsubscribe from topic"""
        async with self._lock:
            # Cancel associated task
            for task in list(self._tasks):
                if hasattr(task, "sub_id") and task.sub_id == sub_id:
                    task.cancel()
                    self._tasks.discard(task)
                    break

    async def send_direct(self, agent_id: str, message: Message) -> bool:
        """
        Send direct message to agent.

        Returns:
            True if sent, False if queue full
        """
        if not self._running:
            raise RuntimeError("Broker not running")

        async with self._lock:
            if agent_id not in self._direct_queues:
                self._direct_queues[agent_id] = asyncio.Queue(maxsize=self.config.max_queue_size)

            queue = self._direct_queues[agent_id]

        try:
            queue.put_nowait(message)
            return True
        except asyncio.QueueFull:
            logger.warning(f"Direct queue full for {agent_id}")
            return False

    async def receive_direct(
        self, agent_id: str, timeout: Optional[float] = None
    ) -> Optional[Message]:
        """
        Receive direct message for agent.

        Returns:
            Message or None if timeout
        """
        if agent_id not in self._direct_queues:
            async with self._lock:
                self._direct_queues[agent_id] = asyncio.Queue(maxsize=self.config.max_queue_size)

        queue = self._direct_queues[agent_id]

        try:
            if timeout:
                return await asyncio.wait_for(queue.get(), timeout=timeout)
            else:
                return await queue.get()
        except asyncio.TimeoutError:
            return None

    async def _notify_subscribers(self, topic: str, message: Message) -> None:
        """Notify all subscribers of a topic"""
        if topic in self._subscribers:
            for handler in self._subscribers[topic]:
                try:
                    # Call handler in background
                    asyncio.create_task(self._safe_handler_call(handler, message))
                except Exception as e:
                    logger.error(f"Failed to notify subscriber: {e}")

    async def _safe_handler_call(self, handler: Callable, message: Message) -> None:
        """Safely call handler with error handling"""
        try:
            await handler(message)
            self._metrics["messages_delivered"] += 1
        except Exception as e:
            logger.error(f"Handler error: {e}")
            self._metrics["messages_failed"] += 1

            # Send to dead letter
            if self.config.dead_letter_enabled:
                await self._dead_letter_queue.put(message)
                self._metrics["messages_deadlettered"] += 1

    async def _consume_topic(self, topic: str, handler: Callable, sub_id: str) -> None:
        """Consume messages from topic queue"""
        if topic not in self._topic_queues:
            return

        queue = self._topic_queues[topic]

        while self._running:
            try:
                # Get with timeout to allow cancellation check
                message = await asyncio.wait_for(queue.get(), timeout=1.0)
                await self._safe_handler_call(handler, message)
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                logger.info(f"Consumer {sub_id} cancelled")
                break
            except Exception as e:
                logger.error(f"Consumer error: {e}")

    async def _process_dead_letters(self) -> None:
        """Process dead letter queue"""
        while self._running:
            try:
                message = await asyncio.wait_for(self._dead_letter_queue.get(), timeout=5.0)

                # Log dead letter for analysis
                logger.warning(f"Dead letter: {message.type} from {message.sender}")

                # Could implement retry logic here

            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break

    def get_metrics(self) -> Dict[str, int]:
        """Get broker metrics"""
        return self._metrics.copy()

    def get_queue_sizes(self) -> Dict[str, int]:
        """Get current queue sizes"""
        sizes = {}
        for topic, queue in self._topic_queues.items():
            sizes[f"topic_{topic}"] = queue.qsize()
        for agent_id, queue in self._direct_queues.items():
            sizes[f"direct_{agent_id}"] = queue.qsize()
        sizes["dead_letter"] = self._dead_letter_queue.qsize()
        return sizes

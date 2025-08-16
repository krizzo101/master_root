"""opsvi-communication - Core opsvi-communication functionality.

Comprehensive opsvi-communication library for the OPSVI ecosystem
"""

from __future__ import annotations

from typing import Any, Awaitable, Callable, Dict, Optional, Tuple
import asyncio
import logging
import uuid
from dataclasses import dataclass, field

from opsvi_foundation import BaseComponent, ComponentError
from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)


class OpsviCommunicationManagerError(ComponentError):
    """Base exception for opsvi-communication errors."""
    pass


class OpsviCommunicationManagerConfigurationError(OpsviCommunicationManagerError):
    """Configuration-related errors in opsvi-communication."""
    pass


class OpsviCommunicationManagerInitializationError(OpsviCommunicationManagerError):
    """Initialization-related errors in opsvi-communication."""
    pass


class OpsviCommunicationManagerConfig(BaseSettings):
    """Configuration for opsvi-communication."""

    enabled: bool = True
    debug: bool = False
    log_level: str = "INFO"

    # Messaging configuration
    default_queue_size: int = 1024
    default_timeout: float = 5.0
    channels: Tuple[str, ...] = ()

    class Config:
        env_prefix = "OPSVI_OPSVI_COMMUNICATION__"


Handler = Callable[[Any, Dict[str, Any]], Awaitable[Optional[Any]]]


@dataclass
class _Message:
    channel: str
    payload: Any
    metadata: Dict[str, Any] = field(default_factory=dict)
    reply_future: Optional[asyncio.Future] = None


@dataclass
class _Channel:
    name: str
    queue: asyncio.Queue
    subscribers: Dict[str, Handler] = field(default_factory=dict)
    dispatcher: Optional[asyncio.Task] = None
    closed: bool = False


class OpsviCommunicationManager(BaseComponent):
    """Base class for opsvi-communication components with in-memory pub/sub."""

    def __init__(
        self,
        config: Optional[OpsviCommunicationManagerConfig] = None,
        **kwargs: Any,
    ) -> None:
        super().__init__("opsvi-communication", config.dict() if config else {})
        self.config = config or OpsviCommunicationManagerConfig(**kwargs)
        self._initialized = False
        self._logger = logging.getLogger(f"{__name__}.opsvi-communication")
        self._channels: Dict[str, _Channel] = {}
        self._subs_to_channel: Dict[str, str] = {}
        self._lock = asyncio.Lock()

    async def initialize(self) -> None:
        """Initialize the component and pre-create configured channels."""
        try:
            if not self.config.enabled:
                self._logger.info("opsvi-communication disabled by configuration")
                self._initialized = True
                return

            level = getattr(logging, self.config.log_level.upper(), logging.INFO)
            logging.getLogger(__name__).setLevel(level)
            if self.config.debug:
                self._logger.setLevel(logging.DEBUG)

            for ch in self.config.channels:
                await self.create_channel(ch)

            self._initialized = True
            self._logger.info("opsvi-communication initialized successfully")
        except Exception as e:
            self._logger.error(f"Failed to initialize opsvi-communication: {e}")
            raise OpsviCommunicationManagerInitializationError(
                f"Initialization failed: {e}"
            ) from e

    async def shutdown(self) -> None:
        """Shutdown the component and stop dispatchers."""
        try:
            self._logger.info("Shutting down opsvi-communication")
            async with self._lock:
                channels = list(self._channels.values())
            await asyncio.gather(*(self._stop_channel(c) for c in channels), return_exceptions=True)
            self._initialized = False
            self._logger.info("opsvi-communication shut down successfully")
        except Exception as e:
            self._logger.error(f"Failed to shutdown opsvi-communication: {e}")
            raise OpsviCommunicationManagerError(f"Shutdown failed: {e}") from e

    async def health_check(self) -> bool:
        """Perform health check."""
        try:
            if not self._initialized:
                return False
            async with self._lock:
                for ch in self._channels.values():
                    if ch.dispatcher and ch.dispatcher.done() and not ch.closed:
                        return False
            return True
        except Exception as e:
            self._logger.error(f"Health check failed: {e}")
            return False

    # Channel management
    async def create_channel(self, name: str, *, maxsize: Optional[int] = None) -> None:
        """Create a channel if it does not exist."""
        async with self._lock:
            if name in self._channels:
                return
            queue = asyncio.Queue(maxsize or self.config.default_queue_size)
            ch = _Channel(name=name, queue=queue)
            ch.dispatcher = asyncio.create_task(self._dispatch_loop(ch), name=f"opsvi-dispatch#{name}")
            self._channels[name] = ch
            self._logger.debug(f"Created channel '{name}'")

    async def delete_channel(self, name: str) -> None:
        """Delete a channel after stopping its dispatcher."""
        async with self._lock:
            ch = self._channels.get(name)
        if ch:
            await self._stop_channel(ch)
            async with self._lock:
                self._channels.pop(name, None)
                # Clean dangling subscriptions mapping
                for sid, cname in list(self._subs_to_channel.items()):
                    if cname == name:
                        self._subs_to_channel.pop(sid, None)

    def list_channels(self) -> Tuple[str, ...]:
        """Return current channel names."""
        return tuple(self._channels.keys())

    # Subscription management
    async def subscribe(self, channel: str, handler: Handler) -> str:
        """Subscribe an async handler to a channel; returns subscription id."""
        if not asyncio.iscoroutinefunction(handler):
            raise OpsviCommunicationManagerConfigurationError("Handler must be an async function")
        await self.create_channel(channel)
        sid = uuid.uuid4().hex
        async with self._lock:
            ch = self._channels[channel]
            ch.subscribers[sid] = handler
            self._subs_to_channel[sid] = channel
        self._logger.debug(f"Subscribed '{sid}' to '{channel}'")
        return sid

    async def unsubscribe(self, subscription_id: str) -> None:
        """Remove a subscription by id."""
        async with self._lock:
            channel = self._subs_to_channel.pop(subscription_id, None)
            if not channel:
                return
            ch = self._channels.get(channel)
            if ch:
                ch.subscribers.pop(subscription_id, None)
        self._logger.debug(f"Unsubscribed '{subscription_id}' from '{channel}'")

    # Messaging APIs
    async def publish(self, channel: str, payload: Any, metadata: Optional[Dict[str, Any]] = None, *, wait: bool = False) -> None:
        """Publish a message to a channel; optionally wait for handlers to finish."""
        await self.create_channel(channel)
        msg = _Message(channel=channel, payload=payload, metadata=metadata or {})
        fut = None
        if wait:
            fut = asyncio.get_running_loop().create_future()
            msg.reply_future = fut  # Will be completed once first handler finishes
        await self._enqueue(channel, msg)
        if fut:
            with contextlib.suppress(asyncio.TimeoutError):
                await asyncio.wait_for(fut, timeout=self.config.default_timeout)

    async def request(self, channel: str, payload: Any, metadata: Optional[Dict[str, Any]] = None, *, timeout: Optional[float] = None) -> Any:
        """Request/response pattern. Returns the first non-None handler result."""
        await self.create_channel(channel)
        async with self._lock:
            ch = self._channels[channel]
            if not ch.subscribers:
                raise OpsviCommunicationManagerError(f"No subscribers on channel '{channel}'")
        loop = asyncio.get_running_loop()
        reply_future: asyncio.Future = loop.create_future()
        msg = _Message(channel=channel, payload=payload, metadata=metadata or {}, reply_future=reply_future)
        await self._enqueue(channel, msg)
        timeout = timeout or self.config.default_timeout
        return await asyncio.wait_for(reply_future, timeout=timeout)

    # Internals
    async def _enqueue(self, channel: str, msg: _Message) -> None:
        async with self._lock:
            ch = self._channels.get(channel)
            if not ch:
                raise OpsviCommunicationManagerError(f"Channel '{channel}' not found")
            await ch.queue.put(msg)

    async def _stop_channel(self, ch: _Channel) -> None:
        ch.closed = True
        if ch.dispatcher and not ch.dispatcher.done():
            ch.dispatcher.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await ch.dispatcher
        # Drain queue
        while not ch.queue.empty():
            with contextlib.suppress(asyncio.QueueEmpty):
                ch.queue.get_nowait()
                ch.queue.task_done()
        ch.subscribers.clear()

    async def _dispatch_loop(self, ch: _Channel) -> None:
        """Fan-out dispatcher for a channel."""
        try:
            while True:
                msg: _Message = await ch.queue.get()
                async with self._lock:
                    subs = list(ch.subscribers.items())
                if not subs:
                    # No subscribers: if someone awaits reply, fail fast
                    if msg.reply_future and not msg.reply_future.done():
                        msg.reply_future.set_exception(OpsviCommunicationManagerError("No subscribers available"))
                    ch.queue.task_done()
                    continue

                tasks = [asyncio.create_task(self._invoke(handler, msg), name=f"opsvi-hdl#{sid}") for sid, handler in subs]
                # If reply expected, complete when first non-None result arrives
                if msg.reply_future is not None and not msg.reply_future.done():
                    async def complete_on_first() -> None:
                        try:
                            for t in asyncio.as_completed(tasks):
                                res = await t
                                if res is not None and not msg.reply_future.done():
                                    msg.reply_future.set_result(res)
                                    break
                            # If all done and no result, set None
                            if not msg.reply_future.done():
                                msg.reply_future.set_result(None)
                        except Exception as e:  # pragma: no cover - guarded
                            if not msg.reply_future.done():
                                msg.reply_future.set_exception(e)
                    asyncio.create_task(complete_on_first())
                ch.queue.task_done()
        except asyncio.CancelledError:
            return
        except Exception as e:  # pragma: no cover - unexpected
            self._logger.exception(f"Dispatcher error on '{ch.name}': {e}")

    async def _invoke(self, handler: Handler, msg: _Message) -> Optional[Any]:
        try:
            res = await handler(msg.payload, dict(msg.metadata))
            # If no reply_future, but publish(wait=True) provided one: any completion should resolve
            if msg.reply_future is not None and not msg.reply_future.done() and res is None:
                msg.reply_future.set_result(None)
            return res
        except Exception as e:
            self._logger.exception(f"Handler error on channel '{msg.channel}': {e}")
            if msg.reply_future is not None and not msg.reply_future.done():
                msg.reply_future.set_exception(e)
            return None


# Utilities needed in a single file without adding imports at top
import contextlib

"""Comm channel base for opsvi-communication.

This module provides an abstract Channel base class that defines a small
publish/subscribe acknowledgement surface together with a retry helper and
a small consumer runner that handles ack/nack semantics. Concrete
implementations should subclass Channel and implement publish and
subscribe.
"""
from __future__ import annotations

import abc
import asyncio
import logging
import random
from dataclasses import dataclass
from typing import AsyncIterator, Awaitable, Callable, Optional, Tuple, TypeVar

T = TypeVar("T")
logger = logging.getLogger(__name__)


@dataclass
class RetryPolicy:
    """Controls retry/backoff behaviour for retry_async.

    Attributes:
        max_attempts: maximum number of attempts (including the first)
        base_delay: initial delay in seconds
        factor: multiplicative backoff factor
        max_delay: maximum delay between attempts
        jitter: fraction [0.0, 1.0) to randomize delay
    """

    max_attempts: int = 3
    base_delay: float = 0.1
    factor: float = 2.0
    max_delay: float = 10.0
    jitter: float = 0.1

    def __post_init__(self) -> None:
        if self.max_attempts < 1:
            raise ValueError("max_attempts must be >= 1")
        if self.base_delay < 0:
            raise ValueError("base_delay must be >= 0")
        if not (0 <= self.jitter < 1):
            raise ValueError("jitter must be in [0, 1)")


async def retry_async(
    fn: Callable[[], Awaitable[T]], policy: Optional[RetryPolicy] = None
) -> T:
    """Call an async factory repeatedly until it succeeds or attempts exhausted.

    The provided callable is invoked anew for each attempt. On exception, the
    function will sleep according to the RetryPolicy and try again. The last
    exception will be propagated if attempts run out.
    """

    policy = policy or RetryPolicy()
    attempt = 0
    last_exc: Optional[BaseException] = None

    while attempt < policy.max_attempts:
        try:
            return await fn()
        except Exception as exc:  # pylint: disable=broad-except
            attempt += 1
            last_exc = exc
            if attempt >= policy.max_attempts:
                break
            # compute backoff with jitter
            delay = min(policy.base_delay * (policy.factor ** (attempt - 1)), policy.max_delay)
            jitter_amount = delay * policy.jitter * (random.random() * 2 - 1)
            sleep_for = max(0.0, delay + jitter_amount)
            logger.debug(
                "Retry attempt %d/%d failed (%s); sleeping %.3fs before retry",
                attempt,
                policy.max_attempts,
                exc,
                sleep_for,
            )
            await asyncio.sleep(sleep_for)

    assert last_exc is not None
    raise last_exc


class Channel(abc.ABC):
    """Abstract communication channel.

    Subclasses implement publish() and subscribe(). The base class provides
    small helpers around ack/nack semantics and a run_consumer helper that
    drives message processing and performs ack/nack automatically.

    publish should return a message identifier (string) if the underlying
    transport provides one; implementations may also return an empty string or
    None-compatible value if not applicable.
    """

    @abc.abstractmethod
    async def publish(self, message: str) -> Optional[str]:
        """Publish a message to the channel.

        Implementations should return a message identifier when available.
        """

    @abc.abstractmethod
    async def subscribe(self) -> AsyncIterator[Tuple[str, str]]:
        """Subscribe to messages from the channel.

        The iterator yields (message_id, message) tuples. Implementations must
        ensure the iterator is cancellable and respects caller cancellation.
        """

    async def ack(self, message_id: str) -> None:
        """Acknowledge successful processing of a message.

        Default implementation does nothing. Subclasses that support
        acknowledgements should override this method.
        """

    async def nack(self, message_id: str, requeue: bool = True) -> None:
        """Indicate that processing failed for the given message.

        Default implementation logs a warning. Subclasses may override to
        implement explicit negative-acknowledge/requeue semantics.
        """
        logger.warning("nack called for message_id=%s requeue=%s", message_id, requeue)

    async def run_consumer(
        self,
        handler: Callable[[str], Awaitable[None]],
        stop_event: Optional[asyncio.Event] = None,
    ) -> None:
        """Consume messages from subscribe() and call handler for each.

        This helper will: for each (message_id, message) yielded by subscribe(),
        call handler(message). On success it calls ack(message_id). On
        exception it calls nack(message_id, requeue=True). The loop stops when
        stop_event is set (if provided) or when the subscribe iterator ends.
        """

        stop_event = stop_event or asyncio.Event()

        async for message_id, message in self.subscribe():
            if stop_event.is_set():
                logger.debug("stop_event set; breaking consumer loop")
                break
            try:
                await handler(message)
            except asyncio.CancelledError:
                # propagate cancellation promptly
                raise
            except Exception as exc:  # pylint: disable=broad-except
                logger.exception("Handler failed for message_id=%s: %s", message_id, exc)
                try:
                    await self.nack(message_id, requeue=True)
                except Exception:
                    logger.exception("nack failed for message_id=%s", message_id)
            else:
                try:
                    await self.ack(message_id)
                except Exception:
                    logger.exception("ack failed for message_id=%s", message_id)


__all__ = ["Channel", "retry_async", "RetryPolicy"]

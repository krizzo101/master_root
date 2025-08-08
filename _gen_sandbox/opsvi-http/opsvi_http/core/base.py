"""opsvi-http - Core opsvi-http functionality.

Comprehensive opsvi-http library for the OPSVI ecosystem
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Dict, Iterable, List, Optional, Set
import asyncio
import logging
import time

from opsvi_foundation import BaseComponent, ComponentError
from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)


class OpsviHttpManagerError(ComponentError):
    """Base exception for opsvi-http errors."""
    pass


class OpsviHttpManagerConfigurationError(OpsviHttpManagerError):
    """Configuration-related errors in opsvi-http."""
    pass


class OpsviHttpManagerInitializationError(OpsviHttpManagerError):
    """Initialization-related errors in opsvi-http."""
    pass


@dataclass(frozen=True)
class HttpRequest:
    """Simple HTTP request container."""

    method: str
    url: str
    headers: Optional[Dict[str, str]] = None
    body: Optional[bytes] = None
    timeout: Optional[float] = None


@dataclass
class HttpResponse:
    """Simple HTTP response container."""

    status: int
    headers: Dict[str, str]
    body: bytes
    duration: float


AsyncHttpSender = Callable[[HttpRequest], Awaitable[HttpResponse]]


class OpsviHttpManagerConfig(BaseSettings):
    """Configuration for opsvi-http."""

    # Core configuration
    enabled: bool = True
    debug: bool = False
    log_level: str = "INFO"

    # Concurrency and retry
    concurrency: int = 10
    request_timeout: float = 30.0
    retry_attempts: int = 3
    retry_backoff_base: float = 0.25
    retry_backoff_max: float = 4.0
    retry_status_codes: List[int] = [429, 500, 502, 503, 504]

    class Config:
        env_prefix = "OPSVI_OPSVI_HTTP__"


class OpsviHttpManager(BaseComponent):
    """Base class for opsvi-http components with async request orchestration."""

    def __init__(
        self,
        config: Optional[OpsviHttpManagerConfig] = None,
        **kwargs: Any,
    ) -> None:
        super().__init__("opsvi-http", config.dict() if config else kwargs)
        self.config = config or OpsviHttpManagerConfig(**kwargs)
        self._initialized: bool = False
        self._logger = logging.getLogger(f"{__name__}.opsvi-http")

        self._sem: Optional[asyncio.Semaphore] = None
        self._pending: Set[asyncio.Task[Any]] = set()
        self._senders: Dict[str, AsyncHttpSender] = {}
        self._default_sender: Optional[str] = None

        # Simple in-memory metrics
        self._successful_requests: int = 0
        self._failed_requests: int = 0

    async def initialize(self) -> None:
        """Initialize the manager and internal resources."""
        try:
            self._configure_logging()
            self._logger.info("Initializing opsvi-http")

            if not self.config.enabled:
                self._logger.warning("opsvi-http disabled by configuration")

            if self.config.concurrency < 1:
                raise OpsviHttpManagerConfigurationError("concurrency must be >= 1")

            self._sem = asyncio.Semaphore(self.config.concurrency)
            self._register_builtin_senders()

            self._initialized = True
            self._logger.info("opsvi-http initialized successfully")
        except Exception as e:  # pragma: no cover
            self._logger.error(f"Failed to initialize opsvi-http: {e}")
            raise OpsviHttpManagerInitializationError(f"Initialization failed: {e}") from e

    async def shutdown(self) -> None:
        """Shutdown the component and cancel pending tasks."""
        try:
            self._logger.info("Shutting down opsvi-http")
            self._initialized = False

            # Cancel and await pending tasks
            pending = list(self._pending)
            for t in pending:
                t.cancel()
            if pending:
                with contextlib.suppress(Exception):
                    await asyncio.gather(*pending, return_exceptions=True)

            self._pending.clear()
            self._sem = None
            self._logger.info("opsvi-http shut down successfully")
        except Exception as e:  # pragma: no cover
            self._logger.error(f"Failed to shutdown opsvi-http: {e}")
            raise OpsviHttpManagerError(f"Shutdown failed: {e}") from e

    async def health_check(self) -> bool:
        """Return True when initialized and basic primitives are healthy."""
        try:
            if not self._initialized or self._sem is None:
                return False
            # Ensure semaphore is usable
            if not await self._try_acquire_release(self._sem):
                return False
            return True
        except Exception as e:  # pragma: no cover
            self._logger.error(f"Health check failed: {e}")
            return False

    # Public API

    def register_sender(self, name: str, sender: AsyncHttpSender, *, default: bool = False) -> None:
        """Register an async sender function by name."""
        if not name:
            raise ValueError("sender name must be non-empty")
        self._senders[name] = sender
        if default or self._default_sender is None:
            self._default_sender = name

    def get_sender(self, name: Optional[str] = None) -> AsyncHttpSender:
        """Return a sender by name or the default sender."""
        key = name or self._default_sender
        if not key or key not in self._senders:
            raise OpsviHttpManagerError("No sender registered")
        return self._senders[key]

    async def execute(self, request: HttpRequest, *, sender: Optional[str] = None) -> HttpResponse:
        """Execute a single request with retries and timeout."""
        self._ensure_ready()
        assert self._sem is not None  # for type checkers

        send = self.get_sender(sender)
        async with _AsyncAcquire(self._sem):
            return await self._execute_with_retry(send, request)

    async def batch_execute(
        self, requests: Iterable[HttpRequest], *, sender: Optional[str] = None
    ) -> List[HttpResponse]:
        """Execute multiple requests concurrently respecting concurrency limits."""
        self._ensure_ready()
        send = self.get_sender(sender)
        tasks: List[asyncio.Task[HttpResponse]] = []
        for req in requests:
            tasks.append(asyncio.create_task(self.execute(req, sender=sender)))
            self._pending.add(tasks[-1])
            tasks[-1].add_done_callback(self._pending.discard)
        results = await asyncio.gather(*tasks)
        return list(results)

    def get_metrics(self) -> Dict[str, int]:
        """Return simple counters for success/failure."""
        return {
            "successful_requests": self._successful_requests,
            "failed_requests": self._failed_requests,
            "pending_tasks": len(self._pending),
        }

    # Internals

    def _configure_logging(self) -> None:
        level = logging.DEBUG if self.config.debug else getattr(logging, self.config.log_level.upper(), logging.INFO)
        self._logger.setLevel(level)
        logger.setLevel(level)

    def _register_builtin_senders(self) -> None:
        # Lightweight local sender useful for tests; does not hit the network.
        async def local_sender(req: HttpRequest) -> HttpResponse:
            start = time.perf_counter()
            if req.url.startswith("echo:"):
                msg = req.url[len("echo:") :].encode()
                return HttpResponse(status=200, headers={"content-type": "text/plain"}, body=msg, duration=time.perf_counter() - start)
            return HttpResponse(status=501, headers={}, body=b"sender not implemented", duration=time.perf_counter() - start)

        self.register_sender("local", local_sender, default=True)

    def _ensure_ready(self) -> None:
        if not self._initialized:
            raise OpsviHttpManagerError("Manager not initialized")
        if self._sem is None:
            raise OpsviHttpManagerError("Concurrency control not configured")

    async def _execute_with_retry(self, send: AsyncHttpSender, request: HttpRequest) -> HttpResponse:
        attempts = max(1, int(self.config.retry_attempts))
        base = max(0.0, float(self.config.retry_backoff_base))
        backoff_max = max(base, float(self.config.retry_backoff_max))
        timeout = float(request.timeout or self.config.request_timeout)
        last_exc: Optional[BaseException] = None

        for attempt in range(1, attempts + 1):
            try:
                start = time.perf_counter()
                resp = await asyncio.wait_for(send(request), timeout=timeout)
                resp.duration = time.perf_counter() - start
                if resp.status in self.config.retry_status_codes and attempt < attempts:
                    await asyncio.sleep(min(backoff_max, base * (2 ** (attempt - 1))))
                    continue
                self._successful_requests += 1 if resp.status < 400 else 0
                self._failed_requests += 1 if resp.status >= 400 else 0
                return resp
            except asyncio.CancelledError:
                self._failed_requests += 1
                raise
            except Exception as exc:
                last_exc = exc
                if attempt >= attempts:
                    self._failed_requests += 1
                    raise OpsviHttpManagerError(f"Request failed after {attempts} attempts: {exc}") from exc
                await asyncio.sleep(min(backoff_max, base * (2 ** (attempt - 1))))
        # Should not reach here
        if last_exc:
            raise OpsviHttpManagerError("Request failed") from last_exc
        raise OpsviHttpManagerError("Request failed with unknown error")

    async def _try_acquire_release(self, sem: asyncio.Semaphore) -> bool:
        try:
            if not sem.locked():
                # Fast-path if permit available
                sem.release()
                sem.acquire_nowait()
            # Fallback to timed acquire
        except ValueError:
            # semaphore over-release guard; do timed acquire instead
            pass
        try:
            if await asyncio.wait_for(sem.acquire(), timeout=0.1):
                sem.release()
                return True
            return False
        except Exception:
            return False

    async def __aenter__(self) -> "OpsviHttpManager":
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.shutdown()


# Helpers
import contextlib


class _AsyncAcquire:
    """Async context manager to acquire and release a semaphore."""

    def __init__(self, sem: asyncio.Semaphore) -> None:
        self._sem = sem

    async def __aenter__(self) -> None:
        await self._sem.acquire()

    async def __aexit__(self, exc_type, exc, tb) -> None:
        self._sem.release()

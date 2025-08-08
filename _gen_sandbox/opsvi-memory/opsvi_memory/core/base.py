"""opsvi-memory - Core opsvi-memory functionality.

Comprehensive opsvi-memory library for the OPSVI ecosystem
"""

from __future__ import annotations

from abc import ABC
from dataclasses import dataclass
from time import monotonic
from typing import Any, Dict, List, Optional
import asyncio
import logging

from opsvi_foundation import BaseComponent, ComponentError
from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)


class OpsviMemoryManagerError(ComponentError):
    """Base exception for opsvi-memory errors."""


class OpsviMemoryManagerConfigurationError(OpsviMemoryManagerError):
    """Configuration-related errors in opsvi-memory."""


class OpsviMemoryManagerInitializationError(OpsviMemoryManagerError):
    """Initialization-related errors in opsvi-memory."""


class OpsviMemoryManagerConfig(BaseSettings):
    """Configuration for opsvi-memory."""

    # Core configuration
    enabled: bool = True
    debug: bool = False
    log_level: str = "INFO"

    # In-memory store configuration
    capacity: int = 10000
    default_ttl_seconds: Optional[float] = None
    eviction_policy: str = "lru"  # one of: "lru", "none"
    sweep_interval_seconds: float = 2.0
    healthcheck_timeout_seconds: float = 0.5

    class Config:
        env_prefix = "OPSVI_OPSVI_MEMORY__"


@dataclass
class _Record:
    value: Any
    expires_at: Optional[float]
    last_access: float

    def expired(self, now: Optional[float] = None) -> bool:
        if self.expires_at is None:
            return False
        if now is None:
            now = monotonic()
        return now >= self.expires_at


class OpsviMemoryManager(BaseComponent):
    """Base class for opsvi-memory components.

    Provides base functionality for all opsvi-memory components.
    Implements an async, in-memory key-value store with TTL and optional LRU eviction.
    """

    def __init__(
        self,
        config: Optional[OpsviMemoryManagerConfig] = None,
        **kwargs: Any
    ) -> None:
        """Initialize OpsviMemoryManager.

        Args:
            config: Configuration for the component
            **kwargs: Additional configuration parameters
        """
        super().__init__("opsvi-memory", config.dict() if config else {})
        self.config = config or OpsviMemoryManagerConfig(**kwargs)
        self._initialized: bool = False
        self._logger = logging.getLogger(f"{__name__}.opsvi-memory")
        self._store: Dict[str, _Record] = {}
        self._lock: asyncio.Lock = asyncio.Lock()
        self._gc_task: Optional[asyncio.Task[None]] = None

    async def initialize(self) -> None:
        """Initialize the component."""
        try:
            self._configure_logging()
            self._logger.info("Initializing opsvi-memory")

            if self.config.capacity <= 0:
                raise OpsviMemoryManagerConfigurationError("capacity must be > 0")
            if self.config.eviction_policy not in {"lru", "none"}:
                raise OpsviMemoryManagerConfigurationError(
                    "eviction_policy must be one of: 'lru', 'none'"
                )

            if not self.config.enabled:
                self._logger.warning("opsvi-memory is disabled by configuration")
                self._initialized = True
                return

            # Start background GC for TTL cleanup
            if self.config.sweep_interval_seconds > 0:
                self._gc_task = asyncio.create_task(self._gc_loop(), name="opsvi-memory-gc")

            self._initialized = True
            self._logger.info("opsvi-memory initialized successfully")

        except Exception as e:  # noqa: BLE001
            self._logger.error(f"Failed to initialize opsvi-memory: {e}")
            raise OpsviMemoryManagerInitializationError(f"Initialization failed: {e}") from e

    async def shutdown(self) -> None:
        """Shutdown the component."""
        try:
            self._logger.info("Shutting down opsvi-memory")
            if self._gc_task is not None:
                self._gc_task.cancel()
                try:
                    await self._gc_task
                except asyncio.CancelledError:
                    pass
                finally:
                    self._gc_task = None

            async with self._lock:
                self._store.clear()

            self._initialized = False
            self._logger.info("opsvi-memory shut down successfully")

        except Exception as e:  # noqa: BLE001
            self._logger.error(f"Failed to shutdown opsvi-memory: {e}")
            raise OpsviMemoryManagerError(f"Shutdown failed: {e}") from e

    async def health_check(self) -> bool:
        """Perform health check."""
        if not self._initialized:
            return False
        try:
            async def _noop() -> None:
                async with self._lock:
                    return None

            await asyncio.wait_for(_noop(), timeout=self.config.healthcheck_timeout_seconds)
            return True
        except Exception:  # noqa: BLE001
            self._logger.exception("Health check failed")
            return False

    # Public API
    async def set(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        """Store a value with optional TTL in seconds."""
        self._require_initialized()
        ttl = self.config.default_ttl_seconds if ttl is None else ttl
        now = monotonic()
        exp = (now + ttl) if ttl and ttl > 0 else None
        async with self._lock:
            await self._evict_if_needed_locked()
            self._store[key] = _Record(value=value, expires_at=exp, last_access=now)

    async def get(self, key: str, default: Any = None) -> Any:
        """Get a value, returning default if missing or expired."""
        self._require_initialized()
        now = monotonic()
        async with self._lock:
            rec = self._store.get(key)
            if rec is None:
                return default
            if rec.expired(now):
                self._store.pop(key, None)
                return default
            rec.last_access = now
            return rec.value

    async def delete(self, key: str) -> bool:
        """Delete a key if it exists."""
        self._require_initialized()
        async with self._lock:
            return self._store.pop(key, None) is not None

    async def exists(self, key: str) -> bool:
        """Check if a key exists and is not expired."""
        self._require_initialized()
        now = monotonic()
        async with self._lock:
            rec = self._store.get(key)
            if rec is None:
                return False
            if rec.expired(now):
                self._store.pop(key, None)
                return False
            return True

    async def touch(self, key: str, ttl: Optional[float] = None) -> bool:
        """Refresh TTL for a key. If ttl is None, uses default."""
        self._require_initialized()
        ttl = self.config.default_ttl_seconds if ttl is None else ttl
        now = monotonic()
        async with self._lock:
            rec = self._store.get(key)
            if rec is None or rec.expired(now):
                if rec is not None and rec.expired(now):
                    self._store.pop(key, None)
                return False
            rec.last_access = now
            rec.expires_at = (now + ttl) if ttl and ttl > 0 else None
            return True

    async def keys(self, prefix: Optional[str] = None) -> List[str]:
        """List keys, optionally filtered by prefix."""
        self._require_initialized()
        now = monotonic()
        async with self._lock:
            self._purge_expired_locked(now)
            if prefix is None:
                return list(self._store.keys())
            return [k for k in self._store.keys() if k.startswith(prefix)]

    async def clear(self, prefix: Optional[str] = None) -> int:
        """Clear all keys or those matching a prefix. Returns count of removed keys."""
        self._require_initialized()
        async with self._lock:
            if prefix is None:
                count = len(self._store)
                self._store.clear()
                return count
            to_delete = [k for k in self._store.keys() if k.startswith(prefix)]
            for k in to_delete:
                self._store.pop(k, None)
            return len(to_delete)

    async def size(self) -> int:
        """Number of non-expired keys currently stored."""
        self._require_initialized()
        now = monotonic()
        async with self._lock:
            self._purge_expired_locked(now)
            return len(self._store)

    async def capacity(self) -> int:
        """Maximum capacity of the store."""
        return self.config.capacity

    # Internal helpers
    def _configure_logging(self) -> None:
        level_name = "DEBUG" if self.config.debug else self.config.log_level
        level = getattr(logging, level_name.upper(), logging.INFO)
        self._logger.setLevel(level)

    def _require_initialized(self) -> None:
        if not self._initialized:
            raise OpsviMemoryManagerInitializationError("Component not initialized")

    def _purge_expired_locked(self, now: Optional[float] = None) -> None:
        if now is None:
            now = monotonic()
        expired_keys = [k for k, v in self._store.items() if v.expired(now)]
        for k in expired_keys:
            self._store.pop(k, None)

    async def _evict_if_needed_locked(self) -> None:
        if len(self._store) < self.config.capacity:
            return
        if self.config.eviction_policy == "none":
            raise OpsviMemoryManagerError("Capacity reached and eviction_policy='none'")
        # LRU eviction
        while len(self._store) >= self.config.capacity:
            # Find least recently used, ignoring already expired entries first
            now = monotonic()
            self._purge_expired_locked(now)
            if not self._store:
                break
            lru_key = min(self._store.items(), key=lambda kv: kv[1].last_access)[0]
            self._store.pop(lru_key, None)

    async def _gc_loop(self) -> None:
        try:
            while True:
                await asyncio.sleep(self.config.sweep_interval_seconds)
                async with self._lock:
                    self._purge_expired_locked()
        except asyncio.CancelledError:
            return
        except Exception:  # noqa: BLE001
            self._logger.exception("GC loop encountered an error")


# End of module

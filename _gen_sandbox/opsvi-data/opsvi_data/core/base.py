"""opsvi-data - Core opsvi-data functionality.

Comprehensive opsvi-data library for the OPSVI ecosystem
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple
import asyncio
import logging
import time

from opsvi_foundation import BaseComponent, ComponentError
from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)


class OpsviDataManagerError(ComponentError):
    """Base exception for opsvi-data errors."""


class OpsviDataManagerConfigurationError(OpsviDataManagerError):
    """Configuration-related errors in opsvi-data."""


class OpsviDataManagerInitializationError(OpsviDataManagerError):
    """Initialization-related errors in opsvi-data."""


class OpsviDataManagerConfig(BaseSettings):
    """Configuration for opsvi-data."""

    # Core configuration
    enabled: bool = True
    debug: bool = False
    log_level: str = "INFO"

    # In-memory store configuration
    default_ttl_seconds: Optional[float] = None
    cleanup_interval_seconds: float = 30.0
    max_items: Optional[int] = None

    class Config:
        env_prefix = "OPSVI_OPSVI_DATA__"


class OpsviDataManager(BaseComponent):
    """Base class for opsvi-data components.

    Provides a simple async in-memory key-value store with optional TTL.
    """

    def __init__(
        self,
        config: Optional[OpsviDataManagerConfig] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize OpsviDataManager.

        Args:
            config: Configuration for the component
            **kwargs: Additional configuration parameters
        """
        super().__init__("opsvi-data", config.dict() if config else {})
        self.config = config or OpsviDataManagerConfig(**kwargs)
        self._initialized: bool = False
        self._logger = logging.getLogger(f"{__name__}.opsvi-data")

        # Internal state
        self._store: Dict[str, Tuple[Any, Optional[float]]] = {}
        self._lock = asyncio.Lock()
        self._janitor_task: Optional[asyncio.Task[None]] = None

    async def initialize(self) -> None:
        """Initialize the component."""
        try:
            # Configure logging
            level_name = "DEBUG" if self.config.debug else self.config.log_level
            level = getattr(logging, level_name.upper(), logging.INFO)
            self._logger.setLevel(level)
            self._logger.info("Initializing opsvi-data")

            if self.config.cleanup_interval_seconds < 0:
                raise OpsviDataManagerConfigurationError(
                    "cleanup_interval_seconds must be >= 0"
                )
            if self.config.max_items is not None and self.config.max_items <= 0:
                raise OpsviDataManagerConfigurationError(
                    "max_items must be positive when provided"
                )

            self._initialized = True

            # Start background janitor for TTL cleanup if enabled
            if self.config.cleanup_interval_seconds > 0 and self.config.enabled:
                self._janitor_task = asyncio.create_task(self._janitor(), name="opsvi-data-janitor")

            self._logger.info("opsvi-data initialized successfully")

        except Exception as e:
            self._logger.error(f"Failed to initialize opsvi-data: {e}")
            raise OpsviDataManagerInitializationError(f"Initialization failed: {e}") from e

    async def shutdown(self) -> None:
        """Shutdown the component."""
        try:
            self._logger.info("Shutting down opsvi-data")
            # Stop janitor task
            if self._janitor_task is not None:
                self._janitor_task.cancel()
                try:
                    await self._janitor_task
                except asyncio.CancelledError:
                    pass
                finally:
                    self._janitor_task = None

            async with self._lock:
                self._store.clear()

            self._initialized = False
            self._logger.info("opsvi-data shut down successfully")

        except Exception as e:
            self._logger.error(f"Failed to shutdown opsvi-data: {e}")
            raise OpsviDataManagerError(f"Shutdown failed: {e}") from e

    async def health_check(self) -> bool:
        """Perform health check."""
        try:
            if not self._initialized:
                return False
            if self._janitor_task is not None and self._janitor_task.done():
                # If the janitor task crashed report unhealthy
                exc = self._janitor_task.exception()
                if exc:
                    self._logger.error(f"Janitor task failed: {exc}")
                    return False
            # Try acquiring/releasing lock to verify loop liveness
            async with self._lock:
                _ = len(self._store)
            return True
        except Exception as e:
            self._logger.error(f"Health check failed: {e}")
            return False

    # Public API

    async def set(self, key: str, value: Any, *, ttl: Optional[float] = None) -> None:
        """Store a value under key with optional TTL in seconds."""
        self._ensure_ready()
        if not key:
            raise OpsviDataManagerError("Key must be a non-empty string")
        if ttl is None:
            ttl = self.config.default_ttl_seconds
        expires_at = (time.monotonic() + ttl) if ttl and ttl > 0 else None
        async with self._lock:
            if self.config.max_items is not None and key not in self._store:
                if len(self._store) >= self.config.max_items:
                    raise OpsviDataManagerError("Store capacity exceeded")
            self._store[key] = (value, expires_at)

    async def get(self, key: str, *, default: Any = None) -> Any:
        """Get a value by key; returns default if not found or expired."""
        self._ensure_ready()
        async with self._lock:
            item = self._store.get(key)
            if item is None:
                return default
            value, expires_at = item
            if expires_at is not None and time.monotonic() >= expires_at:
                # expire lazily
                self._store.pop(key, None)
                return default
            return value

    async def delete(self, key: str) -> bool:
        """Delete a key if present."""
        self._ensure_ready()
        async with self._lock:
            return self._store.pop(key, None) is not None

    async def exists(self, key: str) -> bool:
        """Check if a key exists and is not expired."""
        self._ensure_ready()
        async with self._lock:
            item = self._store.get(key)
            if item is None:
                return False
            _, expires_at = item
            if expires_at is not None and time.monotonic() >= expires_at:
                self._store.pop(key, None)
                return False
            return True

    async def keys(self, prefix: Optional[str] = None) -> List[str]:
        """List keys, optionally filtered by prefix, excluding expired."""
        self._ensure_ready()
        now = time.monotonic()
        async with self._lock:
            result: List[str] = []
            expired: List[str] = []
            for k, (_, exp) in self._store.items():
                if exp is not None and now >= exp:
                    expired.append(k)
                    continue
                if prefix is None or k.startswith(prefix):
                    result.append(k)
            for k in expired:
                self._store.pop(k, None)
            return result

    async def clear(self) -> int:
        """Clear all items. Returns number of removed entries."""
        self._ensure_ready()
        async with self._lock:
            n = len(self._store)
            self._store.clear()
            return n

    async def stats(self) -> Dict[str, Any]:
        """Return store statistics."""
        async with self._lock:
            now = time.monotonic()
            active = sum(1 for _, exp in self._store.values() if not (exp is not None and now >= exp))
            return {
                "initialized": self._initialized,
                "enabled": self.config.enabled,
                "items": len(self._store),
                "active_items": active,
                "max_items": self.config.max_items,
                "cleanup_interval_seconds": self.config.cleanup_interval_seconds,
                "default_ttl_seconds": self.config.default_ttl_seconds,
                "janitor_running": self._janitor_task is not None and not self._janitor_task.done(),
            }

    # Internal helpers

    def _ensure_ready(self) -> None:
        if not self._initialized:
            raise OpsviDataManagerError("Component not initialized")
        if not self.config.enabled:
            raise OpsviDataManagerError("Component is disabled")

    async def _janitor(self) -> None:
        """Background task that cleans up expired entries."""
        try:
            interval = max(0.1, float(self.config.cleanup_interval_seconds))
            while self._initialized and self.config.enabled:
                await asyncio.sleep(interval)
                await self._cleanup_expired()
        except asyncio.CancelledError:
            # Graceful cancellation
            return
        except Exception as e:
            self._logger.exception(f"Janitor task encountered an error: {e}")

    async def _cleanup_expired(self) -> int:
        now = time.monotonic()
        async with self._lock:
            expired = [k for k, (_, exp) in self._store.items() if exp is not None and now >= exp]
            for k in expired:
                self._store.pop(k, None)
            if expired:
                self._logger.debug("Cleaned up %d expired entries", len(expired))
            return len(expired)

"""In-memory persistence backend."""

import logging
from typing import Any, Dict, List, Optional
from threading import Lock
import copy

from .base import PersistenceBackend

logger = logging.getLogger(__name__)


class MemoryBackend(PersistenceBackend):
    """In-memory persistence backend.
    
    This backend stores data in memory only and will lose all data
    when the process exits. Useful for testing and temporary storage.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize memory backend.

        Args:
            config: Optional configuration
        """
        super().__init__(config)
        self._data: Dict[str, Any] = {}
        self._lock = Lock()
        self.max_size = self.config.get("max_size", None)  # Optional size limit

    async def _initialize_impl(self) -> None:
        """Initialize memory backend."""
        logger.info(f"Initialized memory backend (max_size: {self.max_size})")

    async def _shutdown_impl(self) -> None:
        """Shutdown memory backend."""
        with self._lock:
            entries = len(self._data)
            self._data.clear()
        logger.info(f"Cleared {entries} entries from memory")

    def _check_size(self) -> None:
        """Check and enforce size limit."""
        if self.max_size and len(self._data) > self.max_size:
            # Simple FIFO eviction
            to_remove = len(self._data) - self.max_size
            keys_to_remove = list(self._data.keys())[:to_remove]
            for key in keys_to_remove:
                del self._data[key]
            logger.warning(f"Evicted {to_remove} entries due to size limit")

    async def get(self, key: str, default: Any = None) -> Any:
        """Get value by key."""
        with self._lock:
            value = self._data.get(key, default)
            # Deep copy to prevent external modifications
            if value is not None and not isinstance(value, (str, int, float, bool)):
                return copy.deepcopy(value)
            return value

    async def set(self, key: str, value: Any) -> None:
        """Set value by key."""
        with self._lock:
            # Deep copy to prevent external modifications
            if value is not None and not isinstance(value, (str, int, float, bool)):
                value = copy.deepcopy(value)
            self._data[key] = value
            self._check_size()

    async def delete(self, key: str) -> bool:
        """Delete value by key."""
        with self._lock:
            if key in self._data:
                del self._data[key]
                return True
            return False

    async def exists(self, key: str) -> bool:
        """Check if key exists."""
        with self._lock:
            return key in self._data

    async def keys(self, pattern: Optional[str] = None) -> List[str]:
        """Get all keys matching pattern."""
        with self._lock:
            all_keys = list(self._data.keys())
        
        if pattern:
            # Simple wildcard matching
            import fnmatch
            return [k for k in all_keys if fnmatch.fnmatch(k, pattern)]
        return all_keys

    async def clear(self) -> None:
        """Clear all stored data."""
        with self._lock:
            self._data.clear()
        logger.info("Cleared all data from memory")

    async def get_all(self) -> Dict[str, Any]:
        """Get all key-value pairs."""
        with self._lock:
            # Deep copy to prevent external modifications
            return copy.deepcopy(self._data)

    async def set_many(self, data: Dict[str, Any]) -> None:
        """Set multiple key-value pairs."""
        with self._lock:
            for key, value in data.items():
                # Deep copy to prevent external modifications
                if value is not None and not isinstance(value, (str, int, float, bool)):
                    value = copy.deepcopy(value)
                self._data[key] = value
            self._check_size()

    def get_stats(self) -> Dict[str, Any]:
        """Get memory backend statistics."""
        with self._lock:
            import sys
            
            # Calculate approximate memory usage
            total_size = 0
            for key, value in self._data.items():
                total_size += sys.getsizeof(key) + sys.getsizeof(value)
            
            return {
                "entries": len(self._data),
                "max_size": self.max_size,
                "approx_memory_bytes": total_size,
                "approx_memory_mb": round(total_size / (1024 * 1024), 2),
            }

    async def snapshot(self) -> Dict[str, Any]:
        """Create a snapshot of current data."""
        return await self.get_all()

    async def restore_snapshot(self, snapshot: Dict[str, Any]) -> None:
        """Restore data from a snapshot."""
        with self._lock:
            self._data.clear()
            self._data.update(copy.deepcopy(snapshot))
            self._check_size()


__all__ = ["MemoryBackend"]
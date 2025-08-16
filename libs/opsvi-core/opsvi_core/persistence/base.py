"""Base persistence backend for opsvi-core.

Defines the abstract interface for persistence backends.
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from opsvi_foundation import ComponentError

logger = logging.getLogger(__name__)


class PersistenceError(ComponentError):
    """Persistence operation error."""

    pass


class PersistenceBackend(ABC):
    """Abstract base class for persistence backends."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize persistence backend.

        Args:
            config: Backend-specific configuration
        """
        self.config = config or {}
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize the backend.

        This should be called before using the backend.
        """
        if not self._initialized:
            await self._initialize_impl()
            self._initialized = True
            logger.info(f"Initialized {self.__class__.__name__} persistence backend")

    async def shutdown(self) -> None:
        """Shutdown the backend.

        This should be called when done using the backend.
        """
        if self._initialized:
            await self._shutdown_impl()
            self._initialized = False
            logger.info(f"Shutdown {self.__class__.__name__} persistence backend")

    @abstractmethod
    async def _initialize_impl(self) -> None:
        """Backend-specific initialization."""
        pass

    @abstractmethod
    async def _shutdown_impl(self) -> None:
        """Backend-specific shutdown."""
        pass

    @abstractmethod
    async def get(self, key: str, default: Any = None) -> Any:
        """Get value by key.

        Args:
            key: Key to retrieve
            default: Default value if not found

        Returns:
            Value or default
        """
        pass

    @abstractmethod
    async def set(self, key: str, value: Any) -> None:
        """Set value by key.

        Args:
            key: Key to set
            value: Value to store
        """
        pass

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete value by key.

        Args:
            key: Key to delete

        Returns:
            True if deleted, False if not found
        """
        pass

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if key exists.

        Args:
            key: Key to check

        Returns:
            True if exists
        """
        pass

    @abstractmethod
    async def keys(self, pattern: Optional[str] = None) -> List[str]:
        """Get all keys matching pattern.

        Args:
            pattern: Optional pattern to match (e.g., "user:*")

        Returns:
            List of matching keys
        """
        pass

    @abstractmethod
    async def clear(self) -> None:
        """Clear all stored data."""
        pass

    @abstractmethod
    async def get_all(self) -> Dict[str, Any]:
        """Get all key-value pairs.

        Returns:
            Dictionary of all stored data
        """
        pass

    @abstractmethod
    async def set_many(self, data: Dict[str, Any]) -> None:
        """Set multiple key-value pairs.

        Args:
            data: Dictionary of key-value pairs
        """
        pass

    async def get_many(self, keys: List[str]) -> Dict[str, Any]:
        """Get multiple values by keys.

        Args:
            keys: List of keys to retrieve

        Returns:
            Dictionary of key-value pairs
        """
        result = {}
        for key in keys:
            value = await self.get(key)
            if value is not None:
                result[key] = value
        return result

    async def delete_many(self, keys: List[str]) -> int:
        """Delete multiple keys.

        Args:
            keys: List of keys to delete

        Returns:
            Number of keys deleted
        """
        deleted = 0
        for key in keys:
            if await self.delete(key):
                deleted += 1
        return deleted

    async def backup(self, path: str) -> None:
        """Backup data to file.

        Args:
            path: Path to backup file
        """
        # Default implementation - can be overridden
        import json

        data = await self.get_all()
        with open(path, "w") as f:
            json.dump(data, f, indent=2, default=str)

    async def restore(self, path: str) -> None:
        """Restore data from file.

        Args:
            path: Path to backup file
        """
        # Default implementation - can be overridden
        import json

        with open(path, "r") as f:
            data = json.load(f)
        await self.clear()
        await self.set_many(data)

    async def health_check(self) -> bool:
        """Check if backend is healthy.

        Returns:
            True if healthy
        """
        try:
            # Try a simple operation
            test_key = "__health_check__"
            await self.set(test_key, "test")
            value = await self.get(test_key)
            await self.delete(test_key)
            return value == "test"
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False


__all__ = [
    "PersistenceBackend",
    "PersistenceError",
]

"""
Base storage infrastructure for OPSVI Core.

Provides abstract storage interfaces and common storage utilities.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from opsvi_foundation import BaseComponent, ComponentError, get_logger
from pydantic import BaseModel, Field

logger = get_logger(__name__)


class StorageError(ComponentError):
    """Raised when storage operations fail."""

    pass


class StorageConfig(BaseModel):
    """Base configuration for storage backends."""

    connection_timeout: float = Field(
        default=10.0, description="Connection timeout in seconds"
    )
    operation_timeout: float = Field(
        default=30.0, description="Operation timeout in seconds"
    )
    max_retries: int = Field(default=3, description="Maximum retry attempts")
    retry_delay: float = Field(
        default=1.0, description="Delay between retries in seconds"
    )


class StorageBackend(BaseComponent, ABC):
    """Abstract storage backend interface."""

    def __init__(self, config: StorageConfig):
        super().__init__()
        self.config = config

    @abstractmethod
    async def get(self, key: str) -> Any | None:
        """Get a value by key."""
        pass

    @abstractmethod
    async def set(self, key: str, value: Any) -> bool:
        """Set a value by key."""
        pass

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete a value by key."""
        pass

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if key exists."""
        pass

    @abstractmethod
    async def list_keys(self, prefix: str = "") -> list[str]:
        """List keys with optional prefix filter."""
        pass

    @abstractmethod
    async def clear(self) -> bool:
        """Clear all data."""
        pass

    @abstractmethod
    async def size(self) -> int:
        """Get total number of keys."""
        pass


class KeyValueStore(StorageBackend):
    """Base key-value storage implementation."""

    def __init__(self, config: StorageConfig):
        super().__init__(config)
        self._data: dict[str, Any] = {}

    async def get(self, key: str) -> Any | None:
        """Get a value by key."""
        return self._data.get(key)

    async def set(self, key: str, value: Any) -> bool:
        """Set a value by key."""
        try:
            self._data[key] = value
            return True
        except Exception as e:
            logger.error("Failed to set key %s: %s", key, e)
            return False

    async def delete(self, key: str) -> bool:
        """Delete a value by key."""
        try:
            if key in self._data:
                del self._data[key]
                return True
            return False
        except Exception as e:
            logger.error("Failed to delete key %s: %s", key, e)
            return False

    async def exists(self, key: str) -> bool:
        """Check if key exists."""
        return key in self._data

    async def list_keys(self, prefix: str = "") -> list[str]:
        """List keys with optional prefix filter."""
        if prefix:
            return [key for key in self._data.keys() if key.startswith(prefix)]
        return list(self._data.keys())

    async def clear(self) -> bool:
        """Clear all data."""
        try:
            self._data.clear()
            return True
        except Exception as e:
            logger.error("Failed to clear storage: %s", e)
            return False

    async def size(self) -> int:
        """Get total number of keys."""
        return len(self._data)


class StorageManager(BaseComponent):
    """Storage manager with multiple backend support."""

    def __init__(self, default_backend: StorageBackend):
        super().__init__()
        self.default_backend = default_backend
        self._backends: dict[str, StorageBackend] = {"default": default_backend}

    def add_backend(self, name: str, backend: StorageBackend) -> None:
        """Add a storage backend."""
        self._backends[name] = backend
        logger.info("Added storage backend: %s", name)

    def get_backend(self, name: str = "default") -> StorageBackend:
        """Get a storage backend by name."""
        return self._backends.get(name, self.default_backend)

    async def get(self, key: str, backend: str = "default") -> Any | None:
        """Get a value from storage."""
        storage = self.get_backend(backend)
        return await storage.get(key)

    async def set(self, key: str, value: Any, backend: str = "default") -> bool:
        """Set a value in storage."""
        storage = self.get_backend(backend)
        return await storage.set(key, value)

    async def delete(self, key: str, backend: str = "default") -> bool:
        """Delete a key from storage."""
        storage = self.get_backend(backend)
        return await storage.delete(key)

    async def exists(self, key: str, backend: str = "default") -> bool:
        """Check if a key exists in storage."""
        storage = self.get_backend(backend)
        return await storage.exists(key)

    async def list_keys(self, prefix: str = "", backend: str = "default") -> list[str]:
        """List keys from storage."""
        storage = self.get_backend(backend)
        return await storage.list_keys(prefix)

    async def clear(self, backend: str = "default") -> bool:
        """Clear storage."""
        storage = self.get_backend(backend)
        return await storage.clear()

    async def size(self, backend: str = "default") -> int:
        """Get storage size."""
        storage = self.get_backend(backend)
        return await storage.size()


class FileStorage(StorageBackend):
    """File-based storage implementation."""

    def __init__(self, config: StorageConfig, base_path: str = "./data"):
        super().__init__(config)
        self.base_path = base_path
        self._ensure_directory()

    def _ensure_directory(self) -> None:
        """Ensure storage directory exists."""
        import os

        os.makedirs(self.base_path, exist_ok=True)

    def _get_file_path(self, key: str) -> str:
        """Get file path for key."""
        import os

        # Sanitize key for filesystem
        safe_key = key.replace("/", "_").replace("\\", "_")
        return os.path.join(self.base_path, safe_key)

    async def get(self, key: str) -> Any | None:
        """Get a value by key from file."""
        import json
        import os

        file_path = self._get_file_path(key)
        if not os.path.exists(file_path):
            return None

        try:
            with open(file_path, encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error("Failed to read file %s: %s", file_path, e)
            return None

    async def set(self, key: str, value: Any) -> bool:
        """Set a value by key to file."""
        import json

        file_path = self._get_file_path(key)
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(value, f, indent=2)
            return True
        except Exception as e:
            logger.error("Failed to write file %s: %s", file_path, e)
            return False

    async def delete(self, key: str) -> bool:
        """Delete a file by key."""
        import os

        file_path = self._get_file_path(key)
        if not os.path.exists(file_path):
            return False

        try:
            os.remove(file_path)
            return True
        except Exception as e:
            logger.error("Failed to delete file %s: %s", file_path, e)
            return False

    async def exists(self, key: str) -> bool:
        """Check if file exists."""
        import os

        return os.path.exists(self._get_file_path(key))

    async def list_keys(self, prefix: str = "") -> list[str]:
        """List keys (files) with optional prefix filter."""
        import os

        if not os.path.exists(self.base_path):
            return []

        try:
            files = os.listdir(self.base_path)
            if prefix:
                files = [f for f in files if f.startswith(prefix)]
            return files
        except Exception as e:
            logger.error("Failed to list files: %s", e)
            return []

    async def clear(self) -> bool:
        """Clear all files."""
        import os
        import shutil

        try:
            if os.path.exists(self.base_path):
                shutil.rmtree(self.base_path)
            self._ensure_directory()
            return True
        except Exception as e:
            logger.error("Failed to clear storage: %s", e)
            return False

    async def size(self) -> int:
        """Get number of files."""
        import os

        if not os.path.exists(self.base_path):
            return 0

        try:
            return len(os.listdir(self.base_path))
        except Exception as e:
            logger.error("Failed to get storage size: %s", e)
            return 0

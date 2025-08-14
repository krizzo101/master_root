"""JSON file-based persistence backend."""

import asyncio
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
from threading import Lock

from .base import PersistenceBackend, PersistenceError

logger = logging.getLogger(__name__)


class JSONBackend(PersistenceBackend):
    """JSON file-based persistence backend."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize JSON backend.

        Args:
            config: Configuration with 'file_path' key
        """
        super().__init__(config)
        self.file_path = Path(self.config.get("file_path", "data.json"))
        self._data: Dict[str, Any] = {}
        self._lock = Lock()
        self._write_lock = asyncio.Lock()

    async def _initialize_impl(self) -> None:
        """Initialize JSON backend."""
        try:
            # Create directory if needed
            self.file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Load existing data
            if self.file_path.exists():
                with open(self.file_path, "r") as f:
                    self._data = json.load(f)
                logger.info(f"Loaded {len(self._data)} entries from {self.file_path}")
            else:
                self._data = {}
                await self._save()
                logger.info(f"Created new JSON store at {self.file_path}")
        except Exception as e:
            raise PersistenceError(f"Failed to initialize JSON backend: {e}")

    async def _shutdown_impl(self) -> None:
        """Shutdown JSON backend."""
        try:
            await self._save()
            logger.info(f"Saved data to {self.file_path}")
        except Exception as e:
            logger.error(f"Failed to save on shutdown: {e}")

    async def _save(self) -> None:
        """Save data to file."""
        async with self._write_lock:
            try:
                # Write to temp file first
                temp_path = self.file_path.with_suffix(".tmp")
                with open(temp_path, "w") as f:
                    json.dump(self._data, f, indent=2, default=str)
                
                # Atomic rename
                temp_path.replace(self.file_path)
            except Exception as e:
                raise PersistenceError(f"Failed to save data: {e}")

    async def get(self, key: str, default: Any = None) -> Any:
        """Get value by key."""
        with self._lock:
            return self._data.get(key, default)

    async def set(self, key: str, value: Any) -> None:
        """Set value by key."""
        with self._lock:
            self._data[key] = value
        
        # Auto-save if configured
        if self.config.get("auto_save", True):
            await self._save()

    async def delete(self, key: str) -> bool:
        """Delete value by key."""
        with self._lock:
            if key in self._data:
                del self._data[key]
                deleted = True
            else:
                deleted = False
        
        if deleted and self.config.get("auto_save", True):
            await self._save()
        
        return deleted

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
        
        if self.config.get("auto_save", True):
            await self._save()

    async def get_all(self) -> Dict[str, Any]:
        """Get all key-value pairs."""
        with self._lock:
            return self._data.copy()

    async def set_many(self, data: Dict[str, Any]) -> None:
        """Set multiple key-value pairs."""
        with self._lock:
            self._data.update(data)
        
        if self.config.get("auto_save", True):
            await self._save()

    async def compact(self) -> None:
        """Compact the JSON file by removing null values."""
        with self._lock:
            # Remove None values
            self._data = {k: v for k, v in self._data.items() if v is not None}
        
        await self._save()
        logger.info(f"Compacted JSON store to {len(self._data)} entries")


__all__ = ["JSONBackend"]
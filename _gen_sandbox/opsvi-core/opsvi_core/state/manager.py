"""State manager for opsvi-core.

Provides basic state persistence and synchronization.
"""

from typing import Any, Dict
import asyncio
import logging

from opsvi_core.core.base import OpsviCoreManager
from opsvi_core.config.settings import OpsviCoreConfig

logger = logging.getLogger(__name__)

class StateManager(OpsviCoreManager):
    """State management component."""

    def __init__(self, config: OpsviCoreConfig):
        super().__init__(config=config)
        self._state: Dict[str, Any] = {}
        self._lock = asyncio.Lock()

    async def get(self, key: str, default: Any = None) -> Any:
        async with self._lock:
            return self._state.get(key, default)

    async def set(self, key: str, value: Any) -> None:
        async with self._lock:
            self._state[key] = value
            logger.debug(f"State set: {key}")

    async def delete(self, key: str) -> None:
        async with self._lock:
            self._state.pop(key, None)
            logger.debug(f"State deleted: {key}")

    async def snapshot(self) -> Dict[str, Any]:
        async with self._lock:
            return dict(self._state)

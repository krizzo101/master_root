"""Event system foundation for opsvi-core.

Provides event handling and routing capabilities.
"""

from typing import Dict, List, Any, Callable
import asyncio
import logging

from opsvi_core.core.base import OpsviCoreManager
from opsvi_core.config.settings import OpsviCoreConfig
from opsvi_core.exceptions.base import OpsviCoreError

logger = logging.getLogger(__name__)

class Event:
    """Base event class."""
    def __init__(self, event_type: str, data: Dict[str, Any] | None = None):
        self.event_type = event_type
        self.data = data or {}
        self.timestamp = asyncio.get_event_loop().time()

class OpsviCoreEventManager(OpsviCoreManager):
    """Event manager for opsvi-core."""

    def __init__(self, config: OpsviCoreConfig):
        super().__init__(config=config)
        self.handlers: Dict[str, List[Callable]] = {}

    async def subscribe(self, event_type: str, handler: Callable) -> None:
        if event_type not in self.handlers:
            self.handlers[event_type] = []
        self.handlers[event_type].append(handler)

    async def publish(self, event: Event) -> None:
        handlers = self.handlers.get(event.event_type, [])
        for handler in handlers:
            try:
                await handler(event)
            except Exception as e:
                logger.error(f"Error in event handler: {e}")

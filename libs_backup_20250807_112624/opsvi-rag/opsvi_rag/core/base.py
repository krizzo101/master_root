"""
Base classes and interfaces for opsvi-rag.

Provides abstract base classes and common interfaces for all opsvi-rag components.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from opsvi_foundation.patterns.base import BaseComponent


class RagBase(BaseComponent, ABC):
    """Base class for all opsvi-rag components."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__()
        self.config = config or {}
    
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the component."""
        pass
    
    @abstractmethod
    async def shutdown(self) -> None:
        """Shutdown the component."""
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Perform health check."""
        pass

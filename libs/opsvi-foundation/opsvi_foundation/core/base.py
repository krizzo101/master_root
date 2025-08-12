"""Core opsvi-foundation functionality.

Comprehensive opsvi-foundation library for the OPSVI ecosystem
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import logging
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class ComponentError(Exception):
    """Base exception for component errors."""

    pass


class BaseComponent(ABC):
    """Base class for all OPSVI components.

    Provides base functionality for all components in the OPSVI ecosystem
    """

    def __init__(
        self, name: str, config: Optional[Dict[str, Any]] = None, **kwargs: Any
    ) -> None:
        """Initialize base component.

        Args:
            name: Component name
            config: Configuration dictionary
            **kwargs: Additional configuration parameters
        """
        self.name = name
        self.config = config or {}
        self.config.update(kwargs)
        self._initialized = False
        self._logger = logging.getLogger(f"{__name__}.{name}")

    async def initialize(self) -> None:
        """Initialize the component.

        Raises:
            ComponentError: If initialization fails
        """
        try:
            self._logger.info(f"Initializing {self.name}")
            await self._initialize_impl()
            self._initialized = True
            self._logger.info(f"{self.name} initialized successfully")
        except Exception as e:
            self._logger.error(f"Failed to initialize {self.name}: {e}")
            raise ComponentError(f"Initialization failed: {e}") from e

    async def shutdown(self) -> None:
        """Shutdown the component.

        Raises:
            ComponentError: If shutdown fails
        """
        try:
            self._logger.info(f"Shutting down {self.name}")
            await self._shutdown_impl()
            self._initialized = False
            self._logger.info(f"{self.name} shut down successfully")
        except Exception as e:
            self._logger.error(f"Failed to shutdown {self.name}: {e}")
            raise ComponentError(f"Shutdown failed: {e}") from e

    async def health_check(self) -> bool:
        """Perform health check.

        Returns:
            True if healthy, False otherwise
        """
        try:
            if not self._initialized:
                return False
            return await self._health_check_impl()
        except Exception as e:
            self._logger.error(f"Health check failed for {self.name}: {e}")
            return False

    @abstractmethod
    async def _initialize_impl(self) -> None:
        """Implementation-specific initialization."""
        pass

    @abstractmethod
    async def _shutdown_impl(self) -> None:
        """Implementation-specific shutdown."""
        pass

    @abstractmethod
    async def _health_check_impl(self) -> bool:
        """Implementation-specific health check."""
        pass


class BaseSettings(BaseModel):
    """Base settings for OPSVI components."""

    class Config:
        env_prefix = "OPSVI_"
        case_sensitive = False

"""RAG Core opsvi-rag functionality.

Comprehensive opsvi-rag library for the OPSVI ecosystem
"""

from abc import abstractmethod
from typing import Any, Optional
import logging

from opsvi_foundation import BaseComponent, ComponentError
from opsvi_foundation.config.settings import BaseSettings

logger = logging.getLogger(__name__)


class RAGError(ComponentError):
    """Base exception for RAG errors."""

    pass


class RAGConfigurationError(RAGError):
    """Configuration-related errors in RAG."""

    pass


class RAGInitializationError(RAGError):
    """Initialization-related errors in RAG."""

    pass


class RAGConfig(BaseSettings):
    """Configuration for RAG."""

    # Core configuration
    enabled: bool = True
    debug: bool = False
    log_level: str = "INFO"

    # Component-specific configuration
    vector_size: int = 1536
    default_distance: str = "Cosine"

    class Config:
        env_prefix = "OPSVI_RAG_"


class BaseRAGComponent(BaseComponent):
    """Base class for opsvi-rag components.

    Provides base functionality for all opsvi-rag components
    """

    def __init__(self, config: Optional[RAGConfig] = None, **kwargs: Any) -> None:
        """Initialize RAG component.

        Args:
            config: Configuration for the component
            **kwargs: Additional configuration parameters
        """
        super().__init__("rag-component", config.dict() if config else {})
        self.config = config or RAGConfig(**kwargs)
        self._initialized = False
        self._logger = logging.getLogger(f"{__name__}.rag")

        # Component-specific initialization
        self._vector_size = self.config.vector_size

    async def initialize(self) -> None:
        """Initialize the component.

        Raises:
            RAGInitializationError: If initialization fails
        """
        try:
            self._logger.info("Initializing RAG component")

            # Component-specific initialization logic
            await self._initialize_impl()

            self._initialized = True
            self._logger.info("RAG component initialized successfully")

        except Exception as e:
            self._logger.error(f"Failed to initialize RAG component: {e}")
            raise RAGInitializationError(f"Initialization failed: {e}") from e

    async def shutdown(self) -> None:
        """Shutdown the component.

        Raises:
            RAGError: If shutdown fails
        """
        try:
            self._logger.info("Shutting down RAG component")

            # Component-specific shutdown logic
            await self._shutdown_impl()

            self._initialized = False
            self._logger.info("RAG component shut down successfully")

        except Exception as e:
            self._logger.error(f"Failed to shutdown RAG component: {e}")
            raise RAGError(f"Shutdown failed: {e}") from e

    async def health_check(self) -> bool:
        """Perform health check.

        Returns:
            True if healthy, False otherwise
        """
        try:
            if not self._initialized:
                return False

            # Component-specific health check logic
            return await self._health_check_impl()

        except Exception as e:
            self._logger.error(f"Health check failed: {e}")
            return False

    # Abstract methods for subclasses to implement
    @abstractmethod
    async def _initialize_impl(self) -> None:
        """Initialize implementation."""
        pass

    @abstractmethod
    async def _shutdown_impl(self) -> None:
        """Shutdown implementation."""
        pass

    @abstractmethod
    async def _health_check_impl(self) -> bool:
        """Health check implementation."""
        pass

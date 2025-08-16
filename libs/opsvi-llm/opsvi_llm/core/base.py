"""Core opsvi-llm functionality.

Comprehensive opsvi-llm library for the OPSVI ecosystem
"""

import logging
from typing import Any, Optional

from opsvi_foundation import BaseComponent, ComponentError
from opsvi_foundation.config.settings import BaseSettings

logger = logging.getLogger(__name__)


class LLMError(ComponentError):
    """Base exception for LLM errors."""

    pass


class LLMConfigurationError(LLMError):
    """Configuration-related errors in LLM."""

    pass


class LLMInitializationError(LLMError):
    """Initialization-related errors in LLM."""

    pass


class LLMConfig(BaseSettings):
    """Configuration for LLM."""

    # Core configuration
    enabled: bool = True
    debug: bool = False
    log_level: str = "INFO"

    class Config:
        env_prefix = "OPSVI_LLM_"


class BaseLLMComponent(BaseComponent):
    """Base class for LLM components.

    Provides base functionality for all LLM components
    """

    def __init__(
        self, name: str, config: Optional[LLMConfig] = None, **kwargs: Any
    ) -> None:
        """Initialize LLM component.

        Args:
            name: Component name
            config: Configuration for the component
            **kwargs: Additional configuration parameters
        """
        super().__init__(name, config.model_dump() if config else {})
        self.llm_config = config or LLMConfig(**kwargs)
        self._logger = logging.getLogger(f"{__name__}.{name}")

    async def _initialize_impl(self) -> None:
        """Initialize the component."""
        self._logger.info(f"Initializing {self.name}")
        # Component-specific initialization logic
        self._logger.info(f"{self.name} initialized successfully")

    async def _shutdown_impl(self) -> None:
        """Shutdown the component."""
        self._logger.info(f"Shutting down {self.name}")
        # Component-specific shutdown logic
        self._logger.info(f"{self.name} shut down successfully")

    async def _health_check_impl(self) -> bool:
        """Perform health check."""
        # Component-specific health check logic
        return True

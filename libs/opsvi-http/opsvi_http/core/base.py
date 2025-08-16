"""Core opsvi-http functionality.

Comprehensive HTTP client and server functionality for the OPSVI ecosystem
"""

from typing import Any, Optional
import logging

from opsvi_foundation import BaseComponent, ComponentError
from opsvi_foundation.config.settings import BaseSettings

logger = logging.getLogger(__name__)


class HTTPCoreError(ComponentError):
    """Base exception for HTTP core errors."""

    pass


class HTTPConfigurationError(HTTPCoreError):
    """Configuration-related errors in HTTP core."""

    pass


class HTTPInitializationError(HTTPCoreError):
    """Initialization-related errors in HTTP core."""

    pass


class HTTPCoreConfig(BaseSettings):
    """Configuration for HTTP core components."""

    # Core configuration
    enabled: bool = True
    debug: bool = False
    log_level: str = "INFO"

    # HTTP-specific configuration
    default_timeout: float = 30.0
    max_connections: int = 100
    connection_pool_size: int = 20

    model_config = {"env_prefix": "OPSVI_HTTP_CORE_"}


class BaseHTTPCoreComponent(BaseComponent):
    """Base class for HTTP core components.

    Provides base functionality for all HTTP core components
    """

    def __init__(
        self, name: str, config: Optional[HTTPCoreConfig] = None, **kwargs: Any
    ) -> None:
        """Initialize HTTP core component.

        Args:
            name: Component name
            config: Configuration for the component
            **kwargs: Additional configuration parameters
        """
        super().__init__(name, config.model_dump() if config else {})
        self.http_config = config or HTTPCoreConfig(**kwargs)
        self._initialized = False
        self._logger = logging.getLogger(f"{__name__}.{name}")

    async def _initialize_impl(self) -> None:
        """Initialize the HTTP core component."""
        try:
            self._logger.info(f"Initializing HTTP core component: {self.name}")
            # Component-specific initialization logic
            self._initialized = True
            self._logger.info(
                f"HTTP core component {self.name} initialized successfully"
            )
        except Exception as e:
            self._logger.error(
                f"Failed to initialize HTTP core component {self.name}: {e}"
            )
            raise HTTPInitializationError(f"Initialization failed: {e}") from e

    async def _shutdown_impl(self) -> None:
        """Shutdown the HTTP core component."""
        try:
            self._logger.info(f"Shutting down HTTP core component: {self.name}")
            # Component-specific shutdown logic
            self._initialized = False
            self._logger.info(f"HTTP core component {self.name} shut down successfully")
        except Exception as e:
            self._logger.error(
                f"Failed to shutdown HTTP core component {self.name}: {e}"
            )
            raise HTTPCoreError(f"Shutdown failed: {e}") from e

    async def _health_check_impl(self) -> bool:
        """Perform health check for HTTP core component."""
        try:
            if not self._initialized:
                return False

            # Component-specific health check logic
            return True

        except Exception as e:
            self._logger.error(
                f"Health check failed for HTTP core component {self.name}: {e}"
            )
            return False

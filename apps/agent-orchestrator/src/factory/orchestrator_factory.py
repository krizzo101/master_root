"""
Orchestrator Factory with Dependency Injection

Provides configurable factory for creating orchestrator instances
with injected dependencies, eliminating singleton patterns.
"""

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional, Type

from ..interfaces import IFileHandler, IMessageBus, ITokenProvider

logger = logging.getLogger(__name__)


@dataclass
class OrchestratorConfig:
    """Configuration for orchestrator instances"""

    session_dir: Path = field(default_factory=lambda: Path("./output"))
    max_parallel_agents: int = 10
    enable_monitoring: bool = True
    enable_collaboration: bool = True
    enable_checkpointing: bool = True
    checkpoint_interval: int = 300  # seconds
    message_queue_size: int = 1000
    token_reservation_timeout: float = 30.0
    file_operation_timeout: float = 10.0
    enable_metrics: bool = True
    log_level: str = "INFO"
    custom_settings: Dict[str, Any] = field(default_factory=dict)


class OrchestratorFactory:
    """
    Factory for creating orchestrator instances with dependency injection.

    This factory:
    - Creates orchestrator instances with configurable providers
    - Manages dependency injection for all components
    - Enables easy testing with mock implementations
    - Eliminates singleton patterns throughout the codebase
    """

    def __init__(self):
        """Initialize the orchestrator factory"""
        self._token_provider_class: Optional[Type[ITokenProvider]] = None
        self._file_handler_class: Optional[Type[IFileHandler]] = None
        self._message_bus_class: Optional[Type[IMessageBus]] = None
        self._provider_configs: Dict[str, Dict] = {}
        self._orchestrator_class = None

    def register_token_provider(
        self, provider_class: Type[ITokenProvider], config: Optional[Dict] = None
    ) -> "OrchestratorFactory":
        """
        Register a token provider implementation.

        Args:
            provider_class: Class implementing ITokenProvider
            config: Optional configuration for the provider

        Returns:
            Self for method chaining
        """
        if not issubclass(provider_class, ITokenProvider):
            raise TypeError(f"{provider_class} must implement ITokenProvider interface")

        self._token_provider_class = provider_class
        if config:
            self._provider_configs["token"] = config

        logger.info(f"Registered token provider: {provider_class.__name__}")
        return self

    def register_file_handler(
        self, handler_class: Type[IFileHandler], config: Optional[Dict] = None
    ) -> "OrchestratorFactory":
        """
        Register a file handler implementation.

        Args:
            handler_class: Class implementing IFileHandler
            config: Optional configuration for the handler

        Returns:
            Self for method chaining
        """
        if not issubclass(handler_class, IFileHandler):
            raise TypeError(f"{handler_class} must implement IFileHandler interface")

        self._file_handler_class = handler_class
        if config:
            self._provider_configs["file"] = config

        logger.info(f"Registered file handler: {handler_class.__name__}")
        return self

    def register_message_bus(
        self, bus_class: Type[IMessageBus], config: Optional[Dict] = None
    ) -> "OrchestratorFactory":
        """
        Register a message bus implementation.

        Args:
            bus_class: Class implementing IMessageBus
            config: Optional configuration for the bus

        Returns:
            Self for method chaining
        """
        if not issubclass(bus_class, IMessageBus):
            raise TypeError(f"{bus_class} must implement IMessageBus interface")

        self._message_bus_class = bus_class
        if config:
            self._provider_configs["message"] = config

        logger.info(f"Registered message bus: {bus_class.__name__}")
        return self

    def set_orchestrator_class(self, orchestrator_class: Type) -> "OrchestratorFactory":
        """
        Set the orchestrator class to instantiate.

        Args:
            orchestrator_class: Orchestrator class to use

        Returns:
            Self for method chaining
        """
        self._orchestrator_class = orchestrator_class
        logger.info(f"Set orchestrator class: {orchestrator_class.__name__}")
        return self

    def _create_token_provider(self) -> ITokenProvider:
        """Create token provider instance"""
        if not self._token_provider_class:
            # Use default implementation if available
            from ..providers.token_provider_impl import TokenProviderImpl

            self._token_provider_class = TokenProviderImpl

        config = self._provider_configs.get("token", {})
        return self._token_provider_class(**config)

    def _create_file_handler(self) -> IFileHandler:
        """Create file handler instance"""
        if not self._file_handler_class:
            # Use default implementation if available
            from ..providers.file_handler_impl import FileHandlerImpl

            self._file_handler_class = FileHandlerImpl

        config = self._provider_configs.get("file", {})
        return self._file_handler_class(**config)

    def _create_message_bus(self) -> IMessageBus:
        """Create message bus instance"""
        if not self._message_bus_class:
            # Use default implementation if available
            from ..providers.message_bus_impl import MessageBusImpl

            self._message_bus_class = MessageBusImpl

        config = self._provider_configs.get("message", {})
        return self._message_bus_class(**config)

    def create(self, config: Optional[OrchestratorConfig] = None, **kwargs) -> Any:
        """
        Create a new orchestrator instance with injected dependencies.

        Args:
            config: Orchestrator configuration
            **kwargs: Additional arguments for orchestrator constructor

        Returns:
            Configured orchestrator instance

        Raises:
            RuntimeError: If orchestrator class not set
        """
        if not self._orchestrator_class:
            from ..orchestrator_di import DependencyInjectedOrchestrator

            self._orchestrator_class = DependencyInjectedOrchestrator

        config = config or OrchestratorConfig()

        # Create provider instances
        token_provider = self._create_token_provider()
        file_handler = self._create_file_handler()
        message_bus = self._create_message_bus()

        # Create orchestrator with injected dependencies
        orchestrator = self._orchestrator_class(
            token_provider=token_provider,
            file_handler=file_handler,
            message_bus=message_bus,
            config=config,
            **kwargs,
        )

        logger.info(
            f"Created {self._orchestrator_class.__name__} instance with "
            f"injected dependencies"
        )

        return orchestrator

    @classmethod
    def create_default(cls, config: Optional[OrchestratorConfig] = None) -> Any:
        """
        Create orchestrator with default providers.

        Args:
            config: Optional orchestrator configuration

        Returns:
            Orchestrator instance with default providers
        """
        factory = cls()
        return factory.create(config)

    @classmethod
    def create_for_testing(
        cls,
        config: Optional[OrchestratorConfig] = None,
        use_mock_providers: bool = True,
    ) -> Any:
        """
        Create orchestrator configured for testing.

        Args:
            config: Optional orchestrator configuration
            use_mock_providers: Use mock implementations

        Returns:
            Orchestrator instance configured for testing
        """
        factory = cls()

        if use_mock_providers:
            from ..mocks import MockFileHandler, MockMessageBus, MockTokenProvider

            factory.register_token_provider(MockTokenProvider)
            factory.register_file_handler(MockFileHandler)
            factory.register_message_bus(MockMessageBus)

        config = config or OrchestratorConfig(
            enable_monitoring=False, enable_metrics=False, log_level="DEBUG"
        )

        return factory.create(config)

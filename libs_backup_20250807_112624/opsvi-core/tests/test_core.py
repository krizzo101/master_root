"""
Tests for core components of OPSVI Core Library.
"""

from unittest.mock import Mock

import pytest

from opsvi_core.agents.base_agent import BaseAgent
from opsvi_core.core.config import AppConfig, config, load_config
from opsvi_core.core.exceptions import (
    ConfigurationError,
    DatabaseConnectionError,
    ExternalServiceError,
    InitializationError,
    OpsviError,
    ValidationError,
)
from opsvi_core.core.logging import get_logger, setup_logging
from opsvi_core.core.patterns import BaseActor, LifecycleComponent


class TestConfiguration:
    """Test configuration management."""

    def test_config_loading(self):
        """Ensure config loads with expected attributes."""
        assert hasattr(config, "app_name")
        assert hasattr(config, "environment")
        assert hasattr(config, "debug")
        assert hasattr(config, "log_level")
        assert isinstance(config, AppConfig)

    def test_config_defaults(self):
        """Test configuration default values."""
        assert config.app_name == "opsvi"
        assert config.environment == "development"
        assert config.debug is False
        assert config.log_level == "INFO"

    def test_load_config_function(self):
        """Test load_config function."""
        loaded_config = load_config()
        assert isinstance(loaded_config, AppConfig)
        assert loaded_config.app_name == "opsvi"


class TestLogging:
    """Test logging setup and functionality."""

    def test_logging_setup(self):
        """Ensure logging setup does not raise."""
        setup_logging("DEBUG")  # Should not raise

    def test_get_logger(self):
        """Test getting a structured logger."""
        logger = get_logger("test_logger")
        assert logger is not None
        assert hasattr(logger, "info")
        assert hasattr(logger, "error")

    def test_log_context(self):
        """Test log context creation."""
        from opsvi_core.core.logging import log_context

        context = log_context(user_id="123", action="test")
        assert context["user_id"] == "123"
        assert context["action"] == "test"


class TestExceptions:
    """Test custom exception hierarchy."""

    def test_base_exception(self):
        """Test base OpsviError exception."""
        with pytest.raises(OpsviError):
            raise OpsviError("Test error")

    def test_exception_with_details(self):
        """Test exception with additional details."""
        details = {"user_id": "123", "action": "test"}
        error = OpsviError("Test error", details)
        assert error.message == "Test error"
        assert error.details == details

    def test_configuration_error(self):
        """Test ConfigurationError."""
        with pytest.raises(ConfigurationError):
            raise ConfigurationError("Config error")

    def test_initialization_error(self):
        """Test InitializationError."""
        with pytest.raises(InitializationError):
            raise InitializationError("Init error")

    def test_validation_error(self):
        """Test ValidationError."""
        with pytest.raises(ValidationError):
            raise ValidationError("Validation error")

    def test_external_service_error(self):
        """Test ExternalServiceError."""
        with pytest.raises(ExternalServiceError):
            raise ExternalServiceError("Service error")

    def test_database_connection_error(self):
        """Test DatabaseConnectionError."""
        with pytest.raises(DatabaseConnectionError):
            raise DatabaseConnectionError("DB connection error")


class TestBaseActor:
    """Test BaseActor abstract class."""

    class TestActor(BaseActor):
        """Concrete implementation of BaseActor for testing."""

        async def on_start(self):
            """Test startup logic."""
            pass

        async def on_stop(self):
            """Test shutdown logic."""
            pass

        async def process_message(self, message):
            """Test message processing."""
            return {"processed": message}

    @pytest.mark.asyncio
    async def test_actor_initialization(self):
        """Test actor initialization."""
        actor = self.TestActor("test_actor")
        assert actor.name == "test_actor"
        assert actor.active is False

    @pytest.mark.asyncio
    async def test_actor_start_stop(self):
        """Test actor start and stop lifecycle."""
        actor = self.TestActor("test_actor")

        # Start actor
        await actor.start()
        assert actor.active is True

        # Stop actor
        await actor.stop()
        assert actor.active is False

    @pytest.mark.asyncio
    async def test_actor_message_handling(self):
        """Test actor message handling."""
        actor = self.TestActor("test_actor")
        await actor.start()

        message = {"test": "data"}
        result = await actor.handle_message(message)
        assert result["processed"] == message

    @pytest.mark.asyncio
    async def test_actor_inactive_message_handling(self):
        """Test message handling when actor is inactive."""
        actor = self.TestActor("test_actor")

        with pytest.raises(RuntimeError):
            await actor.handle_message({"test": "data"})

    def test_actor_is_active(self):
        """Test actor active status check."""
        actor = self.TestActor("test_actor")
        assert actor.is_active() is False


class TestLifecycleComponent:
    """Test LifecycleComponent abstract class."""

    class TestComponent(LifecycleComponent):
        """Concrete implementation of LifecycleComponent for testing."""

        async def on_initialize(self):
            """Test initialization logic."""
            pass

        async def on_shutdown(self):
            """Test shutdown logic."""
            pass

    @pytest.mark.asyncio
    async def test_component_initialization(self):
        """Test component initialization."""
        component = self.TestComponent("test_component")
        assert component.name == "test_component"
        assert component.active is False

    @pytest.mark.asyncio
    async def test_component_initialize_shutdown(self):
        """Test component initialize and shutdown lifecycle."""
        component = self.TestComponent("test_component")

        # Initialize component
        await component.initialize()
        assert component.active is True

        # Shutdown component
        await component.shutdown()
        assert component.active is False

    def test_component_is_active(self):
        """Test component active status check."""
        component = self.TestComponent("test_component")
        assert component.is_active() is False


class TestBaseAgent:
    """Test BaseAgent class."""

    class TestAgent(BaseAgent):
        """Concrete implementation of BaseAgent for testing."""

        async def process(self, message):
            """Test message processing."""
            return {"processed": message}

    @pytest.mark.asyncio
    async def test_agent_initialization(self):
        """Test agent initialization."""
        agent = self.TestAgent("test_agent")
        assert agent.agent_id == "test_agent"
        assert agent.active is False
        assert agent.plugins == []

    @pytest.mark.asyncio
    async def test_agent_activation_deactivation(self):
        """Test agent activation and deactivation."""
        agent = self.TestAgent("test_agent")

        # Activate agent
        await agent.activate()
        assert agent.active is True

        # Deactivate agent
        await agent.deactivate()
        assert agent.active is False

    @pytest.mark.asyncio
    async def test_agent_message_handling(self):
        """Test agent message handling."""
        agent = self.TestAgent("test_agent")
        await agent.activate()

        message = {"test": "data"}
        result = await agent.handle(message)
        assert result["processed"] == message

    @pytest.mark.asyncio
    async def test_agent_inactive_message_handling(self):
        """Test message handling when agent is inactive."""
        agent = self.TestAgent("test_agent")

        with pytest.raises(RuntimeError):
            await agent.handle({"test": "data"})

    def test_agent_plugin_management(self):
        """Test agent plugin management."""
        agent = self.TestAgent("test_agent")
        plugin = Mock()

        # Add plugin
        agent.add_plugin(plugin)
        assert len(agent.plugins) == 1
        assert plugin in agent.plugins

        # Remove plugin
        agent.remove_plugin(plugin)
        assert len(agent.plugins) == 0
        assert plugin not in agent.plugins

    def test_agent_get_plugins(self):
        """Test getting agent plugins."""
        agent = self.TestAgent("test_agent")
        plugin = Mock()
        agent.add_plugin(plugin)

        plugins = agent.get_plugins()
        assert plugins == [plugin]
        # Ensure it's a copy
        assert plugins is not agent.plugins

    def test_agent_is_active(self):
        """Test agent active status check."""
        agent = self.TestAgent("test_agent")
        assert agent.is_active() is False

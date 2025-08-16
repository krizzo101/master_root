"""Tests for opsvi-foundation library."""

import pytest
import asyncio
from typing import Dict, Any

from opsvi_foundation import (
    BaseComponent,
    ComponentError,
    BaseSettings,
    LibraryConfig,
    LibrarySettings,
    FoundationConfig,
    LibraryError,
    LibraryConfigurationError,
)


class TestComponent(BaseComponent):
    """Test component for testing BaseComponent."""

    async def _initialize_impl(self) -> None:
        """Test initialization implementation."""
        pass

    async def _shutdown_impl(self) -> None:
        """Test shutdown implementation."""
        pass

    async def _health_check_impl(self) -> bool:
        """Test health check implementation."""
        return True


class TestComponentWithError(BaseComponent):
    """Test component that raises errors."""

    async def _initialize_impl(self) -> None:
        """Test initialization that raises error."""
        raise RuntimeError("Initialization failed")

    async def _shutdown_impl(self) -> None:
        """Test shutdown implementation."""
        pass

    async def _health_check_impl(self) -> bool:
        """Test health check implementation."""
        return False


class TestSettings(BaseSettings):
    """Test settings class."""

    test_value: str = "default"


def test_base_component_initialization():
    """Test BaseComponent initialization."""
    component = TestComponent("test-component")
    assert component.name == "test-component"
    assert component.config == {}
    assert not component._initialized


def test_base_component_with_config():
    """Test BaseComponent with configuration."""
    config = {"key": "value"}
    component = TestComponent("test-component", config)
    assert component.config == config


def test_base_component_with_kwargs():
    """Test BaseComponent with kwargs."""
    component = TestComponent("test-component", key="value")
    assert component.config == {"key": "value"}


@pytest.mark.asyncio
async def test_base_component_initialize():
    """Test BaseComponent initialization."""
    component = TestComponent("test-component")
    await component.initialize()
    assert component._initialized


@pytest.mark.asyncio
async def test_base_component_initialize_error():
    """Test BaseComponent initialization error."""
    component = TestComponentWithError("test-component")
    with pytest.raises(ComponentError):
        await component.initialize()


@pytest.mark.asyncio
async def test_base_component_shutdown():
    """Test BaseComponent shutdown."""
    component = TestComponent("test-component")
    await component.initialize()
    await component.shutdown()
    assert not component._initialized


@pytest.mark.asyncio
async def test_base_component_health_check():
    """Test BaseComponent health check."""
    component = TestComponent("test-component")
    # Health check should fail when not initialized
    assert not await component.health_check()

    # Health check should pass when initialized
    await component.initialize()
    assert await component.health_check()


@pytest.mark.asyncio
async def test_base_component_health_check_failure():
    """Test BaseComponent health check failure."""
    component = TestComponentWithError("test-component")
    # Health check should fail when not initialized
    assert not await component.health_check()


def test_base_settings():
    """Test BaseSettings."""
    settings = TestSettings()
    assert settings.test_value == "default"

    settings = TestSettings(test_value="custom")
    assert settings.test_value == "custom"


def test_library_config():
    """Test LibraryConfig."""
    config = LibraryConfig(library_name="test-lib", version="1.0.0")
    assert config.library_name == "test-lib"
    assert config.version == "1.0.0"
    assert config.enabled is True
    assert config.debug is False
    assert config.log_level == "INFO"


def test_library_settings():
    """Test LibrarySettings."""
    settings = LibrarySettings()
    assert settings.environment == "production"
    assert settings.instance_id == "default"
    assert settings.log_format == "json"
    assert settings.max_workers == 10
    assert settings.timeout == 30.0
    assert settings.enable_audit_logging is True
    assert settings.secrets_backend == "env"


def test_foundation_config():
    """Test FoundationConfig."""
    config = FoundationConfig()
    assert config.enable_utilities is True
    assert config.enable_retry is True
    assert config.enable_backoff is True
    assert config.max_retries == 3
    assert config.retry_delay == 1.0
    assert config.backoff_factor == 2.0


def test_library_error():
    """Test LibraryError."""
    error = LibraryError("Test error", "TEST_001", {"detail": "test"})
    assert error.message == "Test error"
    assert error.error_code == "TEST_001"
    assert error.details == {"detail": "test"}


def test_library_configuration_error():
    """Test LibraryConfigurationError."""
    error = LibraryConfigurationError("Config error")
    assert isinstance(error, LibraryError)
    assert error.message == "Config error"


def test_base_settings_inheritance():
    """Test that BaseSettings can be inherited properly."""

    class CustomSettings(BaseSettings):
        custom_field: str = "default"

    settings = CustomSettings()
    assert settings.custom_field == "default"

    settings = CustomSettings(custom_field="custom")
    assert settings.custom_field == "custom"


def test_component_error_inheritance():
    """Test that ComponentError can be inherited properly."""

    class CustomComponentError(ComponentError):
        pass

    error = CustomComponentError("Custom error")
    assert isinstance(error, ComponentError)
    assert str(error) == "Custom error"

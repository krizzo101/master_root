"""
Centralized testing framework for OPSVI libraries.

Provides generic test patterns to eliminate repetition across all libraries.
"""

from __future__ import annotations

import pytest
from typing import Any, Dict, Optional, Type

from opsvi_foundation.scaffolding.base import LibraryBase


class LibraryTestBase:
    """Base test class for all OPSVI library components."""

    @pytest.fixture
    def component(self) -> LibraryBase:
        """Create a test component instance."""
        raise NotImplementedError("Subclasses must implement component fixture")

    @pytest.mark.asyncio
    async def test_initialization(self, component: LibraryBase) -> None:
        """Test component initialization."""
        await component.initialize()
        assert component is not None

    @pytest.mark.asyncio
    async def test_shutdown(self, component: LibraryBase) -> None:
        """Test component shutdown."""
        await component.initialize()
        await component.shutdown()
        # Add assertions as needed

    @pytest.mark.asyncio
    async def test_health_check(self, component: LibraryBase) -> None:
        """Test health check functionality."""
        await component.initialize()
        health_status = await component.health_check()
        assert isinstance(health_status, bool)

    @pytest.mark.asyncio
    async def test_lifecycle(self, component: LibraryBase) -> None:
        """Test complete component lifecycle."""
        # Initialize
        await component.initialize()
        assert await component.health_check()

        # Shutdown
        await component.shutdown()
        # Health check might be False after shutdown, which is acceptable


def create_library_test_class(
    library_name: str,
    component_class: Type[LibraryBase],
    additional_tests: Optional[Dict[str, Any]] = None
) -> Type[LibraryTestBase]:
    """Factory function to create library-specific test classes."""

    class_name = f"Test{library_name.title().replace('-', '')}Base"

    # Create the test class
    test_class = type(class_name, (LibraryTestBase,), {})

    # Add component fixture
    def component_fixture(self):
        return component_class()

    test_class.component = pytest.fixture(component_fixture)

    # Add additional tests
    if additional_tests:
        for test_name, test_method in additional_tests.items():
            setattr(test_class, test_name, test_method)

    return test_class


class ConfigurableLibraryTestBase(LibraryTestBase):
    """Base test class for configurable library components."""

    @pytest.mark.asyncio
    async def test_config_validation(self, component: LibraryBase) -> None:
        """Test configuration validation."""
        # This test assumes the component has config validation
        await component.initialize()
        # Add specific config validation tests as needed

    @pytest.mark.asyncio
    async def test_invalid_config(self, component: LibraryBase) -> None:
        """Test behavior with invalid configuration."""
        # Create component with invalid config and test error handling
        pass


class ServiceLibraryTestBase(LibraryTestBase):
    """Base test class for service library components."""

    @pytest.mark.asyncio
    async def test_start_stop(self, component: LibraryBase) -> None:
        """Test service start and stop."""
        if hasattr(component, 'start') and hasattr(component, 'stop'):
            await component.start()
            assert await component.health_check()

            await component.stop()
            # Service might be stopped, health check could be False

    @pytest.mark.asyncio
    async def test_service_health(self, component: LibraryBase) -> None:
        """Test service-specific health checks."""
        if hasattr(component, 'start'):
            await component.start()
            health_status = await component.health_check()
            assert isinstance(health_status, bool)


class ManagerLibraryTestBase(LibraryTestBase):
    """Base test class for manager library components."""

    @pytest.mark.asyncio
    async def test_component_registration(self, component: LibraryBase) -> None:
        """Test component registration functionality."""
        if hasattr(component, 'register_component'):
            # Test registering a mock component
            mock_component = type('MockComponent', (), {'health_check': lambda: True})()
            await component.register_component('test', mock_component)

            if hasattr(component, 'get_component'):
                retrieved = await component.get_component('test')
                assert retrieved == mock_component

    @pytest.mark.asyncio
    async def test_component_removal(self, component: LibraryBase) -> None:
        """Test component removal functionality."""
        if hasattr(component, 'register_component') and hasattr(component, 'remove_component'):
            mock_component = type('MockComponent', (), {'health_check': lambda: True})()
            await component.register_component('test', mock_component)
            await component.remove_component('test')

            if hasattr(component, 'get_component'):
                retrieved = await component.get_component('test')
                assert retrieved is None


def create_test_suite(
    library_name: str,
    component_class: Type[LibraryBase],
    test_base_class: Type[LibraryTestBase] = LibraryTestBase,
    additional_tests: Optional[Dict[str, Any]] = None
) -> Type[LibraryTestBase]:
    """Create a complete test suite for a library."""
    return create_library_test_class(
        library_name,
        component_class,
        additional_tests
    )


# Common test utilities
def mock_component(health_check_result: bool = True) -> Any:
    """Create a mock component for testing."""
    return type('MockComponent', (), {
        'health_check': lambda: health_check_result,
        'initialize': lambda: None,
        'shutdown': lambda: None,
    })()


def async_mock_component(health_check_result: bool = True) -> Any:
    """Create an async mock component for testing."""
    async def async_health_check():
        return health_check_result

    async def async_initialize():
        pass

    async def async_shutdown():
        pass

    return type('AsyncMockComponent', (), {
        'health_check': async_health_check,
        'initialize': async_initialize,
        'shutdown': async_shutdown,
    })()

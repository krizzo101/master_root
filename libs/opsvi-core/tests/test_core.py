"""Tests for opsvi-core library."""

import pytest
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any

from opsvi_core import (
    ServiceRegistry,
    EventBus,
    StateManager,
    ServiceInfo,
    ServiceStatus,
    CoreConfig,
    CoreError,
    ServiceRegistryError,
    EventBusError,
    StateManagerError,
)


@pytest.fixture
def core_config():
    """Create a test core configuration."""
    return CoreConfig(
        registry_enabled=True,
        event_bus_enabled=True,
        state_manager_enabled=True,
        registry_cleanup_interval=0.1,  # Fast cleanup for testing
        service_timeout=1.0,  # Short timeout for testing
    )


@pytest.fixture
def service_info():
    """Create a test service info."""
    return ServiceInfo(
        name="test-service",
        status=ServiceStatus.RUNNING,
        version="1.0.0",
        host="localhost",
        port=8080,
    )


class TestServiceRegistry:
    """Test ServiceRegistry functionality."""

    @pytest.mark.asyncio
    async def test_service_registry_initialization(self, core_config):
        """Test ServiceRegistry initialization."""
        registry = ServiceRegistry(core_config)
        await registry.initialize()
        assert registry._initialized
        await registry.shutdown()

    @pytest.mark.asyncio
    async def test_register_service(self, core_config, service_info):
        """Test service registration."""
        registry = ServiceRegistry(core_config)
        await registry.initialize()

        await registry.register_service(service_info)
        services = await registry.list_services()
        assert len(services) == 1
        assert services[0].name == "test-service"

        await registry.shutdown()

    @pytest.mark.asyncio
    async def test_unregister_service(self, core_config, service_info):
        """Test service unregistration."""
        registry = ServiceRegistry(core_config)
        await registry.initialize()

        await registry.register_service(service_info)
        await registry.unregister_service("test-service")

        services = await registry.list_services()
        assert len(services) == 0

        await registry.shutdown()

    @pytest.mark.asyncio
    async def test_get_service(self, core_config, service_info):
        """Test getting service information."""
        registry = ServiceRegistry(core_config)
        await registry.initialize()

        await registry.register_service(service_info)
        retrieved_service = await registry.get_service("test-service")

        assert retrieved_service is not None
        assert retrieved_service.name == "test-service"
        assert retrieved_service.status == ServiceStatus.RUNNING

        await registry.shutdown()

    @pytest.mark.asyncio
    async def test_update_heartbeat(self, core_config, service_info):
        """Test heartbeat update."""
        registry = ServiceRegistry(core_config)
        await registry.initialize()

        await registry.register_service(service_info)
        await registry.update_heartbeat("test-service")

        service = await registry.get_service("test-service")
        assert service.last_heartbeat is not None

        await registry.shutdown()

    @pytest.mark.asyncio
    async def test_cleanup_stale_services(self, core_config):
        """Test cleanup of stale services."""
        registry = ServiceRegistry(core_config)
        await registry.initialize()

        # Create a service with old heartbeat
        old_service = ServiceInfo(
            name="old-service",
            status=ServiceStatus.RUNNING,
            last_heartbeat=datetime.utcnow() - timedelta(seconds=10),
        )

        await registry.register_service(old_service)

        # Wait for cleanup
        await asyncio.sleep(0.2)

        services = await registry.list_services()
        assert len(services) == 0

        await registry.shutdown()


class TestEventBus:
    """Test EventBus functionality."""

    @pytest.mark.asyncio
    async def test_event_bus_initialization(self, core_config):
        """Test EventBus initialization."""
        event_bus = EventBus(core_config)
        await event_bus.initialize()
        assert event_bus._initialized
        await event_bus.shutdown()

    @pytest.mark.asyncio
    async def test_subscribe_and_publish(self, core_config):
        """Test event subscription and publishing."""
        event_bus = EventBus(core_config)
        await event_bus.initialize()

        received_events = []

        async def event_handler(data: Dict[str, Any]):
            received_events.append(data)

        await event_bus.subscribe("test-event", event_handler)
        await event_bus.publish("test-event", {"message": "hello"})

        # Wait for event processing
        await asyncio.sleep(0.1)

        assert len(received_events) == 1
        assert received_events[0]["message"] == "hello"

        await event_bus.shutdown()

    @pytest.mark.asyncio
    async def test_unsubscribe(self, core_config):
        """Test event unsubscription."""
        event_bus = EventBus(core_config)
        await event_bus.initialize()

        received_events = []

        async def event_handler(data: Dict[str, Any]):
            received_events.append(data)

        await event_bus.subscribe("test-event", event_handler)
        await event_bus.unsubscribe("test-event", event_handler)
        await event_bus.publish("test-event", {"message": "hello"})

        # Wait for event processing
        await asyncio.sleep(0.1)

        assert len(received_events) == 0

        await event_bus.shutdown()

    @pytest.mark.asyncio
    async def test_multiple_subscribers(self, core_config):
        """Test multiple subscribers for the same event."""
        event_bus = EventBus(core_config)
        await event_bus.initialize()

        received_events_1 = []
        received_events_2 = []

        async def event_handler_1(data: Dict[str, Any]):
            received_events_1.append(data)

        async def event_handler_2(data: Dict[str, Any]):
            received_events_2.append(data)

        await event_bus.subscribe("test-event", event_handler_1)
        await event_bus.subscribe("test-event", event_handler_2)
        await event_bus.publish("test-event", {"message": "hello"})

        # Wait for event processing
        await asyncio.sleep(0.1)

        assert len(received_events_1) == 1
        assert len(received_events_2) == 1
        assert received_events_1[0]["message"] == "hello"
        assert received_events_2[0]["message"] == "hello"

        await event_bus.shutdown()


class TestStateManager:
    """Test StateManager functionality."""

    @pytest.mark.asyncio
    async def test_state_manager_initialization(self, core_config):
        """Test StateManager initialization."""
        state_manager = StateManager(core_config)
        await state_manager.initialize()
        assert state_manager._initialized
        await state_manager.shutdown()

    @pytest.mark.asyncio
    async def test_set_and_get_state(self, core_config):
        """Test setting and getting state."""
        state_manager = StateManager(core_config)
        await state_manager.initialize()

        await state_manager.set_state("test-key", "test-value")
        value = await state_manager.get_state("test-key")

        assert value == "test-value"

        await state_manager.shutdown()

    @pytest.mark.asyncio
    async def test_get_state_default(self, core_config):
        """Test getting state with default value."""
        state_manager = StateManager(core_config)
        await state_manager.initialize()

        value = await state_manager.get_state("non-existent", "default")
        assert value == "default"

        await state_manager.shutdown()

    @pytest.mark.asyncio
    async def test_delete_state(self, core_config):
        """Test deleting state."""
        state_manager = StateManager(core_config)
        await state_manager.initialize()

        await state_manager.set_state("test-key", "test-value")
        await state_manager.delete_state("test-key")

        value = await state_manager.get_state("test-key")
        assert value is None

        await state_manager.shutdown()

    @pytest.mark.asyncio
    async def test_list_state_keys(self, core_config):
        """Test listing state keys."""
        state_manager = StateManager(core_config)
        await state_manager.initialize()

        await state_manager.set_state("key1", "value1")
        await state_manager.set_state("key2", "value2")

        keys = await state_manager.list_state_keys()
        assert "key1" in keys
        assert "key2" in keys
        assert len(keys) == 2

        await state_manager.shutdown()

    @pytest.mark.asyncio
    async def test_clear_state(self, core_config):
        """Test clearing all state."""
        state_manager = StateManager(core_config)
        await state_manager.initialize()

        await state_manager.set_state("key1", "value1")
        await state_manager.set_state("key2", "value2")
        await state_manager.clear_state()

        keys = await state_manager.list_state_keys()
        assert len(keys) == 0

        await state_manager.shutdown()


class TestServiceInfo:
    """Test ServiceInfo functionality."""

    def test_service_info_creation(self):
        """Test ServiceInfo creation."""
        service = ServiceInfo(
            name="test-service",
            status=ServiceStatus.RUNNING,
            version="1.0.0",
            host="localhost",
            port=8080,
            metadata={"env": "test"},
        )

        assert service.name == "test-service"
        assert service.status == ServiceStatus.RUNNING
        assert service.version == "1.0.0"
        assert service.host == "localhost"
        assert service.port == 8080
        assert service.metadata["env"] == "test"
        assert service.created_at is not None
        assert service.last_heartbeat is None

    def test_service_info_defaults(self):
        """Test ServiceInfo default values."""
        service = ServiceInfo(name="test-service", status=ServiceStatus.RUNNING)

        assert service.version == "1.0.0"
        assert service.host == "localhost"
        assert service.port is None
        assert service.metadata == {}


class TestServiceStatus:
    """Test ServiceStatus enumeration."""

    def test_service_status_values(self):
        """Test ServiceStatus values."""
        assert ServiceStatus.UNKNOWN.value == "unknown"
        assert ServiceStatus.STARTING.value == "starting"
        assert ServiceStatus.RUNNING.value == "running"
        assert ServiceStatus.STOPPING.value == "stopping"
        assert ServiceStatus.STOPPED.value == "stopped"
        assert ServiceStatus.ERROR.value == "error"


class TestCoreConfig:
    """Test CoreConfig functionality."""

    def test_core_config_defaults(self):
        """Test CoreConfig default values."""
        config = CoreConfig()

        assert config.registry_enabled is True
        assert config.event_bus_enabled is True
        assert config.state_manager_enabled is True
        assert config.registry_cleanup_interval == 30.0
        assert config.service_timeout == 60.0
        assert config.max_event_queue_size == 1000
        assert config.event_timeout == 5.0
        assert config.state_persistence_enabled is False
        assert config.state_backup_interval == 300.0

    def test_core_config_custom_values(self):
        """Test CoreConfig with custom values."""
        config = CoreConfig(
            registry_enabled=False,
            event_bus_enabled=False,
            state_manager_enabled=False,
            registry_cleanup_interval=10.0,
            service_timeout=30.0,
            max_event_queue_size=500,
            event_timeout=2.0,
            state_persistence_enabled=True,
            state_backup_interval=150.0,
        )

        assert config.registry_enabled is False
        assert config.event_bus_enabled is False
        assert config.state_manager_enabled is False
        assert config.registry_cleanup_interval == 10.0
        assert config.service_timeout == 30.0
        assert config.max_event_queue_size == 500
        assert config.event_timeout == 2.0
        assert config.state_persistence_enabled is True
        assert config.state_backup_interval == 150.0


class TestExceptions:
    """Test exception classes."""

    def test_core_error_inheritance(self):
        """Test CoreError inheritance."""
        error = CoreError("Test error")
        assert isinstance(error, CoreError)
        assert str(error) == "Test error"

    def test_service_registry_error_inheritance(self):
        """Test ServiceRegistryError inheritance."""
        error = ServiceRegistryError("Registry error")
        assert isinstance(error, CoreError)
        assert str(error) == "Registry error"

    def test_event_bus_error_inheritance(self):
        """Test EventBusError inheritance."""
        error = EventBusError("Event bus error")
        assert isinstance(error, CoreError)
        assert str(error) == "Event bus error"

    def test_state_manager_error_inheritance(self):
        """Test StateManagerError inheritance."""
        error = StateManagerError("State manager error")
        assert isinstance(error, CoreError)
        assert str(error) == "State manager error"

"""Core opsvi-core functionality.

Comprehensive opsvi-core library for the OPSVI ecosystem
"""

from typing import Any, Dict, List, Optional, Callable, Awaitable
import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json
from pathlib import Path

from opsvi_foundation import BaseComponent, ComponentError, BaseSettings

logger = logging.getLogger(__name__)


class ServiceStatus(Enum):
    """Service status enumeration."""

    UNKNOWN = "unknown"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"


@dataclass
class ServiceInfo:
    """Service information."""

    name: str
    status: ServiceStatus
    version: str = "1.0.0"
    host: str = "localhost"
    port: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_heartbeat: Optional[datetime] = None


class CoreError(ComponentError):
    """Base exception for core errors."""

    pass


class ServiceRegistryError(CoreError):
    """Service registry errors."""

    pass


class EventBusError(CoreError):
    """Event bus errors."""

    pass


class StateManagerError(CoreError):
    """State manager errors."""

    pass


class CoreConfig(BaseSettings):
    """Configuration for opsvi-core."""

    # Service registry configuration
    registry_enabled: bool = True
    registry_cleanup_interval: float = 30.0  # seconds
    service_timeout: float = 60.0  # seconds

    # Event bus configuration
    event_bus_enabled: bool = True
    max_event_queue_size: int = 1000
    event_timeout: float = 5.0  # seconds

    # State manager configuration
    state_manager_enabled: bool = True
    state_persistence_enabled: bool = False
    state_backup_interval: float = 300.0  # seconds

    class Config:
        env_prefix = "OPSVI_CORE_"


class ServiceRegistry(BaseComponent):
    """Service registry for managing service discovery and health."""

    def __init__(self, config: Optional[CoreConfig] = None, **kwargs: Any) -> None:
        """Initialize service registry."""
        super().__init__("service-registry", config.dict() if config else {})
        self.core_config = config or CoreConfig(**kwargs)
        self._services: Dict[str, ServiceInfo] = {}
        self._cleanup_task: Optional[asyncio.Task] = None

    async def _initialize_impl(self) -> None:
        """Initialize service registry."""
        if self.core_config.registry_enabled:
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())

    async def _shutdown_impl(self) -> None:
        """Shutdown service registry."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

    async def _health_check_impl(self) -> bool:
        """Health check implementation."""
        return len(self._services) >= 0  # Registry is healthy if it can track services

    async def register_service(self, service_info: ServiceInfo) -> None:
        """Register a service."""
        if not self._initialized:
            raise ServiceRegistryError("Service registry not initialized")

        self._services[service_info.name] = service_info
        logger.info(f"Registered service: {service_info.name}")

    async def unregister_service(self, service_name: str) -> None:
        """Unregister a service."""
        if service_name in self._services:
            del self._services[service_name]
            logger.info(f"Unregistered service: {service_name}")

    async def get_service(self, service_name: str) -> Optional[ServiceInfo]:
        """Get service information."""
        return self._services.get(service_name)

    async def list_services(self) -> List[ServiceInfo]:
        """List all registered services."""
        return list(self._services.values())

    async def update_heartbeat(self, service_name: str) -> None:
        """Update service heartbeat."""
        if service_name in self._services:
            self._services[service_name].last_heartbeat = datetime.utcnow()

    async def _cleanup_loop(self) -> None:
        """Cleanup loop for stale services."""
        while True:
            try:
                await asyncio.sleep(self.core_config.registry_cleanup_interval)
                await self._cleanup_stale_services()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")

    async def _cleanup_stale_services(self) -> None:
        """Cleanup stale services."""
        now = datetime.utcnow()
        stale_services = []

        for name, service in self._services.items():
            if (
                service.last_heartbeat
                and (now - service.last_heartbeat).total_seconds()
                > self.core_config.service_timeout
            ):
                stale_services.append(name)

        for name in stale_services:
            await self.unregister_service(name)


class EventBus(BaseComponent):
    """Event bus for inter-service communication."""

    def __init__(self, config: Optional[CoreConfig] = None, **kwargs: Any) -> None:
        """Initialize event bus."""
        super().__init__("event-bus", config.dict() if config else {})
        self.core_config = config or CoreConfig(**kwargs)
        self._subscribers: Dict[
            str, List[Callable[[Dict[str, Any]], Awaitable[None]]]
        ] = {}
        self._event_queue: asyncio.Queue = asyncio.Queue(
            maxsize=self.core_config.max_event_queue_size
        )
        self._processor_task: Optional[asyncio.Task] = None

    async def _initialize_impl(self) -> None:
        """Initialize event bus."""
        if self.core_config.event_bus_enabled:
            self._processor_task = asyncio.create_task(self._process_events())

    async def _shutdown_impl(self) -> None:
        """Shutdown event bus."""
        if self._processor_task:
            self._processor_task.cancel()
            try:
                await self._processor_task
            except asyncio.CancelledError:
                pass

    async def _health_check_impl(self) -> bool:
        """Health check implementation."""
        return not self._event_queue.full()

    async def subscribe(
        self, event_type: str, handler: Callable[[Dict[str, Any]], Awaitable[None]]
    ) -> None:
        """Subscribe to an event type."""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(handler)
        logger.info(f"Subscribed to event type: {event_type}")

    async def unsubscribe(
        self, event_type: str, handler: Callable[[Dict[str, Any]], Awaitable[None]]
    ) -> None:
        """Unsubscribe from an event type."""
        if event_type in self._subscribers:
            try:
                self._subscribers[event_type].remove(handler)
                logger.info(f"Unsubscribed from event type: {event_type}")
            except ValueError:
                pass

    async def publish(self, event_type: str, event_data: Dict[str, Any]) -> None:
        """Publish an event."""
        if not self._initialized:
            raise EventBusError("Event bus not initialized")

        event = {
            "type": event_type,
            "data": event_data,
            "timestamp": datetime.utcnow().isoformat(),
            "source": self.name,
        }

        try:
            self._event_queue.put_nowait(event)
        except asyncio.QueueFull:
            raise EventBusError("Event queue is full")

    async def _process_events(self) -> None:
        """Process events from the queue."""
        while True:
            try:
                event = await asyncio.wait_for(
                    self._event_queue.get(), timeout=self.core_config.event_timeout
                )
                await self._handle_event(event)
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error processing event: {e}")

    async def _handle_event(self, event: Dict[str, Any]) -> None:
        """Handle a single event."""
        event_type = event["type"]
        if event_type in self._subscribers:
            for handler in self._subscribers[event_type]:
                try:
                    await handler(event["data"])
                except Exception as e:
                    logger.error(f"Error in event handler: {e}")


class StateManager(BaseComponent):
    """State manager for managing application state."""

    def __init__(self, config: Optional[CoreConfig] = None, **kwargs: Any) -> None:
        """Initialize state manager."""
        super().__init__("state-manager", config.dict() if config else {})
        self.core_config = config or CoreConfig(**kwargs)
        self._state: Dict[str, Any] = {}
        self._backup_task: Optional[asyncio.Task] = None
        self._state_file = Path("/tmp/opsvi_state_backup.json")
        # Try to restore state on initialization
        self._restore_state()

    async def _initialize_impl(self) -> None:
        """Initialize state manager."""
        if (
            self.core_config.state_manager_enabled
            and self.core_config.state_persistence_enabled
        ):
            self._backup_task = asyncio.create_task(self._backup_loop())

    async def _shutdown_impl(self) -> None:
        """Shutdown state manager."""
        # Save state one final time before shutdown
        if self.core_config.state_persistence_enabled:
            await self._backup_state()

        if self._backup_task:
            self._backup_task.cancel()
            try:
                await self._backup_task
            except asyncio.CancelledError:
                pass

    async def _health_check_impl(self) -> bool:
        """Health check implementation."""
        return True  # State manager is always healthy

    async def set_state(self, key: str, value: Any) -> None:
        """Set a state value."""
        self._state[key] = value
        logger.debug(f"Set state: {key} = {value}")

    async def get_state(self, key: str, default: Any = None) -> Any:
        """Get a state value."""
        return self._state.get(key, default)

    async def delete_state(self, key: str) -> None:
        """Delete a state value."""
        if key in self._state:
            del self._state[key]
            logger.debug(f"Deleted state: {key}")

    async def list_state_keys(self) -> List[str]:
        """List all state keys."""
        return list(self._state.keys())

    async def clear_state(self) -> None:
        """Clear all state."""
        self._state.clear()
        logger.info("Cleared all state")

    async def _backup_loop(self) -> None:
        """Backup loop for state persistence."""
        while True:
            try:
                await asyncio.sleep(self.core_config.state_backup_interval)
                await self._backup_state()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in backup loop: {e}")

    async def _backup_state(self) -> None:
        """Backup state to persistent storage."""
        try:
            # Create a copy of the state to avoid modification during serialization
            state_copy = dict(self._state)

            # Convert to JSON and write to file
            state_json = json.dumps(state_copy, indent=2, default=str)

            # Write atomically by using a temporary file
            temp_file = self._state_file.with_suffix(".tmp")
            temp_file.write_text(state_json)

            # Move temp file to actual file (atomic on most systems)
            temp_file.replace(self._state_file)

            logger.debug(
                f"State backup completed: {len(state_copy)} keys saved to {self._state_file}"
            )
        except Exception as e:
            logger.error(f"Failed to backup state: {e}")
            # Don't raise - we want the system to continue even if backup fails

    def _restore_state(self) -> None:
        """Restore state from persistent storage.

        This is a synchronous method called during initialization.
        """
        try:
            if self._state_file.exists():
                state_json = self._state_file.read_text()
                restored_state = json.loads(state_json)

                if isinstance(restored_state, dict):
                    self._state = restored_state
                    logger.info(
                        f"State restored: {len(self._state)} keys loaded from {self._state_file}"
                    )
                else:
                    logger.warning(
                        f"Invalid state file format: expected dict, got {type(restored_state)}"
                    )
            else:
                logger.debug(
                    f"No state file found at {self._state_file}, starting with empty state"
                )
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse state file: {e}")
            # Start with empty state if file is corrupted
            self._state = {}
        except Exception as e:
            logger.error(f"Failed to restore state: {e}")
            # Start with empty state on any other error
            self._state = {}

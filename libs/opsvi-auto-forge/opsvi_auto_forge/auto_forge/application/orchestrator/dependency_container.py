"""Dependency injection container for orchestrator components."""

import logging
from typing import Any, Dict
from functools import wraps
import redis.asyncio as redis

logger = logging.getLogger(__name__)


class DependencyContainer:
    """Dependency injection container for managing component dependencies.

    This container provides a service locator pattern to manage dependencies
    and break circular imports by using lazy loading and dependency injection.
    """

    def __init__(self):
        """Initialize the dependency container."""
        self._services: Dict[str, Any] = {}
        self._factories: Dict[str, callable] = {}
        self._singletons: Dict[str, Any] = {}

        logger.info("DependencyContainer initialized")

    def register_service(self, name: str, service: Any) -> None:
        """Register a service instance.

        Args:
            name: Service name
            service: Service instance
        """
        self._services[name] = service
        logger.debug(f"Registered service: {name}")

    def register_factory(self, name: str, factory: callable) -> None:
        """Register a service factory.

        Args:
            name: Service name
            factory: Factory function to create service
        """
        self._factories[name] = factory
        logger.debug(f"Registered factory: {name}")

    def register_singleton(self, name: str, factory: callable) -> None:
        """Register a singleton service factory.

        Args:
            name: Service name
            factory: Factory function to create service (called only once)
        """
        self._factories[name] = factory
        logger.debug(f"Registered singleton factory: {name}")

    def get_service(self, name: str) -> Any:
        """Get a service by name.

        Args:
            name: Service name

        Returns:
            Service instance

        Raises:
            KeyError: If service not found
        """
        # Check if service is already registered
        if name in self._services:
            return self._services[name]

        # Check if singleton exists
        if name in self._singletons:
            return self._singletons[name]

        # Check if factory exists
        if name in self._factories:
            factory = self._factories[name]
            service = factory()

            # Store as singleton if it's a singleton factory
            if name in self._factories:  # Still in factories means it's a singleton
                self._singletons[name] = service
                del self._factories[name]  # Remove from factories
            else:
                self._services[name] = service

            logger.debug(f"Created service: {name}")
            return service

        raise KeyError(f"Service '{name}' not found")

    def has_service(self, name: str) -> bool:
        """Check if a service exists.

        Args:
            name: Service name

        Returns:
            True if service exists
        """
        return (
            name in self._services
            or name in self._singletons
            or name in self._factories
        )

    def inject(self, service_name: str):
        """Decorator to inject a service into a function or method.

        Args:
            service_name: Name of the service to inject

        Returns:
            Decorator function
        """

        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Get the service
                service = self.get_service(service_name)

                # Add service to kwargs
                kwargs[service_name] = service

                # Call the original function
                return func(*args, **kwargs)

            return wrapper

        return decorator

    def clear(self) -> None:
        """Clear all registered services."""
        self._services.clear()
        self._factories.clear()
        self._singletons.clear()
        logger.info("DependencyContainer cleared")


# Global dependency container instance
_container = DependencyContainer()


def get_container() -> DependencyContainer:
    """Get the global dependency container.

    Returns:
        Global dependency container instance
    """
    return _container


def register_service(name: str, service: Any) -> None:
    """Register a service in the global container.

    Args:
        name: Service name
        service: Service instance
    """
    _container.register_service(name, service)


def register_factory(name: str, factory: callable) -> None:
    """Register a service factory in the global container.

    Args:
        name: Service name
        factory: Factory function to create service
    """
    _container.register_factory(name, factory)


def register_singleton(name: str, factory: callable) -> None:
    """Register a singleton service factory in the global container.

    Args:
        name: Service name
        factory: Factory function to create service (called only once)
    """
    _container.register_singleton(name, factory)


def get_service(name: str) -> Any:
    """Get a service from the global container.

    Args:
        name: Service name

    Returns:
        Service instance
    """
    return _container.get_service(name)


def inject(service_name: str):
    """Decorator to inject a service from the global container.

    Args:
        service_name: Name of the service to inject

    Returns:
        Decorator function
    """
    return _container.inject(service_name)


def has_service(name: str) -> bool:
    """Check if a service exists in the global container.

    Args:
        name: Service name

    Returns:
        True if service exists
    """
    return _container.has_service(name)


def clear_container() -> None:
    """Clear the global dependency container."""
    _container.clear()


# Lazy import functions to avoid circular dependencies
def get_task_execution_engine():
    """Get the task execution engine with lazy loading."""
    if not has_service("task_execution_engine"):
        try:
            # Import here to avoid circular imports
            from .task_execution_engine import CeleryTaskExecutionEngine
            from opsvi_auto_forge.infrastructure.memory.graph.client import Neo4jClient
            from opsvi_auto_forge.config.settings import settings

            # Create Neo4j client
            neo4j_client = Neo4jClient(
                uri=settings.neo4j_uri,
                username=settings.neo4j_username,
                password=settings.neo4j_password,
            )

            # Create Redis client
            redis_client = redis.Redis.from_url(
                settings.redis_url,
                max_connections=settings.redis_max_connections,
                socket_connect_timeout=settings.redis_connection_timeout,
                decode_responses=True,
            )

            # Create and register the engine
            engine = CeleryTaskExecutionEngine(neo4j_client, redis_client)
            register_service("task_execution_engine", engine)
        except Exception as e:
            logger.warning(f"Could not create TaskExecutionEngine: {e}")
            # Register a placeholder service
            register_service("task_execution_engine", None)

    return get_service("task_execution_engine")


def get_task_execution_bridge():
    """Get the task execution bridge with lazy loading."""
    if not has_service("task_execution_bridge"):
        # Import here to avoid circular imports
        from .task_execution_bridge import TaskExecutionBridge

        # Create and register the bridge
        bridge = TaskExecutionBridge()
        register_service("task_execution_bridge", bridge)

    return get_service("task_execution_bridge")


def get_execution_coordinator():
    """Get the execution coordinator with lazy loading."""
    if not has_service("execution_coordinator"):
        # Import here to avoid circular imports
        from .execution_coordinator import ExecutionCoordinator

        # Create and register the coordinator
        coordinator = ExecutionCoordinator()
        register_service("execution_coordinator", coordinator)

    return get_service("execution_coordinator")


def get_task_router():
    """Get the task router with lazy loading."""
    if not has_service("task_router"):
        # Import here to avoid circular imports
        from .task_router import TaskRouter

        # Create and register the router
        router = TaskRouter()
        register_service("task_router", router)

    return get_service("task_router")


def get_task_state_manager():
    """Get the task state manager with lazy loading."""
    if not has_service("task_state_manager"):
        # Import here to avoid circular imports
        from .task_state_manager import TaskStateManager
        from opsvi_auto_forge.infrastructure.memory.graph.client import Neo4jClient
        from opsvi_auto_forge.config.settings import settings

        # Create Neo4j client
        neo4j_client = Neo4jClient(
            uri=settings.neo4j_uri,
            username=settings.neo4j_username,
            password=settings.neo4j_password,
        )

        # Create Redis client
        redis_client = redis.Redis.from_url(
            settings.redis_url,
            max_connections=settings.redis_max_connections,
            socket_connect_timeout=settings.redis_connection_timeout,
            decode_responses=True,
        )

        # Create and register the state manager
        state_manager = TaskStateManager(neo4j_client, redis_client)
        register_service("task_state_manager", state_manager)

    return get_service("task_state_manager")


def get_result_collector():
    """Get the result collector with lazy loading."""
    if not has_service("result_collector"):
        # Import here to avoid circular imports
        from .result_collector import ResultCollector
        from opsvi_auto_forge.infrastructure.memory.graph.client import Neo4jClient
        from opsvi_auto_forge.config.settings import settings

        # Create Neo4j client
        neo4j_client = Neo4jClient(
            uri=settings.neo4j_uri,
            username=settings.neo4j_username,
            password=settings.neo4j_password,
        )

        # Create and register the result collector
        collector = ResultCollector(neo4j_client)
        register_service("result_collector", collector)

    return get_service("result_collector")


# Initialize core services
def initialize_core_services():
    """Initialize core services in the dependency container."""
    try:
        # Register lazy loading functions
        register_factory("task_execution_bridge", get_task_execution_bridge)
        register_factory("execution_coordinator", get_execution_coordinator)
        register_factory("task_router", get_task_router)
        register_factory("task_state_manager", get_task_state_manager)
        register_factory("result_collector", get_result_collector)

        # Don't register task_execution_engine initially to avoid circular imports
        logger.info("Core services registered in dependency container")

    except Exception as e:
        logger.error(f"Failed to initialize core services: {e}")
        raise


# Auto-initialize when module is imported
initialize_core_services()

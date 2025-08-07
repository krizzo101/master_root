"""
Dependency injection pattern implementation for OPSVI Foundation.

Provides a robust dependency injection container for managing object dependencies.
"""

import inspect
import logging
from collections.abc import Callable
from contextlib import contextmanager
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, TypeVar

logger = logging.getLogger(__name__)


class LifecycleScope(Enum):
    """Dependency lifecycle scopes."""

    SINGLETON = "singleton"
    TRANSIENT = "transient"
    REQUEST = "request"
    SESSION = "session"


class DependencyResolutionError(Exception):
    """Exception raised when dependency resolution fails."""


@dataclass
class ServiceDescriptor:
    """Descriptor for a service registration."""

    service_type: type
    implementation_type: type | None = None
    factory: Callable | None = None
    instance: Any | None = None
    scope: LifecycleScope = LifecycleScope.TRANSIENT
    metadata: dict[str, Any] = field(default_factory=dict)


T = TypeVar("T")


class DependencyContainer:
    """Dependency injection container."""

    def __init__(self) -> None:
        self._services: dict[type, ServiceDescriptor] = {}
        self._scoped_instances: dict[type, Any] = {}
        self._singleton_instances: dict[type, Any] = {}
        self._scope_stack: list[dict[type, Any]] = []

    def register(
        self,
        service_type: type[T],
        implementation_type: type[T] | None = None,
        factory: Callable | None = None,
        scope: LifecycleScope = LifecycleScope.TRANSIENT,
    ) -> None:
        """Register a service with the container."""
        descriptor = ServiceDescriptor(
            service_type=service_type,
            implementation_type=implementation_type,
            factory=factory,
            scope=scope,
        )
        self._services[service_type] = descriptor
        logger.debug(
            f"Registered service: {service_type.__name__} (scope: {scope.value})",
        )

    def register_singleton(
        self,
        service_type: type[T],
        implementation_type: type[T] | None = None,
        factory: Callable | None = None,
    ) -> None:
        """Register a singleton service."""
        self.register(
            service_type,
            implementation_type,
            factory,
            LifecycleScope.SINGLETON,
        )

    def register_transient(
        self,
        service_type: type[T],
        implementation_type: type[T] | None = None,
        factory: Callable | None = None,
    ) -> None:
        """Register a transient service."""
        self.register(
            service_type,
            implementation_type,
            factory,
            LifecycleScope.TRANSIENT,
        )

    def register_scoped(
        self,
        service_type: type[T],
        implementation_type: type[T] | None = None,
        factory: Callable | None = None,
    ) -> None:
        """Register a scoped service."""
        self.register(
            service_type,
            implementation_type,
            factory,
            LifecycleScope.REQUEST,
        )

    def resolve(self, service_type: type[T]) -> T:
        """Resolve a service instance."""
        if service_type not in self._services:
            raise DependencyResolutionError(
                f"Service {service_type.__name__} not registered",
            )

        descriptor = self._services[service_type]

        # Check for existing instance based on scope
        if descriptor.scope == LifecycleScope.SINGLETON:
            if service_type in self._singleton_instances:
                return self._singleton_instances[service_type]
        elif descriptor.scope == LifecycleScope.REQUEST:
            if self._scope_stack and service_type in self._scope_stack[-1]:
                return self._scope_stack[-1][service_type]

        # Create new instance
        instance = self._create_instance(descriptor)

        # Store instance based on scope
        if descriptor.scope == LifecycleScope.SINGLETON:
            self._singleton_instances[service_type] = instance
        elif descriptor.scope == LifecycleScope.REQUEST:
            if self._scope_stack:
                self._scope_stack[-1][service_type] = instance

        return instance

    def _create_instance(self, descriptor: ServiceDescriptor) -> Any:
        """Create a new instance of a service."""
        try:
            if descriptor.factory is not None:
                # Use factory function
                return descriptor.factory(self)
            if descriptor.implementation_type is not None:
                # Use implementation type
                return self._create_instance_from_type(descriptor.implementation_type)
            # Use service type itself
            return self._create_instance_from_type(descriptor.service_type)
        except Exception as e:
            logger.error(
                f"Error creating instance of {descriptor.service_type.__name__}: {e}",
            )
            raise DependencyResolutionError(f"Failed to create instance: {e}")

    def _create_instance_from_type(self, type_class: type) -> Any:
        """Create an instance from a type, resolving dependencies."""
        # Get constructor parameters
        signature = inspect.signature(type_class.__init__)
        parameters = {}

        for param_name, param in signature.parameters.items():
            if param_name == "self":
                continue

            if param.annotation != inspect.Parameter.empty:
                try:
                    parameters[param_name] = self.resolve(param.annotation)
                except DependencyResolutionError:
                    if param.default == inspect.Parameter.empty:
                        raise DependencyResolutionError(
                            f"Cannot resolve required dependency {param_name} of type {param.annotation.__name__}",
                        )
            elif param.default != inspect.Parameter.empty:
                parameters[param_name] = param.default
            else:
                raise DependencyResolutionError(
                    f"Cannot resolve parameter {param_name} without type annotation",
                )

        return type_class(**parameters)

    @contextmanager
    def scope(self):
        """Create a new scope for scoped services."""
        scope_instances = {}
        self._scope_stack.append(scope_instances)
        try:
            yield self
        finally:
            self._scope_stack.pop()

    def is_registered(self, service_type: type) -> bool:
        """Check if a service is registered."""
        return service_type in self._services

    def get_registered_services(self) -> list[type]:
        """Get all registered service types."""
        return list(self._services.keys())

    def clear(self) -> None:
        """Clear all registrations and instances."""
        self._services.clear()
        self._scoped_instances.clear()
        self._singleton_instances.clear()
        self._scope_stack.clear()
        logger.info("Dependency container cleared")


class Injectable:
    """Decorator for marking classes as injectable."""

    def __init__(self, scope: LifecycleScope = LifecycleScope.TRANSIENT) -> None:
        self.scope = scope

    def __call__(self, cls: type[T]) -> type[T]:
        """Mark a class as injectable."""
        cls._injectable_scope = self.scope
        return cls


def inject(service_type: type[T]) -> T:
    """Decorator for injecting dependencies into function parameters."""

    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            # This is a simplified version - in practice, you'd need more complex logic
            # to handle dependency injection in function calls
            container = getattr(func, "_container", None)
            if container is None:
                raise DependencyResolutionError("No container available for injection")

            # Inject the dependency
            injected_value = container.resolve(service_type)

            # Add to kwargs
            param_name = service_type.__name__.lower()
            kwargs[param_name] = injected_value

            return func(*args, **kwargs)

        return wrapper

    return decorator


class ServiceProvider:
    """Service provider interface."""

    def __init__(self, container: DependencyContainer) -> None:
        self.container = container

    def get_service(self, service_type: type[T]) -> T:
        """Get a service instance."""
        return self.container.resolve(service_type)

    def get_required_service(self, service_type: type[T]) -> T:
        """Get a required service instance."""
        if not self.container.is_registered(service_type):
            raise DependencyResolutionError(
                f"Required service {service_type.__name__} not registered",
            )
        return self.container.resolve(service_type)

    def get_optional_service(self, service_type: type[T]) -> T | None:
        """Get an optional service instance."""
        if not self.container.is_registered(service_type):
            return None
        return self.container.resolve(service_type)


class ServiceCollection:
    """Builder for configuring services."""

    def __init__(self) -> None:
        self.container = DependencyContainer()

    def add_singleton(
        self,
        service_type: type[T],
        implementation_type: type[T] | None = None,
        factory: Callable | None = None,
    ) -> "ServiceCollection":
        """Add a singleton service."""
        self.container.register_singleton(service_type, implementation_type, factory)
        return self

    def add_transient(
        self,
        service_type: type[T],
        implementation_type: type[T] | None = None,
        factory: Callable | None = None,
    ) -> "ServiceCollection":
        """Add a transient service."""
        self.container.register_transient(service_type, implementation_type, factory)
        return self

    def add_scoped(
        self,
        service_type: type[T],
        implementation_type: type[T] | None = None,
        factory: Callable | None = None,
    ) -> "ServiceCollection":
        """Add a scoped service."""
        self.container.register_scoped(service_type, implementation_type, factory)
        return self

    def build_service_provider(self) -> ServiceProvider:
        """Build the service provider."""
        return ServiceProvider(self.container)


# Global container instance
_container: DependencyContainer | None = None


def get_container() -> DependencyContainer:
    """Get the global dependency container."""
    global _container
    if _container is None:
        _container = DependencyContainer()
    return _container


def set_container(container: DependencyContainer) -> None:
    """Set the global dependency container."""
    global _container
    _container = container


def resolve(service_type: type[T]) -> T:
    """Resolve a service from the global container."""
    return get_container().resolve(service_type)

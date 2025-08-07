"""
Factory patterns and object creation utilities.

Provides factory methods, abstract factories, and dependency injection
patterns for flexible object creation and configuration.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from enum import Enum
from typing import Any, TypeVar

from opsvi_foundation.patterns import ComponentError


class FactoryError(ComponentError):
    """Raised when factory operation fails."""


class FactoryType(Enum):
    """Factory types."""

    SIMPLE = "simple"
    ABSTRACT = "abstract"
    BUILDER = "builder"
    PROTOTYPE = "prototype"


T = TypeVar("T")


class Factory(ABC):
    """Abstract base class for factories."""

    def __init__(self, name: str):
        """
        Initialize factory.

        Args:
            name: Factory name
        """
        self.name = name
        self.registry: dict[str, type[T]] = {}

    @abstractmethod
    def create(self, *args, **kwargs) -> T:
        """
        Create an instance.

        Args:
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Created instance
        """

    def register(self, name: str, cls: type[T]) -> None:
        """
        Register a class with the factory.

        Args:
            name: Registration name
            cls: Class to register
        """
        self.registry[name] = cls

    def unregister(self, name: str) -> None:
        """
        Unregister a class from the factory.

        Args:
            name: Registration name
        """
        self.registry.pop(name, None)

    def get_registered(self, name: str) -> type[T] | None:
        """
        Get registered class by name.

        Args:
            name: Registration name

        Returns:
            Registered class or None if not found
        """
        return self.registry.get(name)

    def list_registered(self) -> list[str]:
        """
        List all registered names.

        Returns:
            List of registered names
        """
        return list(self.registry.keys())


class SimpleFactory(Factory):
    """Simple factory implementation."""

    def __init__(self, name: str, base_class: type[T] | None = None):
        """
        Initialize simple factory.

        Args:
            name: Factory name
            base_class: Base class for validation
        """
        super().__init__(name)
        self.base_class = base_class

    def create(self, name: str, *args, **kwargs) -> T:
        """
        Create instance by name.

        Args:
            name: Registration name
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Created instance

        Raises:
            FactoryError: If class not found or invalid
        """
        if name not in self.registry:
            raise FactoryError(
                f"Class '{name}' not registered in factory '{self.name}'",
            )

        cls = self.registry[name]

        # Validate base class if specified
        if self.base_class and not issubclass(cls, self.base_class):
            raise FactoryError(
                f"Class '{name}' is not a subclass of {self.base_class.__name__}",
            )

        try:
            return cls(*args, **kwargs)
        except Exception as e:
            raise FactoryError(f"Failed to create instance of '{name}': {e}") from e

    def create_with_config(self, name: str, config: dict[str, Any]) -> T:
        """
        Create instance with configuration.

        Args:
            name: Registration name
            config: Configuration dictionary

        Returns:
            Created instance
        """
        return self.create(name, **config)


class AbstractFactory(Factory):
    """Abstract factory implementation."""

    def __init__(self, name: str):
        """Initialize abstract factory."""
        super().__init__(name)
        self.factories: dict[str, Factory] = {}

    def register_factory(self, category: str, factory: Factory) -> None:
        """
        Register a factory for a category.

        Args:
            category: Category name
            factory: Factory instance
        """
        self.factories[category] = factory

    def create(self, category: str, name: str, *args, **kwargs) -> T:
        """
        Create instance by category and name.

        Args:
            category: Category name
            name: Registration name
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Created instance

        Raises:
            FactoryError: If category or class not found
        """
        if category not in self.factories:
            raise FactoryError(
                f"Category '{category}' not found in factory '{self.name}'",
            )

        factory = self.factories[category]
        return factory.create(name, *args, **kwargs)

    def get_factory(self, category: str) -> Factory | None:
        """
        Get factory for category.

        Args:
            category: Category name

        Returns:
            Factory instance or None if not found
        """
        return self.factories.get(category)

    def list_categories(self) -> list[str]:
        """
        List all categories.

        Returns:
            List of category names
        """
        return list(self.factories.keys())


class Builder:
    """Builder pattern implementation."""

    def __init__(self):
        """Initialize builder."""
        self._parts: dict[str, Any] = {}

    def add_part(self, name: str, value: Any) -> Builder:
        """
        Add a part to the builder.

        Args:
            name: Part name
            value: Part value

        Returns:
            Self for chaining
        """
        self._parts[name] = value
        return self

    def add_parts(self, parts: dict[str, Any]) -> Builder:
        """
        Add multiple parts to the builder.

        Args:
            parts: Dictionary of parts

        Returns:
            Self for chaining
        """
        self._parts.update(parts)
        return self

    def get_part(self, name: str) -> Any:
        """
        Get a part from the builder.

        Args:
            name: Part name

        Returns:
            Part value
        """
        return self._parts.get(name)

    def has_part(self, name: str) -> bool:
        """
        Check if builder has a part.

        Args:
            name: Part name

        Returns:
            True if part exists
        """
        return name in self._parts

    def remove_part(self, name: str) -> Builder:
        """
        Remove a part from the builder.

        Args:
            name: Part name

        Returns:
            Self for chaining
        """
        self._parts.pop(name, None)
        return self

    def clear(self) -> Builder:
        """
        Clear all parts.

        Returns:
            Self for chaining
        """
        self._parts.clear()
        return self

    def build(self, cls: type[T]) -> T:
        """
        Build an instance using the collected parts.

        Args:
            cls: Class to instantiate

        Returns:
            Built instance
        """
        try:
            return cls(**self._parts)
        except Exception as e:
            raise FactoryError(
                f"Failed to build instance of {cls.__name__}: {e}",
            ) from e


class BuilderFactory(Factory):
    """Factory using builder pattern."""

    def __init__(self, name: str):
        """Initialize builder factory."""
        super().__init__(name)

    def create(self, name: str, *args, **kwargs) -> T:
        """
        Create instance using builder pattern.

        Args:
            name: Registration name
            *args: Positional arguments (ignored)
            **kwargs: Keyword arguments for parts

        Returns:
            Created instance
        """
        if name not in self.registry:
            raise FactoryError(
                f"Class '{name}' not registered in factory '{self.name}'",
            )

        cls = self.registry[name]
        builder = Builder()
        builder.add_parts(kwargs)
        return builder.build(cls)


class Prototype:
    """Prototype pattern implementation."""

    def __init__(self):
        """Initialize prototype."""
        self._prototypes: dict[str, Any] = {}

    def register_prototype(self, name: str, prototype: Any) -> None:
        """
        Register a prototype.

        Args:
            name: Prototype name
            prototype: Prototype instance
        """
        self._prototypes[name] = prototype

    def clone(self, name: str) -> Any:
        """
        Clone a prototype.

        Args:
            name: Prototype name

        Returns:
            Cloned instance

        Raises:
            FactoryError: If prototype not found
        """
        if name not in self._prototypes:
            raise FactoryError(f"Prototype '{name}' not found")

        prototype = self._prototypes[name]

        try:
            # Try to use copy method if available
            if hasattr(prototype, "copy"):
                return prototype.copy()
            if hasattr(prototype, "clone"):
                return prototype.clone()
            # Fall back to copy.deepcopy
            import copy

            return copy.deepcopy(prototype)
        except Exception as e:
            raise FactoryError(f"Failed to clone prototype '{name}': {e}") from e

    def list_prototypes(self) -> list[str]:
        """
        List all prototype names.

        Returns:
            List of prototype names
        """
        return list(self._prototypes.keys())


class PrototypeFactory(Factory):
    """Factory using prototype pattern."""

    def __init__(self, name: str):
        """Initialize prototype factory."""
        super().__init__(name)
        self.prototype = Prototype()

    def create(self, name: str, *args, **kwargs) -> T:
        """
        Create instance by cloning prototype.

        Args:
            name: Prototype name
            *args: Positional arguments (ignored)
            **kwargs: Keyword arguments for customization

        Returns:
            Created instance
        """
        instance = self.prototype.clone(name)

        # Apply customizations
        for key, value in kwargs.items():
            if hasattr(instance, key):
                setattr(instance, key, value)

        return instance

    def register_prototype(self, name: str, prototype: T) -> None:
        """
        Register a prototype.

        Args:
            name: Prototype name
            prototype: Prototype instance
        """
        self.prototype.register_prototype(name, prototype)


class DependencyInjector:
    """Dependency injection container."""

    def __init__(self):
        """Initialize dependency injector."""
        self.services: dict[str, Any] = {}
        self.factories: dict[str, Callable] = {}
        self.singletons: dict[str, Any] = {}

    def register_service(self, name: str, service: Any) -> None:
        """
        Register a service instance.

        Args:
            name: Service name
            service: Service instance
        """
        self.services[name] = service

    def register_factory(self, name: str, factory: Callable) -> None:
        """
        Register a service factory.

        Args:
            name: Service name
            factory: Factory function
        """
        self.factories[name] = factory

    def register_singleton(self, name: str, factory: Callable) -> None:
        """
        Register a singleton factory.

        Args:
            name: Service name
            factory: Factory function
        """
        self.factories[name] = factory
        # Singleton will be created on first access

    def get_service(self, name: str) -> Any:
        """
        Get a service by name.

        Args:
            name: Service name

        Returns:
            Service instance

        Raises:
            FactoryError: If service not found
        """
        # Check if service is already registered
        if name in self.services:
            return self.services[name]

        # Check if singleton exists
        if name in self.singletons:
            return self.singletons[name]

        # Check if factory exists
        if name in self.factories:
            factory = self.factories[name]

            # Check if this is a singleton
            if name not in self.singletons:
                instance = factory()
                self.singletons[name] = instance
                return instance
            return self.singletons[name]

        raise FactoryError(f"Service '{name}' not found")

    def inject_dependencies(self, obj: Any) -> None:
        """
        Inject dependencies into an object.

        Args:
            obj: Object to inject dependencies into
        """
        # Get all attributes that start with 'inject_'
        for attr_name in dir(obj):
            if attr_name.startswith("inject_"):
                service_name = attr_name[7:]  # Remove 'inject_' prefix
                service = self.get_service(service_name)
                setattr(obj, service_name, service)

    def create_with_dependencies(self, cls: type[T], **kwargs) -> T:
        """
        Create an instance and inject dependencies.

        Args:
            cls: Class to instantiate
            **kwargs: Additional keyword arguments

        Returns:
            Created instance with dependencies injected
        """
        instance = cls(**kwargs)
        self.inject_dependencies(instance)
        return instance


# Global dependency injector
dependency_injector = DependencyInjector()


def inject(name: str):
    """
    Decorator for dependency injection.

    Args:
        name: Service name to inject
    """

    def decorator(func):
        def wrapper(*args, **kwargs):
            service = dependency_injector.get_service(name)
            return func(service, *args, **kwargs)

        return wrapper

    return decorator


def singleton(name: str):
    """
    Decorator for registering a singleton service.

    Args:
        name: Service name
    """

    def decorator(cls):
        dependency_injector.register_singleton(name, cls)
        return cls

    return decorator


def factory_method(name: str):
    """
    Decorator for registering a factory method.

    Args:
        name: Factory method name
    """

    def decorator(func):
        dependency_injector.register_factory(name, func)
        return func

    return decorator

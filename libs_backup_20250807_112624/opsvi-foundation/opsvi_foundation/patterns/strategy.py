"""
Strategy pattern implementation for OPSVI Foundation.

Provides a flexible way to select algorithms at runtime.
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Generic, TypeVar

logger = logging.getLogger(__name__)


class StrategyType(Enum):
    """Common strategy types for the application."""

    CACHING = "caching"
    ENCRYPTION = "encryption"
    COMPRESSION = "compression"
    SERIALIZATION = "serialization"
    VALIDATION = "validation"
    AUTHENTICATION = "authentication"
    RATE_LIMITING = "rate_limiting"
    RETRY = "retry"
    FALLBACK = "fallback"


T = TypeVar("T")


class Strategy(ABC, Generic[T]):
    """Abstract base class for strategies."""

    @abstractmethod
    def execute(self, context: Any) -> T:
        """Execute the strategy with given context."""

    @abstractmethod
    def get_name(self) -> str:
        """Get the strategy name."""


class StrategyContext:
    """Context class that uses strategies."""

    def __init__(self, strategy: Strategy) -> None:
        self._strategy = strategy
        logger.debug(f"Strategy context initialized with: {strategy.get_name()}")

    def set_strategy(self, strategy: Strategy) -> None:
        """Set a new strategy."""
        self._strategy = strategy
        logger.debug(f"Strategy changed to: {strategy.get_name()}")

    def execute_strategy(self, context: Any) -> Any:
        """Execute the current strategy."""
        try:
            result = self._strategy.execute(context)
            logger.debug(f"Strategy {self._strategy.get_name()} executed successfully")
            return result
        except Exception as e:
            logger.error(f"Strategy {self._strategy.get_name()} failed: {e}")
            raise


class StrategyRegistry:
    """Registry for managing multiple strategies."""

    def __init__(self) -> None:
        self._strategies: dict[str, dict[str, type[Strategy]]] = {}
        self._default_strategies: dict[str, str] = {}

    def register(
        self,
        strategy_type: str,
        name: str,
        strategy_class: type[Strategy],
    ) -> None:
        """Register a strategy."""
        if strategy_type not in self._strategies:
            self._strategies[strategy_type] = {}
        self._strategies[strategy_type][name] = strategy_class
        logger.info(f"Registered strategy: {strategy_type}.{name}")

    def unregister(self, strategy_type: str, name: str) -> None:
        """Unregister a strategy."""
        if (
            strategy_type in self._strategies
            and name in self._strategies[strategy_type]
        ):
            del self._strategies[strategy_type][name]
            logger.info(f"Unregistered strategy: {strategy_type}.{name}")

    def get_strategy(self, strategy_type: str, name: str) -> Strategy:
        """Get a strategy instance by type and name."""
        if strategy_type not in self._strategies:
            raise ValueError(f"Unknown strategy type: {strategy_type}")

        if name not in self._strategies[strategy_type]:
            raise ValueError(f"Unknown strategy: {strategy_type}.{name}")

        strategy_class = self._strategies[strategy_type][name]
        return strategy_class()

    def get_default_strategy(self, strategy_type: str) -> Strategy:
        """Get the default strategy for a type."""
        if strategy_type not in self._default_strategies:
            raise ValueError(f"No default strategy for type: {strategy_type}")

        default_name = self._default_strategies[strategy_type]
        return self.get_strategy(strategy_type, default_name)

    def set_default_strategy(self, strategy_type: str, name: str) -> None:
        """Set the default strategy for a type."""
        if (
            strategy_type not in self._strategies
            or name not in self._strategies[strategy_type]
        ):
            raise ValueError(f"Strategy {strategy_type}.{name} not registered")

        self._default_strategies[strategy_type] = name
        logger.info(f"Set default strategy for {strategy_type}: {name}")

    def list_strategies(self, strategy_type: str | None = None) -> dict[str, Any]:
        """List all registered strategies."""
        if strategy_type is None:
            return {
                strategy_type: list(strategies.keys())
                for strategy_type, strategies in self._strategies.items()
            }

        if strategy_type not in self._strategies:
            return {}

        return {
            name: strategy_class.__name__
            for name, strategy_class in self._strategies[strategy_type].items()
        }


# Global strategy registry
strategy_registry = StrategyRegistry()


class StrategyFactory:
    """Factory for creating strategy instances."""

    @staticmethod
    def create_strategy(strategy_type: str, name: str) -> Strategy:
        """Create a strategy instance."""
        return strategy_registry.get_strategy(strategy_type, name)

    @staticmethod
    def create_default_strategy(strategy_type: str) -> Strategy:
        """Create a default strategy instance."""
        return strategy_registry.get_default_strategy(strategy_type)


@dataclass
class StrategyConfig:
    """Configuration for strategy selection."""

    strategy_type: str
    strategy_name: str
    parameters: dict[str, Any] = None

    def __post_init__(self) -> None:
        if self.parameters is None:
            self.parameters = {}


class StrategySelector:
    """Intelligent strategy selector based on context."""

    def __init__(self) -> None:
        self._selection_rules: dict[str, callable] = {}

    def add_rule(self, strategy_type: str, rule: callable) -> None:
        """Add a selection rule for a strategy type."""
        self._selection_rules[strategy_type] = rule
        logger.debug(f"Added selection rule for {strategy_type}")

    def select_strategy(self, strategy_type: str, context: Any) -> Strategy:
        """Select the best strategy based on context."""
        if strategy_type in self._selection_rules:
            rule = self._selection_rules[strategy_type]
            strategy_name = rule(context)
            return strategy_registry.get_strategy(strategy_type, strategy_name)

        # Fall back to default strategy
        return strategy_registry.get_default_strategy(strategy_type)


# Example strategy implementations


class CachingStrategy(Strategy[bool]):
    """Base class for caching strategies."""

    def get_name(self) -> str:
        return "base_caching"


class MemoryCachingStrategy(CachingStrategy):
    """In-memory caching strategy."""

    def execute(self, context: Any) -> bool:
        # Implementation for memory caching
        return True

    def get_name(self) -> str:
        return "memory"


class RedisCachingStrategy(CachingStrategy):
    """Redis caching strategy."""

    def execute(self, context: Any) -> bool:
        # Implementation for Redis caching
        return True

    def get_name(self) -> str:
        return "redis"


class EncryptionStrategy(Strategy[bytes]):
    """Base class for encryption strategies."""

    def get_name(self) -> str:
        return "base_encryption"


class AESEncryptionStrategy(EncryptionStrategy):
    """AES encryption strategy."""

    def execute(self, context: Any) -> bytes:
        # Implementation for AES encryption
        return b"encrypted_data"

    def get_name(self) -> str:
        return "aes"


class ChaCha20EncryptionStrategy(EncryptionStrategy):
    """ChaCha20 encryption strategy."""

    def execute(self, context: Any) -> bytes:
        # Implementation for ChaCha20 encryption
        return b"encrypted_data"

    def get_name(self) -> str:
        return "chacha20"

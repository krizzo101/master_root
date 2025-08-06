"""
Fallback strategies and graceful degradation.

Provides fallback mechanisms, graceful degradation, and fallback chains
for handling failures and maintaining system availability.
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from typing import Any, TypeVar

from opsvi_foundation.patterns import ComponentError


class FallbackError(ComponentError):
    """Raised when fallback strategy fails."""


class FallbackStrategy(Enum):
    """Fallback strategies."""

    FAST_FAIL = "fast_fail"
    RETRY = "retry"
    CACHE = "cache"
    DEFAULT_VALUE = "default_value"
    ALTERNATIVE_SERVICE = "alternative_service"
    DEGRADED_MODE = "degraded_mode"


@dataclass
class FallbackConfig:
    """Configuration for fallback strategies."""

    strategy: FallbackStrategy = FallbackStrategy.FAST_FAIL
    max_attempts: int = 3
    timeout: float = 30.0
    cache_ttl: float = 300.0  # 5 minutes
    default_value: Any = None
    alternative_services: list[str] = None


T = TypeVar("T")


class FallbackHandler:
    """Base fallback handler."""

    def __init__(self, config: FallbackConfig):
        """
        Initialize fallback handler.

        Args:
            config: Fallback configuration
        """
        self.config = config

    async def execute(self, func: Callable[..., T], *args, **kwargs) -> T:
        """
        Execute function with fallback strategy.

        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            Function result or fallback value

        Raises:
            FallbackError: If all fallback strategies fail
        """
        raise NotImplementedError("Subclasses must implement execute")


class FastFailHandler(FallbackHandler):
    """Fast fail fallback handler."""

    async def execute(self, func: Callable[..., T], *args, **kwargs) -> T:
        """
        Execute function with fast fail strategy.

        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            Function result

        Raises:
            FallbackError: If function fails
        """
        try:
            if asyncio.iscoroutinefunction(func):
                return await asyncio.wait_for(
                    func(*args, **kwargs),
                    timeout=self.config.timeout,
                )
            loop = asyncio.get_event_loop()
            return await asyncio.wait_for(
                loop.run_in_executor(None, func, *args, **kwargs),
                timeout=self.config.timeout,
            )
        except Exception as e:
            raise FallbackError(f"Fast fail strategy failed: {e!s}") from e


class RetryHandler(FallbackHandler):
    """Retry fallback handler."""

    async def execute(self, func: Callable[..., T], *args, **kwargs) -> T:
        """
        Execute function with retry strategy.

        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            Function result

        Raises:
            FallbackError: If all retry attempts fail
        """
        last_exception = None

        for attempt in range(self.config.max_attempts):
            try:
                if asyncio.iscoroutinefunction(func):
                    return await asyncio.wait_for(
                        func(*args, **kwargs),
                        timeout=self.config.timeout,
                    )
                loop = asyncio.get_event_loop()
                return await asyncio.wait_for(
                    loop.run_in_executor(None, func, *args, **kwargs),
                    timeout=self.config.timeout,
                )
            except Exception as e:
                last_exception = e
                if attempt < self.config.max_attempts - 1:
                    # Exponential backoff
                    await asyncio.sleep(2**attempt)
                    continue

        raise FallbackError(
            f"Retry strategy failed after {self.config.max_attempts} attempts",
        ) from last_exception


class CacheHandler(FallbackHandler):
    """Cache fallback handler."""

    def __init__(self, config: FallbackConfig):
        """Initialize cache handler."""
        super().__init__(config)
        self.cache: dict[str, Any] = {}
        self.cache_timestamps: dict[str, float] = {}

    async def execute(self, func: Callable[..., T], *args, **kwargs) -> T:
        """
        Execute function with cache strategy.

        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            Function result or cached value
        """
        import hashlib
        import pickle
        import time

        # Generate cache key
        key_data = (func.__name__, args, tuple(sorted(kwargs.items())))
        key = hashlib.md5(pickle.dumps(key_data)).hexdigest()

        # Check cache
        current_time = time.time()
        if key in self.cache:
            timestamp = self.cache_timestamps.get(key, 0)
            if current_time - timestamp < self.config.cache_ttl:
                return self.cache[key]

        try:
            # Execute function
            if asyncio.iscoroutinefunction(func):
                result = await asyncio.wait_for(
                    func(*args, **kwargs),
                    timeout=self.config.timeout,
                )
            else:
                loop = asyncio.get_event_loop()
                result = await asyncio.wait_for(
                    loop.run_in_executor(None, func, *args, **kwargs),
                    timeout=self.config.timeout,
                )

            # Cache result
            self.cache[key] = result
            self.cache_timestamps[key] = current_time

            return result
        except Exception:
            # Return cached value if available, even if expired
            if key in self.cache:
                return self.cache[key]

            # Return default value
            return self.config.default_value


class DefaultValueHandler(FallbackHandler):
    """Default value fallback handler."""

    async def execute(self, func: Callable[..., T], *args, **kwargs) -> T:
        """
        Execute function with default value strategy.

        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            Function result or default value
        """
        try:
            if asyncio.iscoroutinefunction(func):
                return await asyncio.wait_for(
                    func(*args, **kwargs),
                    timeout=self.config.timeout,
                )
            loop = asyncio.get_event_loop()
            return await asyncio.wait_for(
                loop.run_in_executor(None, func, *args, **kwargs),
                timeout=self.config.timeout,
            )
        except Exception:
            return self.config.default_value


class AlternativeServiceHandler(FallbackHandler):
    """Alternative service fallback handler."""

    def __init__(self, config: FallbackConfig, services: dict[str, Callable]):
        """
        Initialize alternative service handler.

        Args:
            config: Fallback configuration
            services: Dictionary of service name to function mapping
        """
        super().__init__(config)
        self.services = services

    async def execute(self, func: Callable[..., T], *args, **kwargs) -> T:
        """
        Execute function with alternative service strategy.

        Args:
            func: Primary function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            Function result from primary or alternative service

        Raises:
            FallbackError: If all services fail
        """
        # Try primary function first
        try:
            if asyncio.iscoroutinefunction(func):
                return await asyncio.wait_for(
                    func(*args, **kwargs),
                    timeout=self.config.timeout,
                )
            loop = asyncio.get_event_loop()
            return await asyncio.wait_for(
                loop.run_in_executor(None, func, *args, **kwargs),
                timeout=self.config.timeout,
            )
        except Exception:
            pass

        # Try alternative services
        for service_name, service_func in self.services.items():
            try:
                if asyncio.iscoroutinefunction(service_func):
                    return await asyncio.wait_for(
                        service_func(*args, **kwargs),
                        timeout=self.config.timeout,
                    )
                loop = asyncio.get_event_loop()
                return await asyncio.wait_for(
                    loop.run_in_executor(None, service_func, *args, **kwargs),
                    timeout=self.config.timeout,
                )
            except Exception:
                continue

        # All services failed, return default value
        return self.config.default_value


class DegradedModeHandler(FallbackHandler):
    """Degraded mode fallback handler."""

    def __init__(self, config: FallbackConfig, degraded_func: Callable):
        """
        Initialize degraded mode handler.

        Args:
            config: Fallback configuration
            degraded_func: Function to execute in degraded mode
        """
        super().__init__(config)
        self.degraded_func = degraded_func

    async def execute(self, func: Callable[..., T], *args, **kwargs) -> T:
        """
        Execute function with degraded mode strategy.

        Args:
            func: Primary function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            Function result from primary or degraded function
        """
        try:
            if asyncio.iscoroutinefunction(func):
                return await asyncio.wait_for(
                    func(*args, **kwargs),
                    timeout=self.config.timeout,
                )
            loop = asyncio.get_event_loop()
            return await asyncio.wait_for(
                loop.run_in_executor(None, func, *args, **kwargs),
                timeout=self.config.timeout,
            )
        except Exception:
            # Execute degraded function
            if asyncio.iscoroutinefunction(self.degraded_func):
                return await asyncio.wait_for(
                    self.degraded_func(*args, **kwargs),
                    timeout=self.config.timeout,
                )
            loop = asyncio.get_event_loop()
            return await asyncio.wait_for(
                loop.run_in_executor(None, self.degraded_func, *args, **kwargs),
                timeout=self.config.timeout,
            )


class FallbackChain:
    """Chain of fallback strategies."""

    def __init__(self, handlers: list[FallbackHandler]):
        """
        Initialize fallback chain.

        Args:
            handlers: List of fallback handlers in order of preference
        """
        self.handlers = handlers

    async def execute(self, func: Callable[..., T], *args, **kwargs) -> T:
        """
        Execute function with fallback chain.

        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            Function result from first successful handler

        Raises:
            FallbackError: If all handlers fail
        """
        last_exception = None

        for handler in self.handlers:
            try:
                return await handler.execute(func, *args, **kwargs)
            except Exception as e:
                last_exception = e
                continue

        raise FallbackError("All fallback strategies failed") from last_exception


class FallbackManager:
    """Manager for fallback strategies."""

    def __init__(self):
        """Initialize fallback manager."""
        self.handlers: dict[str, FallbackHandler] = {}
        self.chains: dict[str, FallbackChain] = {}

    def add_handler(self, name: str, handler: FallbackHandler) -> None:
        """
        Add fallback handler.

        Args:
            name: Handler name
            handler: Fallback handler
        """
        self.handlers[name] = handler

    def create_chain(self, name: str, handler_names: list[str]) -> FallbackChain:
        """
        Create fallback chain from handler names.

        Args:
            name: Chain name
            handler_names: List of handler names in order

        Returns:
            Created fallback chain
        """
        handlers = [
            self.handlers[name] for name in handler_names if name in self.handlers
        ]
        chain = FallbackChain(handlers)
        self.chains[name] = chain
        return chain

    def get_handler(self, name: str) -> FallbackHandler | None:
        """Get fallback handler by name."""
        return self.handlers.get(name)

    def get_chain(self, name: str) -> FallbackChain | None:
        """Get fallback chain by name."""
        return self.chains.get(name)

    async def execute_with_handler(
        self,
        name: str,
        func: Callable[..., T],
        *args,
        **kwargs,
    ) -> T:
        """
        Execute function with named handler.

        Args:
            name: Handler name
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            Function result

        Raises:
            ValueError: If handler not found
        """
        handler = self.get_handler(name)
        if not handler:
            raise ValueError(f"Fallback handler '{name}' not found")

        return await handler.execute(func, *args, **kwargs)

    async def execute_with_chain(
        self,
        name: str,
        func: Callable[..., T],
        *args,
        **kwargs,
    ) -> T:
        """
        Execute function with named chain.

        Args:
            name: Chain name
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            Function result

        Raises:
            ValueError: If chain not found
        """
        chain = self.get_chain(name)
        if not chain:
            raise ValueError(f"Fallback chain '{name}' not found")

        return await chain.execute(func, *args, **kwargs)


# Global fallback manager
fallback_manager = FallbackManager()


def fallback(strategy: FallbackStrategy = FallbackStrategy.FAST_FAIL, **config_kwargs):
    """
    Decorator for fallback strategies.

    Args:
        strategy: Fallback strategy to use
        **config_kwargs: Configuration parameters
    """

    def decorator(func):
        async def wrapper(*args, **kwargs):
            config = FallbackConfig(strategy=strategy, **config_kwargs)

            if strategy == FallbackStrategy.FAST_FAIL:
                handler = FastFailHandler(config)
            elif strategy == FallbackStrategy.RETRY:
                handler = RetryHandler(config)
            elif strategy == FallbackStrategy.CACHE:
                handler = CacheHandler(config)
            elif strategy == FallbackStrategy.DEFAULT_VALUE:
                handler = DefaultValueHandler(config)
            else:
                raise ValueError(f"Unsupported fallback strategy: {strategy}")

            return await handler.execute(func, *args, **kwargs)

        return wrapper

    return decorator

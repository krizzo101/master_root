"""
Testing helpers for OPSVI Foundation.

Provides utilities for testing foundation components.
"""

import asyncio
import logging
import tempfile
import time
from collections.abc import Callable
from contextlib import asynccontextmanager, contextmanager
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from freezegun import freeze_time


class AsyncTestCase:
    """Base class for async test cases."""

    @classmethod
    def setup_class(cls) -> None:
        """Set up the test class."""
        # Configure logging for tests
        logging.basicConfig(level=logging.DEBUG)

    def setup_method(self) -> None:
        """Set up each test method."""

    def teardown_method(self) -> None:
        """Tear down each test method."""


class MockFactory:
    """Factory for creating common mocks."""

    @staticmethod
    def create_logger() -> MagicMock:
        """Create a mock logger."""
        logger = MagicMock(spec=logging.Logger)
        logger.debug = MagicMock()
        logger.info = MagicMock()
        logger.warning = MagicMock()
        logger.error = MagicMock()
        logger.critical = MagicMock()
        return logger

    @staticmethod
    def create_async_logger() -> AsyncMock:
        """Create a mock async logger."""
        logger = AsyncMock(spec=logging.Logger)
        logger.debug = AsyncMock()
        logger.info = AsyncMock()
        logger.warning = AsyncMock()
        logger.error = AsyncMock()
        logger.critical = AsyncMock()
        return logger

    @staticmethod
    def create_config() -> MagicMock:
        """Create a mock configuration object."""
        config = MagicMock()
        config.get = MagicMock(return_value="test_value")
        config.set = MagicMock()
        config.has = MagicMock(return_value=True)
        return config

    @staticmethod
    def create_event_bus() -> MagicMock:
        """Create a mock event bus."""
        event_bus = MagicMock()
        event_bus.publish = AsyncMock()
        event_bus.subscribe = MagicMock()
        event_bus.unsubscribe = MagicMock()
        return event_bus


class TestUtils:
    """Utility functions for testing."""

    @staticmethod
    def assert_async_called_with(mock: AsyncMock, *args, **kwargs) -> None:
        """Assert that an async mock was called with specific arguments."""
        mock.assert_called_with(*args, **kwargs)

    @staticmethod
    def assert_async_called_once(mock: AsyncMock) -> None:
        """Assert that an async mock was called exactly once."""
        mock.assert_called_once()

    @staticmethod
    def assert_async_not_called(mock: AsyncMock) -> None:
        """Assert that an async mock was not called."""
        mock.assert_not_called()

    @staticmethod
    async def wait_for_condition(
        condition: Callable[[], bool],
        timeout: float = 5.0,
        interval: float = 0.1,
    ) -> None:
        """Wait for a condition to become true."""
        start_time = time.time()
        while not condition():
            if time.time() - start_time > timeout:
                raise TimeoutError(f"Condition not met within {timeout} seconds")
            await asyncio.sleep(interval)

    @staticmethod
    def create_temp_file(content: str = "") -> str:
        """Create a temporary file with content."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write(content)
            return f.name

    @staticmethod
    def create_temp_directory() -> str:
        """Create a temporary directory."""
        return tempfile.mkdtemp()


class AsyncTestRunner:
    """Runner for async tests."""

    @staticmethod
    async def run_async_test(test_func: Callable) -> Any:
        """Run an async test function."""
        try:
            return await test_func()
        except Exception as e:
            pytest.fail(f"Async test failed: {e}")

    @staticmethod
    def run_sync_test(test_func: Callable) -> Any:
        """Run a sync test function."""
        try:
            return test_func()
        except Exception as e:
            pytest.fail(f"Sync test failed: {e}")


class TestDataFactory:
    """Factory for creating test data."""

    @staticmethod
    def create_test_event(
        event_type: str = "test_event",
        data: Any = None,
    ) -> dict[str, Any]:
        """Create a test event."""
        return {
            "event_type": event_type,
            "data": data or {},
            "timestamp": time.time(),
            "source": "test",
        }

    @staticmethod
    def create_test_config() -> dict[str, Any]:
        """Create test configuration data."""
        return {
            "app_name": "test_app",
            "environment": "test",
            "debug": True,
            "log_level": "DEBUG",
            "database": {"url": "sqlite:///test.db", "pool_size": 5},
            "redis": {"url": "redis://localhost:6379/0"},
        }

    @staticmethod
    def create_test_user() -> dict[str, Any]:
        """Create test user data."""
        return {
            "id": "test_user_123",
            "username": "testuser",
            "email": "test@example.com",
            "roles": ["user"],
            "permissions": ["read", "write"],
        }


class PerformanceTestHelper:
    """Helper for performance testing."""

    @staticmethod
    async def measure_execution_time(func: Callable, *args, **kwargs) -> float:
        """Measure the execution time of a function."""
        start_time = time.time()
        if asyncio.iscoroutinefunction(func):
            await func(*args, **kwargs)
        else:
            func(*args, **kwargs)
        end_time = time.time()
        return end_time - start_time

    @staticmethod
    async def benchmark_function(
        func: Callable,
        iterations: int = 1000,
        *args,
        **kwargs,
    ) -> dict[str, float]:
        """Benchmark a function over multiple iterations."""
        times = []
        for _ in range(iterations):
            execution_time = await PerformanceTestHelper.measure_execution_time(
                func,
                *args,
                **kwargs,
            )
            times.append(execution_time)

        return {
            "min": min(times),
            "max": max(times),
            "avg": sum(times) / len(times),
            "total": sum(times),
            "iterations": iterations,
        }


class MockContextManager:
    """Context manager for creating mocks."""

    def __init__(self, *patches: str) -> None:
        self.patches = patches
        self.mocks = []

    def __enter__(self):
        """Enter the context."""
        for patch_path in self.patches:
            mock = patch(patch_path)
            self.mocks.append(mock.start())
        return self.mocks[0] if len(self.mocks) == 1 else self.mocks

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit the context."""
        for mock in self.mocks:
            mock.stop()


@contextmanager
def mock_time(timestamp: float):
    """Mock time for testing."""
    with freeze_time(timestamp):
        yield


@asynccontextmanager
async def async_context_manager():
    """Async context manager for testing."""
    try:
        yield
    finally:
        # Cleanup code here
        pass


class TestEventBus:
    """Test event bus for testing event-driven components."""

    def __init__(self) -> None:
        self.events: list[dict[str, Any]] = []
        self.subscribers: dict[str, list[Callable]] = {}

    async def publish(self, event: dict[str, Any]) -> None:
        """Publish an event."""
        self.events.append(event)
        event_type = event.get("event_type")
        if event_type in self.subscribers:
            for subscriber in self.subscribers[event_type]:
                try:
                    if asyncio.iscoroutinefunction(subscriber):
                        await subscriber(event)
                    else:
                        subscriber(event)
                except Exception as e:
                    logging.error(f"Error in event subscriber: {e}")

    def subscribe(self, event_type: str, callback: Callable) -> None:
        """Subscribe to events."""
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(callback)

    def unsubscribe(self, event_type: str, callback: Callable) -> None:
        """Unsubscribe from events."""
        if event_type in self.subscribers:
            self.subscribers[event_type].remove(callback)

    def get_events(self, event_type: str | None = None) -> list[dict[str, Any]]:
        """Get published events."""
        if event_type is None:
            return self.events.copy()
        return [event for event in self.events if event.get("event_type") == event_type]

    def clear_events(self) -> None:
        """Clear all events."""
        self.events.clear()


class TestMetricsCollector:
    """Test metrics collector for testing observability components."""

    def __init__(self) -> None:
        self.metrics: dict[str, list[dict[str, Any]]] = {}
        self.counters: dict[str, int] = {}
        self.gauges: dict[str, float] = {}
        self.histograms: dict[str, list[float]] = {}

    def increment_counter(
        self,
        name: str,
        value: int = 1,
        labels: dict[str, str] | None = None,
    ) -> None:
        """Increment a counter."""
        if name not in self.counters:
            self.counters[name] = 0
        self.counters[name] += value

        if name not in self.metrics:
            self.metrics[name] = []
        self.metrics[name].append(
            {
                "type": "counter",
                "value": value,
                "labels": labels or {},
                "timestamp": time.time(),
            },
        )

    def set_gauge(
        self,
        name: str,
        value: float,
        labels: dict[str, str] | None = None,
    ) -> None:
        """Set a gauge value."""
        self.gauges[name] = value

        if name not in self.metrics:
            self.metrics[name] = []
        self.metrics[name].append(
            {
                "type": "gauge",
                "value": value,
                "labels": labels or {},
                "timestamp": time.time(),
            },
        )

    def record_histogram(
        self,
        name: str,
        value: float,
        labels: dict[str, str] | None = None,
    ) -> None:
        """Record a histogram value."""
        if name not in self.histograms:
            self.histograms[name] = []
        self.histograms[name].append(value)

        if name not in self.metrics:
            self.metrics[name] = []
        self.metrics[name].append(
            {
                "type": "histogram",
                "value": value,
                "labels": labels or {},
                "timestamp": time.time(),
            },
        )

    def get_counter(self, name: str) -> int:
        """Get counter value."""
        return self.counters.get(name, 0)

    def get_gauge(self, name: str) -> float:
        """Get gauge value."""
        return self.gauges.get(name, 0.0)

    def get_histogram(self, name: str) -> list[float]:
        """Get histogram values."""
        return self.histograms.get(name, [])

    def get_metrics(
        self,
        name: str | None = None,
    ) -> dict[str, list[dict[str, Any]]]:
        """Get all metrics."""
        if name is None:
            return self.metrics.copy()
        return {name: self.metrics.get(name, [])}

    def clear_metrics(self) -> None:
        """Clear all metrics."""
        self.metrics.clear()
        self.counters.clear()
        self.gauges.clear()
        self.histograms.clear()

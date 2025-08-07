"""
Base testing infrastructure for OPSVI Core.

Provides testing utilities, fixtures, and helpers.
"""

from __future__ import annotations

import asyncio
import contextlib
import tempfile
import time
from collections.abc import AsyncGenerator, Callable, Generator
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock

from opsvi_foundation import BaseComponent, get_logger

logger = get_logger(__name__)


class TestFixtures:
    """Common test fixtures and utilities."""

    @staticmethod
    @contextlib.contextmanager
    def temporary_directory() -> Generator[Path, None, None]:
        """Create a temporary directory for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    @staticmethod
    @contextlib.contextmanager
    def temporary_file(
        suffix: str = "", content: str = ""
    ) -> Generator[Path, None, None]:
        """Create a temporary file for testing."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=suffix, delete=False
        ) as temp_file:
            if content:
                temp_file.write(content)
            temp_file.flush()
            temp_path = Path(temp_file.name)

        try:
            yield temp_path
        finally:
            temp_path.unlink(missing_ok=True)

    @staticmethod
    def create_mock_component(component_class: type[BaseComponent]) -> MagicMock:
        """Create a mock component with proper lifecycle methods."""
        mock = MagicMock(spec=component_class)
        mock.start = AsyncMock()
        mock.stop = AsyncMock()
        mock._start = AsyncMock()
        mock._stop = AsyncMock()
        mock._cleanup = AsyncMock()
        return mock

    @staticmethod
    async def wait_for_condition(
        condition: Callable[[], bool], timeout: float = 5.0, interval: float = 0.1
    ) -> bool:
        """Wait for a condition to become true."""
        start_time = time.time()
        while time.time() - start_time < timeout:
            if condition():
                return True
            await asyncio.sleep(interval)
        return False

    @staticmethod
    @contextlib.asynccontextmanager
    async def component_lifecycle(
        component: BaseComponent,
    ) -> AsyncGenerator[BaseComponent, None]:
        """Manage component lifecycle in tests."""
        try:
            await component.start()
            yield component
        finally:
            await component.stop()


class MockServices:
    """Mock implementations of common services."""

    @staticmethod
    def create_mock_message_broker():
        """Create a mock message broker."""
        from ..messaging.base import MessageBroker

        mock_broker = MagicMock(spec=MessageBroker)
        mock_broker.publish = AsyncMock()
        mock_broker.subscribe = AsyncMock()
        mock_broker.start = AsyncMock()
        mock_broker.stop = AsyncMock()
        return mock_broker

    @staticmethod
    def create_mock_event_bus():
        """Create a mock event bus."""
        from ..events.base import EventBus

        mock_bus = MagicMock(spec=EventBus)
        mock_bus.publish = AsyncMock()
        mock_bus.subscribe = AsyncMock()
        mock_bus.start = AsyncMock()
        mock_bus.stop = AsyncMock()
        return mock_bus

    @staticmethod
    def create_mock_storage():
        """Create a mock storage backend."""
        from ..storage.base import StorageBackend

        mock_storage = MagicMock(spec=StorageBackend)
        mock_storage.get = AsyncMock()
        mock_storage.set = AsyncMock()
        mock_storage.delete = AsyncMock()
        mock_storage.exists = AsyncMock()
        mock_storage.list_keys = AsyncMock()
        mock_storage.clear = AsyncMock()
        mock_storage.size = AsyncMock()
        return mock_storage

    @staticmethod
    def create_mock_cache():
        """Create a mock cache backend."""
        from ..caching.base import CacheBackend

        mock_cache = MagicMock(spec=CacheBackend)
        mock_cache.get = AsyncMock()
        mock_cache.set = AsyncMock()
        mock_cache.delete = AsyncMock()
        mock_cache.exists = AsyncMock()
        mock_cache.clear = AsyncMock()
        return mock_cache


class TestHelpers:
    """Helper functions for testing."""

    @staticmethod
    def assert_called_with_timeout(mock_func: AsyncMock, timeout: float = 1.0) -> bool:
        """Assert that a mock function was called within timeout."""
        start_time = time.time()
        while time.time() - start_time < timeout:
            if mock_func.called:
                return True
            time.sleep(0.01)
        return False

    @staticmethod
    async def run_with_timeout(coro, timeout: float = 5.0):
        """Run coroutine with timeout."""
        return await asyncio.wait_for(coro, timeout=timeout)

    @staticmethod
    def create_test_config(overrides: dict[str, Any] | None = None) -> dict[str, Any]:
        """Create a test configuration."""
        base_config = {
            "debug": True,
            "log_level": "DEBUG",
            "timeout": 5.0,
            "max_retries": 1,
        }
        if overrides:
            base_config.update(overrides)
        return base_config

    @staticmethod
    @contextlib.contextmanager
    def patch_environment(env_vars: dict[str, str]) -> Generator[None, None, None]:
        """Temporarily patch environment variables."""
        import os

        original_values = {}
        for key, value in env_vars.items():
            original_values[key] = os.environ.get(key)
            os.environ[key] = value

        try:
            yield
        finally:
            for key, original_value in original_values.items():
                if original_value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = original_value


class TestCase:
    """Base test case with common setup and teardown."""

    def __init__(self):
        self.fixtures = TestFixtures()
        self.mocks = MockServices()
        self.helpers = TestHelpers()
        self._cleanup_tasks: list[Callable] = []

    async def setup(self) -> None:
        """Setup test case."""
        pass

    async def teardown(self) -> None:
        """Teardown test case."""
        for cleanup_task in self._cleanup_tasks:
            try:
                if asyncio.iscoroutinefunction(cleanup_task):
                    await cleanup_task()
                else:
                    cleanup_task()
            except Exception as e:
                logger.error("Cleanup task failed: %s", e)
        self._cleanup_tasks.clear()

    def add_cleanup(self, cleanup_task: Callable) -> None:
        """Add cleanup task to run during teardown."""
        self._cleanup_tasks.append(cleanup_task)

    @contextlib.asynccontextmanager
    async def managed_test(self) -> AsyncGenerator[None, None]:
        """Context manager for test lifecycle."""
        await self.setup()
        try:
            yield
        finally:
            await self.teardown()


class PerformanceTester:
    """Performance testing utilities."""

    @staticmethod
    async def measure_async_function(
        func: Callable, *args, **kwargs
    ) -> tuple[Any, float]:
        """Measure execution time of async function."""
        start_time = time.time()
        result = await func(*args, **kwargs)
        duration = time.time() - start_time
        return result, duration

    @staticmethod
    def measure_sync_function(func: Callable, *args, **kwargs) -> tuple[Any, float]:
        """Measure execution time of sync function."""
        start_time = time.time()
        result = func(*args, **kwargs)
        duration = time.time() - start_time
        return result, duration

    @staticmethod
    async def benchmark_async_function(
        func: Callable, iterations: int = 100, *args, **kwargs
    ) -> dict[str, float]:
        """Benchmark async function performance."""
        times = []

        for _ in range(iterations):
            _, duration = await PerformanceTester.measure_async_function(
                func, *args, **kwargs
            )
            times.append(duration)

        return {
            "min": min(times),
            "max": max(times),
            "avg": sum(times) / len(times),
            "total": sum(times),
            "iterations": iterations,
        }

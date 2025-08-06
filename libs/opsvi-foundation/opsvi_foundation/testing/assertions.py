"""
Testing assertions for OPSVI Foundation.

Provides custom assertions for testing foundation components.
"""

import asyncio
import json
import time
from collections.abc import Callable
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest


class AsyncAssertions:
    """Custom assertions for async testing."""

    @staticmethod
    async def assert_async_called_with(mock: AsyncMock, *args, **kwargs) -> None:
        """Assert that an async mock was called with specific arguments."""
        mock.assert_called_with(*args, **kwargs)

    @staticmethod
    async def assert_async_called_once(mock: AsyncMock) -> None:
        """Assert that an async mock was called exactly once."""
        mock.assert_called_once()

    @staticmethod
    async def assert_async_not_called(mock: AsyncMock) -> None:
        """Assert that an async mock was not called."""
        mock.assert_not_called()

    @staticmethod
    async def assert_async_called_times(mock: AsyncMock, expected_calls: int) -> None:
        """Assert that an async mock was called a specific number of times."""
        actual_calls = mock.call_count
        assert (
            actual_calls == expected_calls
        ), f"Expected {expected_calls} calls, got {actual_calls}"

    @staticmethod
    async def assert_async_called_with_any_order(
        mock: AsyncMock,
        *expected_calls,
    ) -> None:
        """Assert that an async mock was called with arguments in any order."""
        actual_calls = mock.call_args_list
        assert len(actual_calls) == len(
            expected_calls,
        ), f"Expected {len(expected_calls)} calls, got {len(actual_calls)}"

        # Convert expected calls to comparable format
        expected_call_args = [call[0] for call in expected_calls]
        actual_call_args = [call[0] for call in actual_calls]

        # Check if all expected calls are present
        for expected in expected_call_args:
            assert (
                expected in actual_call_args
            ), f"Expected call {expected} not found in {actual_call_args}"


class EventAssertions:
    """Custom assertions for event testing."""

    @staticmethod
    def assert_event_published(event_bus: MagicMock, event_type: str, **kwargs) -> None:
        """Assert that an event was published."""
        event_bus.publish.assert_called()
        call_args = event_bus.publish.call_args_list

        for call in call_args:
            event = call[0][0] if call[0] else call[1]
            if event.get("event_type") == event_type:
                # Check additional kwargs if provided
                for key, value in kwargs.items():
                    assert (
                        event.get(key) == value
                    ), f"Event {key} mismatch: expected {value}, got {event.get(key)}"
                return

        pytest.fail(f"Event of type '{event_type}' was not published")

    @staticmethod
    def assert_event_not_published(event_bus: MagicMock, event_type: str) -> None:
        """Assert that an event was not published."""
        if not event_bus.publish.called:
            return

        call_args = event_bus.publish.call_args_list
        for call in call_args:
            event = call[0][0] if call[0] else call[1]
            if event.get("event_type") == event_type:
                pytest.fail(
                    f"Event of type '{event_type}' was published when it should not have been",
                )

    @staticmethod
    def assert_event_count(event_bus: MagicMock, expected_count: int) -> None:
        """Assert that a specific number of events were published."""
        actual_count = event_bus.publish.call_count
        assert (
            actual_count == expected_count
        ), f"Expected {expected_count} events, got {actual_count}"


class LoggingAssertions:
    """Custom assertions for logging testing."""

    @staticmethod
    def assert_logged(logger: MagicMock, level: str, message: str) -> None:
        """Assert that a specific log message was recorded."""
        log_method = getattr(logger, level.lower())
        log_method.assert_called()

        call_args = log_method.call_args_list
        for call in call_args:
            if message in str(call):
                return

        pytest.fail(f"Log message '{message}' was not found in {level} calls")

    @staticmethod
    def assert_logged_with_level(logger: MagicMock, level: str) -> None:
        """Assert that a specific log level was used."""
        log_method = getattr(logger, level.lower())
        assert log_method.called, f"No {level} log calls were made"

    @staticmethod
    def assert_not_logged(logger: MagicMock, level: str, message: str) -> None:
        """Assert that a specific log message was not recorded."""
        log_method = getattr(logger, level.lower())
        if not log_method.called:
            return

        call_args = log_method.call_args_list
        for call in call_args:
            if message in str(call):
                pytest.fail(
                    f"Log message '{message}' was found in {level} calls when it should not have been",
                )

    @staticmethod
    def assert_log_count(logger: MagicMock, level: str, expected_count: int) -> None:
        """Assert that a specific number of log messages were recorded."""
        log_method = getattr(logger, level.lower())
        actual_count = log_method.call_count
        assert (
            actual_count == expected_count
        ), f"Expected {expected_count} {level} log calls, got {actual_count}"


class ConfigAssertions:
    """Custom assertions for configuration testing."""

    @staticmethod
    def assert_config_value(config: MagicMock, key: str, expected_value: Any) -> None:
        """Assert that a configuration value matches expected value."""
        config.get.assert_called_with(key)
        call_args = config.get.call_args_list

        for call in call_args:
            if call[0][0] == key and call[1].get("default") == expected_value:
                return

        pytest.fail(f"Config value for '{key}' was not set to '{expected_value}'")

    @staticmethod
    def assert_config_has_key(config: MagicMock, key: str) -> None:
        """Assert that a configuration key exists."""
        config.has.assert_called_with(key)
        assert config.has.return_value, f"Config key '{key}' does not exist"

    @staticmethod
    def assert_config_set(config: MagicMock, key: str, value: Any) -> None:
        """Assert that a configuration value was set."""
        config.set.assert_called_with(key, value)


class MetricsAssertions:
    """Custom assertions for metrics testing."""

    @staticmethod
    def assert_counter_incremented(
        metrics_collector: MagicMock,
        counter_name: str,
        expected_increment: int = 1,
    ) -> None:
        """Assert that a counter was incremented."""
        metrics_collector.increment_counter.assert_called_with(
            counter_name,
            expected_increment,
        )

    @staticmethod
    def assert_gauge_set(
        metrics_collector: MagicMock,
        gauge_name: str,
        expected_value: float,
    ) -> None:
        """Assert that a gauge was set to a specific value."""
        metrics_collector.set_gauge.assert_called_with(gauge_name, expected_value)

    @staticmethod
    def assert_histogram_recorded(
        metrics_collector: MagicMock,
        histogram_name: str,
        expected_value: float,
    ) -> None:
        """Assert that a histogram value was recorded."""
        metrics_collector.record_histogram.assert_called_with(
            histogram_name,
            expected_value,
        )

    @staticmethod
    def assert_metrics_count(metrics_collector: MagicMock, expected_count: int) -> None:
        """Assert that a specific number of metrics were recorded."""
        total_calls = (
            metrics_collector.increment_counter.call_count
            + metrics_collector.set_gauge.call_count
            + metrics_collector.record_histogram.call_count
        )
        assert (
            total_calls == expected_count
        ), f"Expected {expected_count} metric calls, got {total_calls}"


class TimeAssertions:
    """Custom assertions for time-based testing."""

    @staticmethod
    async def assert_completes_within_timeout(
        func: Callable,
        timeout: float,
        *args,
        **kwargs,
    ) -> None:
        """Assert that a function completes within a timeout."""
        start_time = time.time()
        try:
            if asyncio.iscoroutinefunction(func):
                await asyncio.wait_for(func(*args, **kwargs), timeout=timeout)
            else:
                result = func(*args, **kwargs)
                if asyncio.iscoroutine(result):
                    await asyncio.wait_for(result, timeout=timeout)
        except TimeoutError:
            pytest.fail(f"Function did not complete within {timeout} seconds")

        end_time = time.time()
        execution_time = end_time - start_time
        assert (
            execution_time <= timeout
        ), f"Function took {execution_time}s, expected <= {timeout}s"

    @staticmethod
    async def assert_takes_at_least(
        func: Callable,
        min_time: float,
        *args,
        **kwargs,
    ) -> None:
        """Assert that a function takes at least a minimum time."""
        start_time = time.time()
        try:
            if asyncio.iscoroutinefunction(func):
                await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
                if asyncio.iscoroutine(result):
                    await result
        except Exception as e:
            pytest.fail(f"Function failed: {e}")

        end_time = time.time()
        execution_time = end_time - start_time
        assert (
            execution_time >= min_time
        ), f"Function took {execution_time}s, expected >= {min_time}s"


class DataAssertions:
    """Custom assertions for data validation."""

    @staticmethod
    def assert_dict_contains(
        dict_obj: dict[str, Any],
        expected_items: dict[str, Any],
    ) -> None:
        """Assert that a dictionary contains specific key-value pairs."""
        for key, expected_value in expected_items.items():
            assert key in dict_obj, f"Key '{key}' not found in dictionary"
            actual_value = dict_obj[key]
            assert (
                actual_value == expected_value
            ), f"Value for key '{key}' mismatch: expected {expected_value}, got {actual_value}"

    @staticmethod
    def assert_list_contains(list_obj: list[Any], expected_item: Any) -> None:
        """Assert that a list contains a specific item."""
        assert expected_item in list_obj, f"Item {expected_item} not found in list"

    @staticmethod
    def assert_list_length(list_obj: list[Any], expected_length: int) -> None:
        """Assert that a list has a specific length."""
        actual_length = len(list_obj)
        assert (
            actual_length == expected_length
        ), f"Expected list length {expected_length}, got {actual_length}"

    @staticmethod
    def assert_json_equals(json_str: str, expected_data: Any) -> None:
        """Assert that a JSON string equals expected data."""
        try:
            parsed_data = json.loads(json_str)
            assert (
                parsed_data == expected_data
            ), f"JSON data mismatch: expected {expected_data}, got {parsed_data}"
        except json.JSONDecodeError as e:
            pytest.fail(f"Invalid JSON: {e}")

    @staticmethod
    def assert_string_contains(text: str, substring: str) -> None:
        """Assert that a string contains a substring."""
        assert substring in text, f"Substring '{substring}' not found in text"

    @staticmethod
    def assert_string_matches_pattern(text: str, pattern: str) -> None:
        """Assert that a string matches a regex pattern."""
        import re

        assert re.match(pattern, text), f"Text does not match pattern '{pattern}'"


class ExceptionAssertions:
    """Custom assertions for exception testing."""

    @staticmethod
    def assert_raises_exception(
        func: Callable,
        exception_type: type,
        *args,
        **kwargs,
    ) -> None:
        """Assert that a function raises a specific exception."""
        with pytest.raises(exception_type):
            func(*args, **kwargs)

    @staticmethod
    async def assert_raises_async_exception(
        func: Callable,
        exception_type: type,
        *args,
        **kwargs,
    ) -> None:
        """Assert that an async function raises a specific exception."""
        with pytest.raises(exception_type):
            if asyncio.iscoroutinefunction(func):
                await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
                if asyncio.iscoroutine(result):
                    await result

    @staticmethod
    def assert_raises_with_message(
        func: Callable,
        exception_type: type,
        expected_message: str,
        *args,
        **kwargs,
    ) -> None:
        """Assert that a function raises an exception with a specific message."""
        with pytest.raises(exception_type, match=expected_message):
            func(*args, **kwargs)

    @staticmethod
    def assert_no_exception(func: Callable, *args, **kwargs) -> None:
        """Assert that a function does not raise any exception."""
        try:
            func(*args, **kwargs)
        except Exception as e:
            pytest.fail(f"Function raised unexpected exception: {e}")

    @staticmethod
    async def assert_no_async_exception(func: Callable, *args, **kwargs) -> None:
        """Assert that an async function does not raise any exception."""
        try:
            if asyncio.iscoroutinefunction(func):
                await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
                if asyncio.iscoroutine(result):
                    await result
        except Exception as e:
            pytest.fail(f"Async function raised unexpected exception: {e}")


class MockAssertions:
    """Custom assertions for mock testing."""

    @staticmethod
    def assert_mock_called_with_args(
        mock: MagicMock,
        *expected_args,
        **expected_kwargs,
    ) -> None:
        """Assert that a mock was called with specific arguments."""
        mock.assert_called_with(*expected_args, **expected_kwargs)

    @staticmethod
    def assert_mock_called_times(mock: MagicMock, expected_calls: int) -> None:
        """Assert that a mock was called a specific number of times."""
        actual_calls = mock.call_count
        assert (
            actual_calls == expected_calls
        ), f"Expected {expected_calls} calls, got {actual_calls}"

    @staticmethod
    def assert_mock_not_called(mock: MagicMock) -> None:
        """Assert that a mock was not called."""
        mock.assert_not_called()

    @staticmethod
    def assert_mock_called_once(mock: MagicMock) -> None:
        """Assert that a mock was called exactly once."""
        mock.assert_called_once()

    @staticmethod
    def assert_mock_return_value(mock: MagicMock, expected_value: Any) -> None:
        """Assert that a mock returns a specific value."""
        assert (
            mock.return_value == expected_value
        ), f"Expected return value {expected_value}, got {mock.return_value}"

    @staticmethod
    def assert_mock_side_effect_called(mock: MagicMock) -> None:
        """Assert that a mock's side effect was called."""
        assert mock.side_effect is not None, "Mock has no side effect"
        # This is a simplified check - in practice you'd need more complex logic
        assert mock.called, "Mock was not called"

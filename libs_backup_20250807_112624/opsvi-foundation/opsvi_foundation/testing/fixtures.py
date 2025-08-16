"""
Shared testing fixtures and utilities.

Provides common test fixtures for OPSVI libraries.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from ..config import FoundationConfig
from ..resilience import CircuitBreaker, CircuitBreakerConfig
from ..security import AuthConfig, AuthManager


@pytest.fixture
def foundation_config():
    """Provide test foundation configuration."""
    return FoundationConfig(
        environment="test",
        debug=True,
        log_level="DEBUG",
        jwt_secret="test-secret",
        api_timeout=10,
        max_retries=2,
    )


@pytest.fixture
def auth_config():
    """Provide test auth configuration."""
    return AuthConfig(
        jwt_secret="test-secret",
        jwt_expiry_hours=1,
        api_key_length=16,
    )


@pytest.fixture
def auth_manager(auth_config):
    """Provide test auth manager."""
    return AuthManager(auth_config)


@pytest.fixture
def circuit_breaker_config():
    """Provide test circuit breaker configuration."""
    return CircuitBreakerConfig(
        failure_threshold=2,
        recovery_timeout=5,
        success_threshold=1,
        timeout=5,
    )


@pytest.fixture
def circuit_breaker(circuit_breaker_config):
    """Provide test circuit breaker."""
    return CircuitBreaker(circuit_breaker_config)


@pytest.fixture
def mock_async_function():
    """Provide mock async function for testing."""
    return AsyncMock(return_value="success")


@pytest.fixture
def mock_sync_function():
    """Provide mock sync function for testing."""
    return MagicMock(return_value="success")

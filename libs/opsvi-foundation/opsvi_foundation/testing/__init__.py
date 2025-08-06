"""
Testing module for opsvi-foundation.

Provides shared fixtures and testing utilities.
"""

from .fixtures import (
    foundation_config,
    auth_config,
    auth_manager,
    circuit_breaker_config,
    circuit_breaker,
    mock_async_function,
    mock_sync_function,
)

__all__ = [
    "foundation_config",
    "auth_config",
    "auth_manager",
    "circuit_breaker_config",
    "circuit_breaker",
    "mock_async_function",
    "mock_sync_function",
]

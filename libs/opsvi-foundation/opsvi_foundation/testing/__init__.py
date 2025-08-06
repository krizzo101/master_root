"""
Testing module for opsvi-foundation.

Provides shared fixtures and testing utilities.
"""

from .fixtures import (
    auth_config,
    auth_manager,
    circuit_breaker,
    circuit_breaker_config,
    foundation_config,
    mock_async_function,
    mock_sync_function,
)

__all__ = [
    "auth_config",
    "auth_manager",
    "circuit_breaker",
    "circuit_breaker_config",
    "foundation_config",
    "mock_async_function",
    "mock_sync_function",
]

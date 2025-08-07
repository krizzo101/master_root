"""Exceptions module for opsvi-llm.

Provides exception hierarchy and error handling.
"""

from .base import (
    OpsviLlmError,
    OpsviLlmConfigurationError,
    OpsviLlmConnectionError,
    OpsviLlmValidationError,
    OpsviLlmTimeoutError,
    OpsviLlmResourceError,
    OpsviLlmInitializationError,
)

__all__ = [
    "OpsviLlmError",
    "OpsviLlmConfigurationError",
    "OpsviLlmConnectionError",
    "OpsviLlmValidationError",
    "OpsviLlmTimeoutError",
    "OpsviLlmResourceError",
    "OpsviLlmInitializationError",
]

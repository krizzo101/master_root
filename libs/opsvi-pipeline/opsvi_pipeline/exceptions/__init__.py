"""Exceptions module for opsvi-pipeline.

Provides exception hierarchy and error handling.
"""

from .base import (
    OpsviPipelineError,
    OpsviPipelineConfigurationError,
    OpsviPipelineConnectionError,
    OpsviPipelineValidationError,
    OpsviPipelineTimeoutError,
    OpsviPipelineResourceError,
    OpsviPipelineInitializationError,
)

__all__ = [
    "OpsviPipelineError",
    "OpsviPipelineConfigurationError",
    "OpsviPipelineConnectionError",
    "OpsviPipelineValidationError",
    "OpsviPipelineTimeoutError",
    "OpsviPipelineResourceError",
    "OpsviPipelineInitializationError",
]

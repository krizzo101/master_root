"""
Utilities module for opsvi-core.

Provides core utility functions and helpers.
"""

from opsvi_foundation import (
    BaseComponent,
    ComponentError,
    FoundationConfig,
    get_logger,
)

# Base utility functions
from .base import (
    AsyncLock,
    RateLimiter,
    chunk_list,
    format_bytes,
    format_duration,
    gather_with_limit,
    merge_dicts,
    retry_on_failure,
    safe_dict_get,
    timing_decorator,
)

__all__ = [
    # Base classes and utilities
    "AsyncLock",
    "RateLimiter",
    "chunk_list",
    "format_bytes",
    "format_duration",
    "gather_with_limit",
    "merge_dicts",
    "retry_on_failure",
    "safe_dict_get",
    "timing_decorator",
]

__version__ = "1.0.0"

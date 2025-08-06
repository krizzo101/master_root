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

__all__ = [
    "get_logger",
    "ComponentError",
    "BaseComponent",
    "FoundationConfig",
]

__version__ = "1.0.0"

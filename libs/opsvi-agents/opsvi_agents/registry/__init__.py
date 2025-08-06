"""
Registry module for opsvi-agents.

Provides agent registration, discovery, and lifecycle management.
"""

from opsvi_foundation import (
    BaseComponent,
    ComponentError,
    get_logger,
)

__all__ = [
    "BaseComponent",
    "ComponentError",
    "get_logger",
]

__version__ = "1.0.0"

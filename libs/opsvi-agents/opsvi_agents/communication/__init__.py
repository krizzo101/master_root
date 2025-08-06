"""
Communication module for opsvi-agents.

Provides inter-agent communication protocols and message passing.
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

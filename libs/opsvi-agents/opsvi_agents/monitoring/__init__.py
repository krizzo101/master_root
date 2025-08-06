"""
Monitoring module for opsvi-agents.

Provides agent monitoring, metrics, tracing, and observability capabilities.
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

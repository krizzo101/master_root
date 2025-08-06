"""
Fine-tuning module for opsvi-llm.

Provides model fine-tuning, training orchestration, and evaluation capabilities.
"""

from opsvi_foundation import (
    BaseComponent,
    ComponentError,
    get_logger,
)

__all__ = [
    "get_logger",
    "ComponentError",
    "BaseComponent",
]

__version__ = "1.0.0"

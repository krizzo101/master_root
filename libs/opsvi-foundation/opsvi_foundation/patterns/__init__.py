"""
Patterns module for opsvi-foundation.

Provides base classes and lifecycle management patterns.
"""

from .base import BaseComponent, ComponentError, LifecycleComponent

__all__ = [
    "BaseComponent",
    "ComponentError",
    "LifecycleComponent",
]

"""
Patterns module for opsvi-foundation.

Provides base classes and lifecycle management patterns.
"""

from .base import BaseComponent, LifecycleComponent, ComponentError

__all__ = [
    "BaseComponent",
    "LifecycleComponent",
    "ComponentError",
]

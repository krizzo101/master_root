"""
Deployment module for opsvi-agents.

Provides agent deployment strategies for local, Docker, Kubernetes, and cloud environments.
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

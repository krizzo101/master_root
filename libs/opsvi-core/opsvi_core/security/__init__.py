"""
Security module for opsvi-core.

Provides authentication, authorization, and security utilities.
"""

from opsvi_foundation import (
    BaseComponent,
    ComponentError,
    get_logger,
)

# Security components
from .auth import (
    AuthConfig,
    AuthManager,
    SecurityError,
)

__all__ = [
    # Base classes
    "AuthConfig",
    "AuthManager",
    "SecurityError",
]

__version__ = "1.0.0"

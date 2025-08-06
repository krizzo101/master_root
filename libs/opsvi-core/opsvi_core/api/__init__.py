"""
API module for opsvi-core.

Provides FastAPI-based REST API framework with authentication, rate limiting, and documentation.
"""

from opsvi_foundation import (
    BaseComponent,
    ComponentError,
    get_logger,
)

# Base API infrastructure
from .base import (
    APIAuthenticator,
    APIConfig,
    APIEndpoint,
    APIError,
    APIServer,
    JWTAuthenticator,
    RateLimiter,
    RateLimitExceeded,
    RateLimitMiddleware,
)

__all__ = [
    # Base classes
    "APIAuthenticator",
    "APIConfig",
    "APIEndpoint",
    "APIError",
    "APIServer",
    "JWTAuthenticator",
    "RateLimitExceeded",
    "RateLimitMiddleware",
    "RateLimiter",
]

__version__ = "1.0.0"

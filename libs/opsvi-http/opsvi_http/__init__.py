"""OPSVI HTTP Library.

Comprehensive HTTP client and server functionality for the OPSVI ecosystem.
"""

__version__ = "0.1.0"
__author__ = "OPSVI Team"
__description__ = "HTTP client and server functionality for OPSVI"

# Core exports
from .client.base import (
    BaseHTTPClient,
    HTTPConfig,
    HTTPRequest,
    HTTPResponse,
    HTTPMethod,
    HTTPStatus,
    HTTPError,
    HTTPClientError,
    HTTPRequestError,
    HTTPResponseError,
    HTTPTimeoutError,
)

from .client.httpx_client import (
    HTTPXClient,
    HTTPXConfig,
)

# Convenience exports
__all__ = [
    # Core
    "BaseHTTPClient",
    "HTTPConfig",
    "HTTPRequest",
    "HTTPResponse",
    "HTTPMethod",
    "HTTPStatus",
    "HTTPError",
    "HTTPClientError",
    "HTTPRequestError",
    "HTTPResponseError",
    "HTTPTimeoutError",
    # HTTPX implementation
    "HTTPXClient",
    "HTTPXConfig",
]


def get_version() -> str:
    """Get the library version."""
    return __version__


def get_author() -> str:
    """Get the library author."""
    return __author__


def get_description() -> str:
    """Get the library description."""
    return __description__

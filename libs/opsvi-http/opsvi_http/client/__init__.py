"""HTTP client module for OPSVI HTTP library."""

from .base import (
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

from .httpx_client import (
    HTTPXClient,
    HTTPXConfig,
)

__all__ = [
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
    "HTTPXClient",
    "HTTPXConfig",
]

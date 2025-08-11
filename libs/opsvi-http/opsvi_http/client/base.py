"""Base HTTP client interface for OPSVI HTTP library.

Comprehensive HTTP client abstraction for the OPSVI ecosystem
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
import asyncio
import logging
from enum import Enum
from datetime import datetime, timedelta
from urllib.parse import urljoin, urlparse

import aiohttp
import httpx
from pydantic import BaseModel, Field, ConfigDict

from opsvi_foundation import BaseComponent, ComponentError, BaseSettings

logger = logging.getLogger(__name__)


class HTTPMethod(Enum):
    """HTTP methods enumeration."""

    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"


class HTTPStatus(Enum):
    """HTTP status codes enumeration."""

    OK = 200
    CREATED = 201
    ACCEPTED = 202
    NO_CONTENT = 204
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    METHOD_NOT_ALLOWED = 405
    CONFLICT = 409
    UNPROCESSABLE_ENTITY = 422
    INTERNAL_SERVER_ERROR = 500
    BAD_GATEWAY = 502
    SERVICE_UNAVAILABLE = 503


class HTTPError(ComponentError):
    """Base exception for HTTP errors."""

    pass


class HTTPClientError(HTTPError):
    """HTTP client errors."""

    pass


class HTTPRequestError(HTTPError):
    """HTTP request errors."""

    pass


class HTTPResponseError(HTTPError):
    """HTTP response errors."""

    pass


class HTTPTimeoutError(HTTPError):
    """HTTP timeout errors."""

    pass


class HTTPConfig(BaseSettings):
    """Base configuration for HTTP clients."""

    # Client configuration
    base_url: Optional[str] = Field(default=None, description="Base URL for requests")
    timeout: float = Field(default=30.0, description="Request timeout in seconds")
    max_retries: int = Field(default=3, description="Maximum number of retries")
    retry_delay: float = Field(
        default=1.0, description="Delay between retries in seconds"
    )
    backoff_factor: float = Field(default=2.0, description="Exponential backoff factor")

    # Connection configuration
    max_connections: int = Field(default=100, description="Maximum connections in pool")
    max_keepalive_connections: int = Field(
        default=20, description="Maximum keepalive connections"
    )
    keepalive_timeout: float = Field(
        default=30.0, description="Keepalive timeout in seconds"
    )

    # Headers configuration
    default_headers: Dict[str, str] = Field(
        default_factory=dict, description="Default headers"
    )
    user_agent: str = Field(default="OPSVI-HTTP/1.0", description="User agent string")

    # SSL configuration
    verify_ssl: bool = Field(default=True, description="Verify SSL certificates")
    ssl_cert: Optional[str] = Field(default=None, description="SSL certificate path")
    ssl_key: Optional[str] = Field(default=None, description="SSL key path")

    # Proxy configuration
    proxy: Optional[str] = Field(default=None, description="Proxy URL")
    proxy_auth: Optional[Dict[str, str]] = Field(
        default=None, description="Proxy authentication"
    )

    model_config = ConfigDict(env_prefix="OPSVI_HTTP_")


class HTTPRequest(BaseModel):
    """HTTP request model."""

    method: HTTPMethod = Field(description="HTTP method")
    url: str = Field(description="Request URL")
    headers: Optional[Dict[str, str]] = Field(
        default=None, description="Request headers"
    )
    params: Optional[Dict[str, Any]] = Field(
        default=None, description="Query parameters"
    )
    data: Optional[Union[str, bytes, Dict[str, Any]]] = Field(
        default=None, description="Request data"
    )
    json: Optional[Dict[str, Any]] = Field(default=None, description="JSON data")
    timeout: Optional[float] = Field(default=None, description="Request timeout")
    follow_redirects: bool = Field(default=True, description="Follow redirects")

    model_config = ConfigDict(use_enum_values=True)


class HTTPResponse(BaseModel):
    """HTTP response model."""

    status_code: int = Field(description="HTTP status code")
    headers: Dict[str, str] = Field(description="Response headers")
    content: Optional[bytes] = Field(default=None, description="Response content")
    text: Optional[str] = Field(default=None, description="Response text")
    json: Optional[Dict[str, Any]] = Field(default=None, description="Response JSON")
    url: str = Field(description="Final URL after redirects")
    elapsed: float = Field(description="Request elapsed time in seconds")

    model_config = ConfigDict(arbitrary_types_allowed=True)


class BaseHTTPClient(BaseComponent):
    """Base class for HTTP clients.

    Provides common functionality for all HTTP clients in the OPSVI ecosystem.
    """

    def __init__(self, config: HTTPConfig, **kwargs: Any) -> None:
        """Initialize HTTP client.

        Args:
            config: HTTP client configuration
            **kwargs: Additional configuration parameters
        """
        super().__init__(f"http-client-{id(self)}", config.model_dump())
        self.config = config
        self._session: Optional[Any] = None
        self._request_count = 0
        self._error_count = 0
        self._start_time = datetime.utcnow()

    async def _initialize_impl(self) -> None:
        """Initialize the HTTP client session."""
        try:
            self._session = await self._create_session()
            logger.info(
                f"Initialized HTTP client with base URL: {self.config.base_url}"
            )
        except Exception as e:
            logger.error(f"Failed to initialize HTTP client: {e}")
            raise HTTPClientError(f"Client initialization failed: {e}") from e

    async def _shutdown_impl(self) -> None:
        """Shutdown the HTTP client session."""
        try:
            if self._session:
                await self._close_session()
            logger.info("HTTP client shutdown successfully")
        except Exception as e:
            logger.error(f"Failed to shutdown HTTP client: {e}")
            raise HTTPClientError(f"Client shutdown failed: {e}") from e

    async def _health_check_impl(self) -> bool:
        """Health check implementation."""
        try:
            if not self._session:
                return False

            # Try a simple health check request
            if self.config.base_url:
                health_url = urljoin(self.config.base_url, "/health")
                try:
                    await self._make_request(
                        HTTPRequest(method=HTTPMethod.GET, url=health_url, timeout=5.0)
                    )
                    return True
                except Exception:
                    # Health endpoint might not exist, but client is functional
                    return True

            return True
        except Exception as e:
            logger.error(f"HTTP client health check failed: {e}")
            return False

    @abstractmethod
    async def _create_session(self) -> Any:
        """Create the HTTP session."""
        pass

    @abstractmethod
    async def _close_session(self) -> None:
        """Close the HTTP session."""
        pass

    @abstractmethod
    async def _make_request(self, request: HTTPRequest) -> HTTPResponse:
        """Make an HTTP request."""
        pass

    async def request(self, request: HTTPRequest) -> HTTPResponse:
        """Make an HTTP request with retry logic."""
        if not self._initialized:
            raise HTTPClientError("HTTP client not initialized")

        self._request_count += 1
        last_exception = None

        for attempt in range(self.config.max_retries + 1):
            try:
                response = await self._make_request(request)

                # Check if response indicates retry is needed
                if response.status_code >= 500 and attempt < self.config.max_retries:
                    raise HTTPResponseError(f"Server error: {response.status_code}")

                return response

            except (HTTPTimeoutError, HTTPResponseError) as e:
                last_exception = e
                if attempt < self.config.max_retries:
                    delay = self.config.retry_delay * (
                        self.config.backoff_factor**attempt
                    )
                    logger.warning(
                        f"Request failed (attempt {attempt + 1}/{self.config.max_retries + 1}), retrying in {delay}s: {e}"
                    )
                    await asyncio.sleep(delay)
                else:
                    break
            except Exception as e:
                self._error_count += 1
                logger.error(f"Request failed: {e}")
                raise HTTPRequestError(f"Request failed: {e}") from e

        self._error_count += 1
        raise HTTPRequestError(
            f"Request failed after {self.config.max_retries + 1} attempts: {last_exception}"
        ) from last_exception

    async def get(self, url: str, **kwargs: Any) -> HTTPResponse:
        """Make a GET request."""
        request = HTTPRequest(method=HTTPMethod.GET, url=url, **kwargs)
        return await self.request(request)

    async def post(self, url: str, **kwargs: Any) -> HTTPResponse:
        """Make a POST request."""
        request = HTTPRequest(method=HTTPMethod.POST, url=url, **kwargs)
        return await self.request(request)

    async def put(self, url: str, **kwargs: Any) -> HTTPResponse:
        """Make a PUT request."""
        request = HTTPRequest(method=HTTPMethod.PUT, url=url, **kwargs)
        return await self.request(request)

    async def delete(self, url: str, **kwargs: Any) -> HTTPResponse:
        """Make a DELETE request."""
        request = HTTPRequest(method=HTTPMethod.DELETE, url=url, **kwargs)
        return await self.request(request)

    async def patch(self, url: str, **kwargs: Any) -> HTTPResponse:
        """Make a PATCH request."""
        request = HTTPRequest(method=HTTPMethod.PATCH, url=url, **kwargs)
        return await self.request(request)

    def get_stats(self) -> Dict[str, Any]:
        """Get client statistics."""
        uptime = datetime.utcnow() - self._start_time
        return {
            "uptime_seconds": uptime.total_seconds(),
            "total_requests": self._request_count,
            "error_count": self._error_count,
            "success_rate": (self._request_count - self._error_count)
            / max(self._request_count, 1),
            "initialized": self._initialized,
        }

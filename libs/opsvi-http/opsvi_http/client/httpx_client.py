"""HTTPX-based HTTP client implementation for OPSVI HTTP library."""

import asyncio
import logging
from typing import Any, Dict, Optional
from datetime import datetime

import httpx
from pydantic import Field, ConfigDict

from .base import (
    BaseHTTPClient,
    HTTPConfig,
    HTTPRequest,
    HTTPResponse,
    HTTPMethod,
    HTTPClientError,
    HTTPRequestError,
    HTTPResponseError,
    HTTPTimeoutError,
)

logger = logging.getLogger(__name__)


class HTTPXConfig(HTTPConfig):
    """Configuration for HTTPX client."""

    # HTTPX-specific configuration
    http2: bool = Field(default=False, description="Enable HTTP/2 support")
    limits: Optional[Dict[str, int]] = Field(
        default=None, description="Connection limits"
    )
    transport: Optional[str] = Field(default=None, description="Custom transport")

    model_config = ConfigDict(env_prefix="OPSVI_HTTP_HTTPX_")


class HTTPXClient(BaseHTTPClient):
    """HTTPX-based HTTP client implementation."""

    def __init__(self, config: HTTPXConfig, **kwargs: Any) -> None:
        """Initialize HTTPX client.

        Args:
            config: HTTPX configuration
            **kwargs: Additional configuration parameters
        """
        super().__init__(config, **kwargs)
        self.httpx_config = config
        self._client: Optional[httpx.AsyncClient] = None

    async def _create_session(self) -> httpx.AsyncClient:
        """Create HTTPX async client."""
        # Prepare headers
        headers = self.httpx_config.default_headers.copy()
        headers.setdefault("User-Agent", self.httpx_config.user_agent)

        # Prepare limits
        limits = httpx.Limits(
            max_connections=self.httpx_config.max_connections,
            max_keepalive_connections=self.httpx_config.max_keepalive_connections,
            keepalive_expiry=self.httpx_config.keepalive_timeout,
        )

        # Prepare SSL configuration
        ssl_context = None
        if not self.httpx_config.verify_ssl:
            import ssl

            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE

        # Create client
        self._client = httpx.AsyncClient(
            base_url=self.httpx_config.base_url or "",
            headers=headers,
            timeout=httpx.Timeout(self.httpx_config.timeout),
            limits=limits,
            http2=self.httpx_config.http2,
            verify=ssl_context if ssl_context else self.httpx_config.verify_ssl,
            cert=(
                (self.httpx_config.ssl_cert, self.httpx_config.ssl_key)
                if self.httpx_config.ssl_cert
                else None
            ),
            proxy=self.httpx_config.proxy,
            follow_redirects=True,
        )

        return self._client

    async def _close_session(self) -> None:
        """Close HTTPX client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def _make_request(self, request: HTTPRequest) -> HTTPResponse:
        """Make an HTTP request using HTTPX."""
        if not self._client:
            raise HTTPClientError("HTTPX client not initialized")

        start_time = datetime.utcnow()

        try:
            # Prepare request parameters
            method = (
                request.method.value
                if hasattr(request.method, "value")
                else request.method
            )
            url = request.url
            headers = request.headers or {}
            params = request.params
            timeout = request.timeout or self.httpx_config.timeout

            # Prepare request data
            request_data = None
            if request.json is not None:
                request_data = request.json
            elif request.data is not None:
                request_data = request.data

            # Make request
            response = await self._client.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                json=request_data if isinstance(request_data, dict) else None,
                data=request_data if not isinstance(request_data, dict) else None,
                timeout=timeout,
                follow_redirects=request.follow_redirects,
            )

            elapsed = (datetime.utcnow() - start_time).total_seconds()

            # Parse response
            content = response.content
            text = response.text if content else None

            # Try to parse JSON
            json_data = None
            if text and response.headers.get("content-type", "").startswith(
                "application/json"
            ):
                try:
                    json_data = response.json()
                except Exception:
                    pass

            return HTTPResponse(
                status_code=response.status_code,
                headers=dict(response.headers),
                content=content,
                text=text,
                json=json_data,
                url=str(response.url),
                elapsed=elapsed,
            )

        except httpx.TimeoutException as e:
            elapsed = (datetime.utcnow() - start_time).total_seconds()
            logger.error(f"HTTPX request timeout after {elapsed}s: {e}")
            raise HTTPTimeoutError(f"Request timeout: {e}") from e

        except httpx.HTTPStatusError as e:
            elapsed = (datetime.utcnow() - start_time).total_seconds()
            logger.error(f"HTTPX HTTP error after {elapsed}s: {e}")
            raise HTTPResponseError(f"HTTP error {e.response.status_code}: {e}") from e

        except httpx.RequestError as e:
            elapsed = (datetime.utcnow() - start_time).total_seconds()
            logger.error(f"HTTPX request error after {elapsed}s: {e}")
            raise HTTPRequestError(f"Request error: {e}") from e

        except Exception as e:
            elapsed = (datetime.utcnow() - start_time).total_seconds()
            logger.error(f"HTTPX unexpected error after {elapsed}s: {e}")
            raise HTTPRequestError(f"Unexpected error: {e}") from e

    async def stream(self, method: HTTPMethod, url: str, **kwargs: Any) -> Any:
        """Stream a response."""
        if not self._client:
            raise HTTPClientError("HTTPX client not initialized")

        method_str = method.value if hasattr(method, "value") else method
        return await self._client.stream(method_str, url, **kwargs)

    async def get_stream(self, url: str, **kwargs: Any) -> Any:
        """Stream a GET response."""
        return await self.stream(HTTPMethod.GET, url, **kwargs)

    async def post_stream(self, url: str, **kwargs: Any) -> Any:
        """Stream a POST response."""
        return await self.stream(HTTPMethod.POST, url, **kwargs)

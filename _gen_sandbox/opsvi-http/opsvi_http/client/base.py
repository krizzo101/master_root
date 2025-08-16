"""HTTP client base for opsvi-http.

Provides an abstract HTTPClient with common request handling, timeout
management, header merging from configuration, and convenience HTTP
method helpers. Concrete adapters should implement _send.
"""
from typing import Any, Dict, Optional, Tuple, Type
import logging
import asyncio
from abc import abstractmethod

from opsvi_http.core.base import OpsviHttpManager
from opsvi_http.config.settings import OpsviHttpConfig
from opsvi_http.exceptions.base import OpsviHttpError

logger = logging.getLogger(__name__)


class HTTPClient(OpsviHttpManager):
    """Abstract base HTTP client.

    Subclasses must implement _send() to perform the actual request using a
    concrete HTTP library (aiohttp, httpx, etc.). This base class takes care
    of parameter normalization, timeout handling, default headers from
    configuration, and translating exceptions into OpsviHttpError.
    """

    def __init__(self, config: Optional[OpsviHttpConfig] = None) -> None:
        super().__init__()
        self.config = config or OpsviHttpConfig()

    @abstractmethod
    async def _send(self, method: str, url: str, **kwargs: Any) -> Any:
        """Perform the actual HTTP request.

        Must be implemented by concrete adapters. Should raise exceptions
        that will be wrapped into OpsviHttpError by request() where
        appropriate.
        """

    async def request(self, method: str, url: str, **kwargs: Any) -> Any:
        """Send an HTTP request with basic error and timeout handling.

        Accepted kwargs: params, headers, json, data, timeout (float seconds),
        and any library-specific passthroughs.
        """
        method = (method or "GET").upper()
        if not url:
            raise OpsviHttpError("URL must be provided")

        # Merge default headers from config if present
        headers: Dict[str, str] = {}
        if hasattr(self.config, "default_headers") and self.config.default_headers:
            headers.update(self.config.default_headers)
        if "headers" in kwargs and kwargs["headers"]:
            # allow callers to pass None
            provided = kwargs.pop("headers") or {}
            headers.update(provided)
        if headers:
            kwargs["headers"] = headers

        # Determine timeout
        timeout = kwargs.pop("timeout", None)
        if timeout is None and getattr(self.config, "timeout", None) is not None:
            timeout = self.config.timeout

        try:
            if timeout is None:
                return await self._send(method, url, **kwargs)

            # Use asyncio.wait_for to apply timeout to the send operation
            return await asyncio.wait_for(self._send(method, url, **kwargs), timeout)
        except asyncio.TimeoutError as exc:
            logger.exception("Request timed out: %s %s", method, url)
            raise OpsviHttpError("request timeout") from exc
        except OpsviHttpError:
            # Pass through our own errors
            raise
        except Exception as exc:  # pragma: no cover - wrap other errors
            logger.exception("HTTP request failed: %s %s", method, url)
            raise OpsviHttpError("request failed") from exc

    # Convenience helpers for common HTTP methods
    async def get(self, url: str, **kwargs: Any) -> Any:
        """Perform a GET request."""
        return await self.request("GET", url, **kwargs)

    async def post(self, url: str, **kwargs: Any) -> Any:
        """Perform a POST request."""
        return await self.request("POST", url, **kwargs)

    async def put(self, url: str, **kwargs: Any) -> Any:
        """Perform a PUT request."""
        return await self.request("PUT", url, **kwargs)

    async def patch(self, url: str, **kwargs: Any) -> Any:
        """Perform a PATCH request."""
        return await self.request("PATCH", url, **kwargs)

    async def delete(self, url: str, **kwargs: Any) -> Any:
        """Perform a DELETE request."""
        return await self.request("DELETE", url, **kwargs)

    async def head(self, url: str, **kwargs: Any) -> Any:
        """Perform a HEAD request."""
        return await self.request("HEAD", url, **kwargs)

    async def options(self, url: str, **kwargs: Any) -> Any:
        """Perform an OPTIONS request."""
        return await self.request("OPTIONS", url, **kwargs)

    # Async context manager support for convenience
    async def __aenter__(self) -> "HTTPClient":
        return self

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc: Optional[BaseException],
        tb: Optional[Any],
    ) -> None:
        # Prefer an async close method if implemented by subclasses
        aclose = getattr(self, "aclose", None)
        if callable(aclose):
            result = aclose()
            if asyncio.iscoroutine(result):
                await result
            return

        # Fall back to sync close if provided
        close = getattr(self, "close", None)
        if callable(close):
            try:
                close()
            except Exception:
                logger.exception("Error during client close")

    async def aclose(self) -> None:
        """Default no-op async close hook.

        Subclasses may override this to perform asynchronous cleanup.
        """
        return None

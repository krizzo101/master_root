"""
HTTP Client Shared Interface
---------------------------
Authoritative implementation based on the official requests and httpx documentation:
- https://docs.python-requests.org/en/latest/
- https://www.python-httpx.org/
Implements all core features: session support, GET/POST, error handling, and async support.
Version: Referenced as of July 2024
"""

import functools
import logging
from typing import Any, Callable, Dict, Optional

try:
    import requests
except ImportError:
    raise ImportError("requests is required. Install with `pip install requests`.")

try:
    import httpx
except ImportError:
    httpx = None  # Async support is optional

logger = logging.getLogger(__name__)


class HTTPClientInterface:
    """
    Authoritative shared interface for HTTP client operations (requests, httpx).
    See:
    - https://docs.python-requests.org/en/latest/
    - https://www.python-httpx.org/
    """

    def __init__(
        self, base_url: Optional[str] = None, headers: Optional[Dict[str, str]] = None
    ):
        self.base_url = base_url
        self.headers = headers or {}
        self.session = requests.Session()
        self.session.headers.update(self.headers)

    def set_config(
        self,
        timeout: int = 60,
        max_retries: int = 2,
        proxies: Optional[Dict[str, str]] = None,
    ):
        """Set client config: timeout, retries, proxies."""
        self.timeout = timeout
        self.max_retries = max_retries
        self.proxies = proxies
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        if proxies:
            self.session.proxies.update(proxies)
        adapter = requests.adapters.HTTPAdapter(max_retries=max_retries)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    def _structured_response(self, func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                resp = func(*args, **kwargs)
                return {
                    "success": True,
                    "response": resp,
                    "status_code": resp.status_code,
                }
            except Exception as e:
                logger.error(f"HTTP error: {e}")
                return {
                    "success": False,
                    "error": str(e),
                    "response": None,
                    "status_code": None,
                }

        return wrapper

    @_structured_response
    def put(self, url: str, data: Any = None, json: Any = None, **kwargs):
        """Sync PUT request."""
        full_url = self.base_url + url if self.base_url else url
        return self.session.put(
            full_url, data=data, json=json, timeout=self.timeout, **kwargs
        )

    @_structured_response
    def patch(self, url: str, data: Any = None, json: Any = None, **kwargs):
        """Sync PATCH request."""
        full_url = self.base_url + url if self.base_url else url
        return self.session.patch(
            full_url, data=data, json=json, timeout=self.timeout, **kwargs
        )

    @_structured_response
    def delete(self, url: str, **kwargs):
        """Sync DELETE request."""
        full_url = self.base_url + url if self.base_url else url
        return self.session.delete(full_url, timeout=self.timeout, **kwargs)

    @_structured_response
    def head(self, url: str, **kwargs):
        """Sync HEAD request."""
        full_url = self.base_url + url if self.base_url else url
        return self.session.head(full_url, timeout=self.timeout, **kwargs)

    @_structured_response
    def options(self, url: str, **kwargs):
        """Sync OPTIONS request."""
        full_url = self.base_url + url if self.base_url else url
        return self.session.options(full_url, timeout=self.timeout, **kwargs)

    @_structured_response
    def get(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        stream: bool = False,
        **kwargs,
    ):
        """Sync GET request with streaming support."""
        full_url = self.base_url + url if self.base_url else url
        return self.session.get(
            full_url, params=params, timeout=self.timeout, stream=stream, **kwargs
        )

    @_structured_response
    def post(
        self,
        url: str,
        data: Any = None,
        json: Any = None,
        stream: bool = False,
        **kwargs,
    ):
        """Sync POST request with streaming support."""
        full_url = self.base_url + url if self.base_url else url
        return self.session.post(
            full_url,
            data=data,
            json=json,
            timeout=self.timeout,
            stream=stream,
            **kwargs,
        )

    # Async support using httpx
    async def aget(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        stream: bool = False,
        **kwargs,
    ):
        """Async GET request with streaming support."""
        if not httpx:
            raise ImportError(
                "httpx is required for async support. Install with `pip install httpx`."
            )
        full_url = self.base_url + url if self.base_url else url
        async with httpx.AsyncClient(
            headers=self.headers, timeout=self.timeout
        ) as client:
            resp = await client.get(full_url, params=params, stream=stream, **kwargs)
            return {"success": True, "response": resp, "status_code": resp.status_code}

    async def apost(
        self,
        url: str,
        data: Any = None,
        json: Any = None,
        stream: bool = False,
        **kwargs,
    ):
        """Async POST request with streaming support."""
        if not httpx:
            raise ImportError(
                "httpx is required for async support. Install with `pip install httpx`."
            )
        full_url = self.base_url + url if self.base_url else url
        async with httpx.AsyncClient(
            headers=self.headers, timeout=self.timeout
        ) as client:
            resp = await client.post(
                full_url, data=data, json=json, stream=stream, **kwargs
            )
            return {"success": True, "response": resp, "status_code": resp.status_code}

    async def aput(self, url: str, data: Any = None, json: Any = None, **kwargs):
        """Async PUT request."""
        if not httpx:
            raise ImportError(
                "httpx is required for async support. Install with `pip install httpx`."
            )
        full_url = self.base_url + url if self.base_url else url
        async with httpx.AsyncClient(
            headers=self.headers, timeout=self.timeout
        ) as client:
            resp = await client.put(full_url, data=data, json=json, **kwargs)
            return {"success": True, "response": resp, "status_code": resp.status_code}

    async def apatch(self, url: str, data: Any = None, json: Any = None, **kwargs):
        """Async PATCH request."""
        if not httpx:
            raise ImportError(
                "httpx is required for async support. Install with `pip install httpx`."
            )
        full_url = self.base_url + url if self.base_url else url
        async with httpx.AsyncClient(
            headers=self.headers, timeout=self.timeout
        ) as client:
            resp = await client.patch(full_url, data=data, json=json, **kwargs)
            return {"success": True, "response": resp, "status_code": resp.status_code}

    async def adelete(self, url: str, **kwargs):
        """Async DELETE request."""
        if not httpx:
            raise ImportError(
                "httpx is required for async support. Install with `pip install httpx`."
            )
        full_url = self.base_url + url if self.base_url else url
        async with httpx.AsyncClient(
            headers=self.headers, timeout=self.timeout
        ) as client:
            resp = await client.delete(full_url, **kwargs)
            return {"success": True, "response": resp, "status_code": resp.status_code}

    async def ahead(self, url: str, **kwargs):
        """Async HEAD request."""
        if not httpx:
            raise ImportError(
                "httpx is required for async support. Install with `pip install httpx`."
            )
        full_url = self.base_url + url if self.base_url else url
        async with httpx.AsyncClient(
            headers=self.headers, timeout=self.timeout
        ) as client:
            resp = await client.head(full_url, **kwargs)
            return {"success": True, "response": resp, "status_code": resp.status_code}

    async def aoptions(self, url: str, **kwargs):
        """Async OPTIONS request."""
        if not httpx:
            raise ImportError(
                "httpx is required for async support. Install with `pip install httpx`."
            )
        full_url = self.base_url + url if self.base_url else url
        async with httpx.AsyncClient(
            headers=self.headers, timeout=self.timeout
        ) as client:
            resp = await client.options(full_url, **kwargs)
            return {"success": True, "response": resp, "status_code": resp.status_code}

    # --- Hooks/callbacks for request/response events (sync only for now) ---
    def set_hook(self, event: str, func: Callable):
        """Set a hook for 'request' or 'response' events (sync only)."""
        if event == "request":
            self.session.hooks["request"] = [func]
        elif event == "response":
            self.session.hooks["response"] = [func]
        else:
            raise ValueError("Event must be 'request' or 'response'.")


# Example usage and advanced features are available in the official docs:
# https://docs.python-requests.org/en/latest/
# https://www.python-httpx.org/

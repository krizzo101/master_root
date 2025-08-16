"""Tests for OPSVI HTTP client functionality."""

import pytest
import asyncio
from typing import Dict, Any
from unittest.mock import AsyncMock, MagicMock

from opsvi_http import (
    HTTPXClient,
    HTTPXConfig,
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
from opsvi_foundation import ComponentError


class MockHTTPXResponse:
    """Mock HTTPX response for testing."""

    def __init__(
        self,
        status_code: int,
        content: bytes,
        text: str,
        headers: Dict[str, str],
        url: str,
    ):
        self.status_code = status_code
        self.content = content
        self.text = text
        self.headers = headers
        self.url = url

    def json(self):
        """Mock JSON method."""
        return {"status": "ok"}


class MockHTTPXClient:
    """Mock HTTPX client for testing."""

    def __init__(self):
        self.request = AsyncMock()
        self.aclose = AsyncMock()

    def stream(self, method: str, url: str, **kwargs):
        """Mock stream method."""
        return AsyncMock()


@pytest.fixture
def http_config():
    """Create a test HTTP configuration."""
    return HTTPXConfig(
        base_url="https://api.example.com",
        timeout=30.0,
        max_retries=3,
        user_agent="Test-Agent/1.0",
    )


@pytest.fixture
def mock_httpx_client(monkeypatch):
    """Mock HTTPX client."""
    mock_client = MockHTTPXClient()

    async def mock_async_client(*args, **kwargs):
        return mock_client

    monkeypatch.setattr("httpx.AsyncClient", mock_async_client)
    return mock_client


class TestHTTPXConfig:
    """Test HTTPX configuration."""

    def test_http_config_defaults(self):
        """Test HTTP config default values."""
        config = HTTPXConfig()

        assert config.base_url is None
        assert config.timeout == 30.0
        assert config.max_retries == 3
        assert config.retry_delay == 1.0
        assert config.backoff_factor == 2.0
        assert config.max_connections == 100
        assert config.max_keepalive_connections == 20
        assert config.keepalive_timeout == 30.0
        assert config.default_headers == {}
        assert config.user_agent == "OPSVI-HTTP/1.0"
        assert config.verify_ssl is True
        assert config.http2 is False

    def test_http_config_custom_values(self):
        """Test HTTP config with custom values."""
        config = HTTPXConfig(
            base_url="https://api.test.com",
            timeout=60.0,
            max_retries=5,
            user_agent="Custom-Agent/2.0",
            http2=True,
        )

        assert config.base_url == "https://api.test.com"
        assert config.timeout == 60.0
        assert config.max_retries == 5
        assert config.user_agent == "Custom-Agent/2.0"
        assert config.http2 is True


class TestHTTPRequest:
    """Test HTTP request model."""

    def test_http_request_creation(self):
        """Test HTTP request creation."""
        request = HTTPRequest(
            method=HTTPMethod.GET,
            url="https://api.example.com/test",
            headers={"Authorization": "Bearer token"},
            params={"page": 1},
            timeout=10.0,
        )

        assert request.method == HTTPMethod.GET
        assert request.url == "https://api.example.com/test"
        assert request.headers == {"Authorization": "Bearer token"}
        assert request.params == {"page": 1}
        assert request.timeout == 10.0
        assert request.follow_redirects is True

    def test_http_request_defaults(self):
        """Test HTTP request default values."""
        request = HTTPRequest(
            method=HTTPMethod.POST,
            url="https://api.example.com/test",
        )

        assert request.method == HTTPMethod.POST
        assert request.url == "https://api.example.com/test"
        assert request.headers is None
        assert request.params is None
        assert request.data is None
        assert request.json is None
        assert request.timeout is None
        assert request.follow_redirects is True


class TestHTTPResponse:
    """Test HTTP response model."""

    def test_http_response_creation(self):
        """Test HTTP response creation."""
        response = HTTPResponse(
            status_code=200,
            headers={"Content-Type": "application/json"},
            content=b'{"status": "ok"}',
            text='{"status": "ok"}',
            json={"status": "ok"},
            url="https://api.example.com/test",
            elapsed=0.5,
        )

        assert response.status_code == 200
        assert response.headers == {"Content-Type": "application/json"}
        assert response.content == b'{"status": "ok"}'
        assert response.text == '{"status": "ok"}'
        assert response.json == {"status": "ok"}
        assert response.url == "https://api.example.com/test"
        assert response.elapsed == 0.5

    def test_http_response_defaults(self):
        """Test HTTP response default values."""
        response = HTTPResponse(
            status_code=404,
            headers={},
            url="https://api.example.com/not-found",
            elapsed=0.1,
        )

        assert response.status_code == 404
        assert response.headers == {}
        assert response.content is None
        assert response.text is None
        assert response.json is None
        assert response.url == "https://api.example.com/not-found"
        assert response.elapsed == 0.1


class TestHTTPXClient:
    """Test HTTPX client functionality."""

    @pytest.mark.asyncio
    async def test_http_client_initialization(self, http_config, mock_httpx_client):
        """Test HTTPX client initialization."""
        client = HTTPXClient(http_config)
        await client.initialize()

        assert client._initialized
        assert client._client is not None
        await client.shutdown()

    @pytest.mark.asyncio
    async def test_http_client_get_request(self, http_config, mock_httpx_client):
        """Test HTTPX client GET request."""
        # Setup mock response
        mock_response = MockHTTPXResponse(
            status_code=200,
            content=b'{"status": "ok"}',
            text='{"status": "ok"}',
            headers={"Content-Type": "application/json"},
            url="https://api.example.com/test",
        )
        mock_httpx_client.request.return_value = mock_response

        client = HTTPXClient(http_config)
        await client.initialize()

        response = await client.get("https://api.example.com/test")

        assert response.status_code == 200
        assert response.headers == {"Content-Type": "application/json"}
        assert response.text == '{"status": "ok"}'
        assert response.json == {"status": "ok"}

        await client.shutdown()

    @pytest.mark.asyncio
    async def test_http_client_post_request(self, http_config, mock_httpx_client):
        """Test HTTPX client POST request."""
        # Setup mock response
        mock_response = MockHTTPXResponse(
            status_code=201,
            content=b'{"id": 123}',
            text='{"id": 123}',
            headers={"Content-Type": "application/json"},
            url="https://api.example.com/resource",
        )
        mock_httpx_client.request.return_value = mock_response

        client = HTTPXClient(http_config)
        await client.initialize()

        response = await client.post(
            "https://api.example.com/resource",
            json={"name": "test"},
        )

        assert response.status_code == 201
        assert response.json == {"id": 123}

        await client.shutdown()

    @pytest.mark.asyncio
    async def test_http_client_put_request(self, http_config, mock_httpx_client):
        """Test HTTPX client PUT request."""
        # Setup mock response
        mock_response = MockHTTPXResponse(
            status_code=200,
            content=b'{"updated": true}',
            text='{"updated": true}',
            headers={"Content-Type": "application/json"},
            url="https://api.example.com/resource/123",
        )
        mock_httpx_client.request.return_value = mock_response

        client = HTTPXClient(http_config)
        await client.initialize()

        response = await client.put(
            "https://api.example.com/resource/123",
            json={"name": "updated"},
        )

        assert response.status_code == 200
        assert response.json == {"updated": True}

        await client.shutdown()

    @pytest.mark.asyncio
    async def test_http_client_delete_request(self, http_config, mock_httpx_client):
        """Test HTTPX client DELETE request."""
        # Setup mock response
        mock_response = MockHTTPXResponse(
            status_code=204,
            content=b"",
            text="",
            headers={},
            url="https://api.example.com/resource/123",
        )
        mock_httpx_client.request.return_value = mock_response

        client = HTTPXClient(http_config)
        await client.initialize()

        response = await client.delete("https://api.example.com/resource/123")

        assert response.status_code == 204
        assert response.content == b""

        await client.shutdown()

    @pytest.mark.asyncio
    async def test_http_client_patch_request(self, http_config, mock_httpx_client):
        """Test HTTPX client PATCH request."""
        # Setup mock response
        mock_response = MockHTTPXResponse(
            status_code=200,
            content=b'{"patched": true}',
            text='{"patched": true}',
            headers={"Content-Type": "application/json"},
            url="https://api.example.com/resource/123",
        )
        mock_httpx_client.request.return_value = mock_response

        client = HTTPXClient(http_config)
        await client.initialize()

        response = await client.patch(
            "https://api.example.com/resource/123",
            json={"field": "value"},
        )

        assert response.status_code == 200
        assert response.json == {"patched": True}

        await client.shutdown()

    @pytest.mark.asyncio
    async def test_http_client_health_check(self, http_config, mock_httpx_client):
        """Test HTTPX client health check."""
        # Setup mock response for health check
        mock_response = MockHTTPXResponse(
            status_code=200,
            content=b'{"status": "healthy"}',
            text='{"status": "healthy"}',
            headers={"Content-Type": "application/json"},
            url="https://api.example.com/health",
        )
        mock_httpx_client.request.return_value = mock_response

        client = HTTPXClient(http_config)
        await client.initialize()

        # Health check should pass
        assert await client.health_check()

        await client.shutdown()

    @pytest.mark.asyncio
    async def test_http_client_stats(self, http_config, mock_httpx_client):
        """Test HTTPX client statistics."""
        client = HTTPXClient(http_config)
        await client.initialize()

        stats = client.get_stats()

        assert "uptime_seconds" in stats
        assert "total_requests" in stats
        assert "error_count" in stats
        assert "success_rate" in stats
        assert "initialized" in stats
        assert stats["initialized"] is True
        assert stats["total_requests"] == 0
        assert stats["error_count"] == 0

        await client.shutdown()

    @pytest.mark.asyncio
    async def test_http_client_stream(self, http_config, mock_httpx_client):
        """Test HTTPX client streaming."""
        client = HTTPXClient(http_config)
        await client.initialize()

        # Test stream method
        stream_response = await client.get_stream("https://api.example.com/stream")
        assert stream_response is not None

        # Test post stream method
        stream_response = await client.post_stream("https://api.example.com/stream")
        assert stream_response is not None

        await client.shutdown()


class TestHTTPExceptions:
    """Test HTTP exception classes."""

    def test_http_error_inheritance(self):
        """Test HTTP error inheritance."""
        error = HTTPError("Test error")
        assert isinstance(error, HTTPError)
        assert isinstance(error, ComponentError)
        assert str(error) == "Test error"

    def test_http_client_error_inheritance(self):
        """Test HTTP client error inheritance."""
        error = HTTPClientError("Client error")
        assert isinstance(error, HTTPError)
        assert str(error) == "Client error"

    def test_http_request_error_inheritance(self):
        """Test HTTP request error inheritance."""
        error = HTTPRequestError("Request error")
        assert isinstance(error, HTTPError)
        assert str(error) == "Request error"

    def test_http_response_error_inheritance(self):
        """Test HTTP response error inheritance."""
        error = HTTPResponseError("Response error")
        assert isinstance(error, HTTPError)
        assert str(error) == "Response error"

    def test_http_timeout_error_inheritance(self):
        """Test HTTP timeout error inheritance."""
        error = HTTPTimeoutError("Timeout error")
        assert isinstance(error, HTTPError)
        assert str(error) == "Timeout error"


class TestHTTPMethod:
    """Test HTTP method enumeration."""

    def test_http_method_values(self):
        """Test HTTP method values."""
        assert HTTPMethod.GET.value == "GET"
        assert HTTPMethod.POST.value == "POST"
        assert HTTPMethod.PUT.value == "PUT"
        assert HTTPMethod.DELETE.value == "DELETE"
        assert HTTPMethod.PATCH.value == "PATCH"
        assert HTTPMethod.HEAD.value == "HEAD"
        assert HTTPMethod.OPTIONS.value == "OPTIONS"


class TestHTTPStatus:
    """Test HTTP status enumeration."""

    def test_http_status_values(self):
        """Test HTTP status values."""
        assert HTTPStatus.OK.value == 200
        assert HTTPStatus.CREATED.value == 201
        assert HTTPStatus.BAD_REQUEST.value == 400
        assert HTTPStatus.UNAUTHORIZED.value == 401
        assert HTTPStatus.NOT_FOUND.value == 404
        assert HTTPStatus.INTERNAL_SERVER_ERROR.value == 500

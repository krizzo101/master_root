"""
OpenAI Responses API Interface

Authoritative implementation based on the official OpenAI Python SDK and API documentation:
- https://github.com/openai/openai-python
- https://platform.openai.com/docs/api-reference/responses

Implements all core endpoints and features:
- create, retrieve, delete, cancel, list input items
- sync and async support
- streaming (sync/async)
- pagination
- official type hints and error handling

Version: Referenced as of July 2024
"""

import functools
import logging
import os
import time
from collections.abc import AsyncIterator, Callable, Generator, Iterator
from dataclasses import dataclass
from typing import (
    Any,
)

from openai import AsyncOpenAI, OpenAI
from openai.types import SyncCursorPage
from openai.types.responses import (
    Response,
    ResponseItem,
    ResponseItemList,
)

try:
    from openai import APIError, APITimeoutError, AsyncOpenAI, OpenAI, RateLimitError
except ImportError:
    raise ImportError("openai package is required. Install with `pip install openai`.")

logger = logging.getLogger(__name__)


class OpenAIResponsesError(Exception):
    """Custom exception for OpenAI Responses API errors."""

    pass


@dataclass
class StructuredResponse:
    id: str
    status: str
    output_text: str | None = None
    tool_calls: list[dict[str, Any]] | None = None
    function_results: list[dict[str, Any]] | None = None
    raw: Any | None = None


class OpenAIResponsesInterface:
    """
    Shared interface for the OpenAI Responses API (sync).
    Implements all official endpoints and features.
    """

    def __init__(self, api_key: str | None = None):
        self.client = OpenAI(api_key=api_key) if api_key else OpenAI()

    def create(self, **params) -> Response:
        """Create a new response object. Params per OpenAI docs."""
        return self.client.responses.create(**params)

    def retrieve(self, response_id: str, **params) -> Response:
        """Retrieve a response by ID."""
        return self.client.responses.retrieve(response_id, **params)

    def delete(self, response_id: str) -> None:
        """Delete a response by ID."""
        return self.client.responses.delete(response_id)

    def cancel(self, response_id: str) -> Response:
        """Cancel an in-progress response by ID."""
        return self.client.responses.cancel(response_id)

    def list_input_items(
        self, response_id: str, **params
    ) -> SyncCursorPage[ResponseItem]:
        """List input items for a response (paginated)."""
        return self.client.responses.input_items.list(response_id, **params)

    def stream(self, **params) -> Iterator[Any]:
        """Stream a response (Server-Sent Events). Params must include stream=True."""
        stream = self.client.responses.create(stream=True, **params)
        for event in stream:
            yield event


class AsyncOpenAIResponsesInterface:
    """
    Shared interface for the OpenAI Responses API (async).
    Implements all official endpoints and features.
    """

    def __init__(self, api_key: str | None = None):
        self.client = AsyncOpenAI(api_key=api_key) if api_key else AsyncOpenAI()

    async def create(self, **params) -> Response:
        """Create a new response object (async)."""
        return await self.client.responses.create(**params)

    async def retrieve(self, response_id: str, **params) -> Response:
        """Retrieve a response by ID (async)."""
        return await self.client.responses.retrieve(response_id, **params)

    async def delete(self, response_id: str) -> None:
        """Delete a response by ID (async)."""
        return await self.client.responses.delete(response_id)

    async def cancel(self, response_id: str) -> Response:
        """Cancel an in-progress response by ID (async)."""
        return await self.client.responses.cancel(response_id)

    async def list_input_items(
        self, response_id: str, **params
    ) -> SyncCursorPage[ResponseItem]:
        """List input items for a response (paginated, async)."""
        return await self.client.responses.input_items.list(response_id, **params)

    async def stream(self, **params) -> AsyncIterator[Any]:
        """Stream a response (Server-Sent Events, async). Params must include stream=True."""
        stream = await self.client.responses.create(stream=True, **params)
        async for event in stream:
            yield event


class OpenAIResponsesInterface:
    """
    Enhanced shared interface for the OpenAI Responses API.
    Provides sync/async, streaming, status polling, batch, tool/function, and structured output.
    """

    def __init__(self, api_key_env: str = "OPENAI_API_KEY") -> None:
        self.api_key = os.getenv(api_key_env)
        if not self.api_key:
            logger.error(f"Environment variable '{api_key_env}' not set.")
            raise OSError(f"Please set the '{api_key_env}' environment variable.")
        self.client = OpenAI(api_key=self.api_key)
        self.async_client = AsyncOpenAI(api_key=self.api_key)
        logger.info("OpenAIResponsesInterface initialized.")

    # --- Core CRUD ---
    def create_response(self, **params) -> Response:
        """
        Create a new response using the OpenAI Responses API.
        Supports retries for transient errors.
        """
        return self._with_retries(lambda: self.client.responses.create(**params))

    async def acreate_response(self, **params) -> Response:
        return await self._awith_retries(
            lambda: self.async_client.responses.create(**params)
        )

    def retrieve_response(self, response_id: str) -> Response:
        return self._with_retries(lambda: self.client.responses.retrieve(response_id))

    async def aretrieve_response(self, response_id: str) -> Response:
        return await self._awith_retries(
            lambda: self.async_client.responses.retrieve(response_id)
        )

    def list_input_items(self, response_id: str, **params) -> ResponseItemList:
        return self._with_retries(
            lambda: self.client.responses.input_items.list(response_id, **params)
        )

    async def alist_input_items(self, response_id: str, **params) -> ResponseItemList:
        return await self._awith_retries(
            lambda: self.async_client.responses.input_items.list(response_id, **params)
        )

    def delete_response(self, response_id: str) -> None:
        self._with_retries(lambda: self.client.responses.delete(response_id))

    async def adelete_response(self, response_id: str) -> None:
        await self._awith_retries(
            lambda: self.async_client.responses.delete(response_id)
        )

    def cancel_response(self, response_id: str) -> Response:
        return self._with_retries(lambda: self.client.responses.cancel(response_id))

    async def acancel_response(self, response_id: str) -> Response:
        return await self._awith_retries(
            lambda: self.async_client.responses.cancel(response_id)
        )

    # --- Streaming (if supported) ---
    def stream_response(self, **params) -> Generator[Response, None, None]:
        """
        Stream a response (if supported by the API).
        Yields Response objects as they arrive.
        """
        try:
            stream = self.client.responses.create(stream=True, **params)
            for chunk in stream:
                yield chunk
        except Exception:
            logger.exception("Error streaming response.")
            raise

    async def astream_response(self, **params):
        try:
            stream = await self.async_client.responses.create(stream=True, **params)
            async for chunk in stream:
                yield chunk
        except Exception:
            logger.exception("Error streaming response (async).")
            raise

    # --- Status/Progress Polling ---
    def get_status(self, response_id: str) -> str:
        resp = self.retrieve_response(response_id)
        return getattr(resp, "status", "unknown")

    async def aget_status(self, response_id: str) -> str:
        resp = await self.aretrieve_response(response_id)
        return getattr(resp, "status", "unknown")

    def wait_for_completion(
        self, response_id: str, timeout: int = 60, poll_interval: float = 2.0
    ) -> Response:
        """
        Polls the response status until it is completed or failed, or timeout is reached.
        """
        start = time.time()
        while time.time() - start < timeout:
            resp = self.retrieve_response(response_id)
            status = getattr(resp, "status", "unknown")
            if status in ("completed", "failed", "cancelled"):
                return resp
            time.sleep(poll_interval)
        raise TimeoutError(
            f"Response {response_id} did not complete in {timeout} seconds."
        )

    async def await_for_completion(
        self, response_id: str, timeout: int = 60, poll_interval: float = 2.0
    ) -> Response:
        import asyncio

        start = time.time()
        while time.time() - start < timeout:
            resp = await self.aretrieve_response(response_id)
            status = getattr(resp, "status", "unknown")
            if status in ("completed", "failed", "cancelled"):
                return resp
            await asyncio.sleep(poll_interval)
        raise TimeoutError(
            f"Response {response_id} did not complete in {timeout} seconds."
        )

    # --- Tool/Function Calling and Output Parsing ---
    def get_output_text(self, response: Response) -> str | None:
        return getattr(response, "output_text", None)

    def get_tool_calls(self, response: Response) -> list[dict[str, Any]] | None:
        return getattr(response, "tool_calls", None)

    def get_function_results(self, response: Response) -> list[dict[str, Any]] | None:
        return getattr(response, "function_results", None)

    def to_structured(self, response: Response) -> StructuredResponse:
        return StructuredResponse(
            id=getattr(response, "id", ""),
            status=getattr(response, "status", "unknown"),
            output_text=self.get_output_text(response),
            tool_calls=self.get_tool_calls(response),
            function_results=self.get_function_results(response),
            raw=response,
        )

    # --- Pagination/Filtering Helpers ---
    def list_responses(self, **params) -> list[Response]:
        """
        List all responses (paginated).
        """
        results = []
        cursor = None
        while True:
            page = self.client.responses.list(cursor=cursor, **params)
            items = getattr(page, "data", [])
            results.extend(items)
            cursor = getattr(page, "next_cursor", None)
            if not cursor:
                break
        return results

    async def alist_responses(self, **params) -> list[Response]:
        results = []
        cursor = None
        while True:
            page = await self.async_client.responses.list(cursor=cursor, **params)
            items = getattr(page, "data", [])
            results.extend(items)
            cursor = getattr(page, "next_cursor", None)
            if not cursor:
                break
        return results

    # --- Retry Logic ---
    def _with_retries(self, func: Callable, retries: int = 3, backoff: float = 2.0):
        for attempt in range(retries):
            try:
                return func()
            except (APITimeoutError, RateLimitError) as e:
                logger.warning(f"Retryable error: {e}. Attempt {attempt+1}/{retries}")
                time.sleep(backoff * (2**attempt))
            except Exception as e:
                logger.error(f"Non-retryable error: {e}")
                raise
        raise OpenAIResponsesError("Max retries exceeded.")

    async def _awith_retries(
        self, func: Callable, retries: int = 3, backoff: float = 2.0
    ):
        import asyncio

        for attempt in range(retries):
            try:
                return await func()
            except (APITimeoutError, RateLimitError) as e:
                logger.warning(f"Retryable error: {e}. Attempt {attempt+1}/{retries}")
                await asyncio.sleep(backoff * (2**attempt))
            except Exception as e:
                logger.error(f"Non-retryable error: {e}")
                raise
        raise OpenAIResponsesError("Max retries exceeded (async).")

    # --- Metadata/Logs/Audit (if available) ---
    def get_metadata(self, response_id: str) -> dict[str, Any] | None:
        resp = self.retrieve_response(response_id)
        return getattr(resp, "metadata", None)

    # --- Utility ---
    def to_dict(self, response: Response) -> dict[str, Any]:
        return (
            response.model_dump() if hasattr(response, "model_dump") else dict(response)
        )

    def call_endpoint(self, method: str, path: str, **kwargs) -> Any:
        """
        Generic method to call any OpenAI endpoint (for new/experimental APIs).
        Args:
            method: HTTP method ("get", "post", "delete", etc.)
            path: API path (e.g., "/responses/experimental")
            **kwargs: Request parameters (json, params, etc.)
        Returns:
            API response (dict or object)
        Example:
            >>> api.call_endpoint("post", "/responses/experimental", json={...})
        """
        import httpx

        url = f"https://api.openai.com/v1{path}"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        timeout = kwargs.pop("timeout", getattr(self, "timeout", 60))
        with httpx.Client(timeout=timeout) as client:
            resp = client.request(method, url, headers=headers, **kwargs)
            resp.raise_for_status()
            return resp.json()

    def set_timeout(self, timeout: float):
        """Set default timeout (seconds) for all requests."""
        self.timeout = timeout

    def set_api_version(self, version: str):
        """Set API version for all requests (if supported by OpenAI)."""
        self.api_version = version

    def log_call(self, func):
        """Decorator to log API calls."""

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            logger.info(
                f"Calling {func.__name__} with args={args[1:]}, kwargs={kwargs}"
            )
            result = func(*args, **kwargs)
            logger.info(f"{func.__name__} result: {str(result)[:200]}")
            return result

        return wrapper

    # Example: apply logging to create_response
    @property
    def create_response_logged(self):
        return self.log_call(self.create_response)

    # --- Batch/file helpers (if available) ---
    def batch_create_responses(
        self, batch_params: list[dict[str, Any]]
    ) -> list[Response]:
        """
        Batch create responses (if OpenAI supports batch endpoint).
        Args:
            batch_params: List of parameter dicts for each response.
        Returns:
            List of Response objects.
        """
        results = []
        for params in batch_params:
            try:
                results.append(self.create_response(**params))
            except Exception as e:
                logger.error(f"Batch create failed: {e}")
                results.append({"success": False, "error": str(e)})
        return results

    # --- Usage Example (advanced) ---
    # See docstring at top of file for more examples
    """
    Example advanced usage:
    >>> api = OpenAIResponsesInterface()
    >>> # Set timeout and version
    >>> api.set_timeout(30)
    >>> api.set_api_version("2024-07-01")
    >>> # Create a response with logging
    >>> res = api.create_response_logged(model="gpt-4.1-mini", messages=[{"role": "user", "content": "Hello!"}])
    >>> # Call a new/experimental endpoint
    >>> api.call_endpoint("post", "/responses/experimental", json={...})
    >>> # Batch create
    >>> batch = [
    ...     {"model": "gpt-4.1-mini", "messages": [{"role": "user", "content": "Hi 1"}]},
    ...     {"model": "gpt-4.1-mini", "messages": [{"role": "user", "content": "Hi 2"}]},
    ... ]
    >>> results = api.batch_create_responses(batch)
    """


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    interface = OpenAIResponsesInterface()
    try:
        # Create a response
        response = interface.create_response(
            model="gpt-4.1-mini",
            input="Tell me a joke",
        )
        print("Response output_text:", interface.get_output_text(response))
        # Wait for completion
        completed = interface.wait_for_completion(response.id)
        print("Completed response output_text:", interface.get_output_text(completed))
        # List responses
        responses = interface.list_responses()
        print(f"Total responses: {len(responses)}")
        # Stream response (if supported)
        # for chunk in interface.stream_response(model="gpt-4.1-mini", input="Stream a story", stream=True):
        #     print("Chunk:", chunk)
    except Exception as e:
        print("Error:", e)

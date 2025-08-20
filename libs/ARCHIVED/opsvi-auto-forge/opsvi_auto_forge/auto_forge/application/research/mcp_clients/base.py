"""Base class for MCP clients."""

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Any, Awaitable, Optional

from ..errors import ClientError
from ..models import ClientConfig, SearchResult, SourceType

logger = logging.getLogger(__name__)


class BaseMCPClient(ABC):
    """Base class for all MCP clients."""

    def __init__(self, config: ClientConfig):
        self.config = config
        self.name = config.name
        self.timeout = config.timeout
        self.max_results = config.max_results
        self.api_key = config.api_key

    async def __aenter__(self) -> "BaseMCPClient":
        """Async context manager entry."""
        return self

    async def __aexit__(
        self,
        exc_type: Optional[type],
        exc_val: Optional[BaseException],
        exc_tb: Optional[Any],
    ) -> None:
        """Async context manager exit."""

    @abstractmethod
    async def search(self, query: str, **kwargs: Any) -> list[SearchResult]:
        """Search using this client."""

    def _create_search_result(
        self,
        url: str,
        title: str,
        snippet: str,
        content: str | None = None,
        score: float = 0.0,
        metadata: dict[str, Any] | None = None,
    ) -> SearchResult:
        """Create a SearchResult with proper source type."""
        return SearchResult(
            source=self._get_source_type(),
            url=url,
            title=title,
            snippet=snippet,
            content=content,
            score=score,
            metadata=metadata or {},
        )

    @abstractmethod
    def _get_source_type(self) -> SourceType:
        """Get the source type for this client."""

    async def _execute_with_timeout(
        self, coro: Awaitable[Any], timeout: Optional[float] = None
    ) -> Any:
        """Execute a coroutine with timeout."""
        timeout = timeout or self.timeout
        try:
            return await asyncio.wait_for(coro, timeout=timeout)
        except TimeoutError:
            raise ClientError(
                f"Request to {self.name} timed out after {timeout}s",
                self.name,
                {"timeout": timeout},
            )
        except Exception as e:
            raise ClientError(
                f"Request to {self.name} failed: {e}",
                self.name,
                {"original_error": str(e)},
            )

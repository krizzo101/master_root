"""
BraveSearchTool
===============

Asynchronous façade around the Brave MCP Search client used by ResearchAgent
to perform web searches.

Key Features
------------
1.  Lazy dependency import – avoids heavy MCP dependency tree unless needed.
2.  Production-grade logging & error handling.
3.  Minimal, typed public interface.

Exceptions
----------
BraveSearchUnavailableError
    Raised when the Brave MCP client cannot be imported **or** a runtime
    failure occurs while performing a search (network issues, auth errors,
    server not running, …).
"""

from __future__ import annotations

import logging
from typing import List, NamedTuple

logger = logging.getLogger(__name__)


class BraveSearchUnavailableError(RuntimeError):
    """Raised when the Brave search infrastructure is not available."""


class BraveSearchResult(NamedTuple):
    """Typed container for a single Brave search result."""

    url: str
    title: str
    snippet: str
    rank: int


class BraveSearchTool:  # pylint: disable=too-few-public-methods
    """
    Thin asynchronous façade around the `BraveMCPSearch` reference client.

    Example
    -------
    >>> from capabilities.tools.brave_search_tool import BraveSearchTool
    >>> results = await BraveSearchTool().search("python asyncio tutorial")
    >>> print(results[0].url)
    """

    _DEFAULT_RESULT_COUNT = 5

    def __init__(self) -> None:
        self._logger = logging.getLogger(self.__class__.__name__)
        # Lazy import so that unit-tests (which typically mock this class) do
        # not require the heavy MCP dependency tree.
        try:
            from shared.mcp.brave_mcp_search import BraveMCPSearch  # noqa: WPS433

            self._client_cls = BraveMCPSearch
        except ModuleNotFoundError as exc:  # pragma: no cover
            raise BraveSearchUnavailableError(
                "`shared.mcp.brave_mcp_search` is missing – "
                "ensure the MCP client dependencies are installed."
            ) from exc

    def search(
        self, query: str, count: int | None = None
    ) -> List[BraveSearchResult]:
        """
        Perform an asynchronous Brave web search.

        Parameters
        ----------
        query:
            Free-form search query.
        count:
            Maximum number of results (defaults to 5).

        Returns
        -------
        list[BraveSearchResult]
            Normalised search results (never `None`).

        Raises
        ------
        BraveSearchUnavailableError
            If the underlying Brave client or server is unavailable.
        """
        count = count or self._DEFAULT_RESULT_COUNT
        self._logger.debug("BraveSearchTool.search(query=%s, count=%s)", query, count)

        try:
            searcher = self._client_cls()  # type: ignore[call-arg]
            loop = asyncio.get_event_loop()
            if loop.is_running():
                raw_result = loop.run_until_complete(searcher.search(query, count=count))  # pyright: ignore
            else:
                raw_result = asyncio.run(searcher.search(query, count=count))  # pyright: ignore
        except Exception as exc:  # noqa: BLE001
            self._logger.exception("Brave search failed: %s", exc)
            raise BraveSearchUnavailableError(str(exc)) from exc

        # Normalise results.
        results = [
            BraveSearchResult(
                url=item.url,
                title=item.title,
                snippet=item.snippet,
                rank=index + 1,
            )
            for index, item in enumerate(raw_result.results)
        ]
        self._logger.debug("Brave search returned %s results", len(results))
        return results


# --------------------------------------------------------------------------- #
# Stand-alone test driver
# --------------------------------------------------------------------------- #
if __name__ == "__main__":  # pragma: no cover
    import asyncio
    import json
    import sys

    async def _main() -> None:  # noqa: WPS430
        query = " ".join(sys.argv[1:]) or "OpenAI latest API changes"
        results = await BraveSearchTool().search(query)
        print(json.dumps([r._asdict() for r in results], indent=2))

    asyncio.run(_main())

"""
FirecrawlTool
=============

Thin asynchronous façade around the *Firecrawl* MCP client used by
ResearchAgent to scrape rich-text / markdown from arbitrary URLs.

Extracted reference patterns
----------------------------
• Lazy dependency import – avoids pulling the heavy MCP stack unless the tool
  is actually used.
• Runtime capability probe – raises a dedicated exception when the Firecrawl
  client or server is not reachable.
• Strong typing with `NamedTuple` results for ergonomic downstream handling.

This module purposefully keeps the public surface minimal – **one** method,
`scrape`, that returns a `FirecrawlResult`.
"""

from __future__ import annotations

import logging
from typing import NamedTuple

logger = logging.getLogger(__name__)


class FirecrawlUnavailableError(RuntimeError):
    """Raised when the Firecrawl infrastructure is not available."""


class FirecrawlResult(NamedTuple):
    """
    Normalised Firecrawl scraping result.

    Attributes
    ----------
    url : str
        The URL that was scraped.
    content_md : str
        Markdown content returned by Firecrawl (full page).
    """

    url: str
    content_md: str


class FirecrawlTool:  # pylint: disable=too-few-public-methods
    """
    Minimal wrapper around the `FirecrawlMCPClient`.

    Example
    -------
    >>> from capabilities.tools.firecrawl_tool import FirecrawlTool
    >>> content = await FirecrawlTool().scrape("https://openai.com")
    >>> print(content.content_md[:200])
    """

    def __init__(self) -> None:
        self._logger = logging.getLogger(self.__class__.__name__)
        try:
            # Heavy dependency – imported lazily to speed up unit tests.
            from shared.mcp.firecrawl_mcp_client import (
                FirecrawlMCPClient,
            )  # noqa: WPS433

            self._client_cls = FirecrawlMCPClient
        except ModuleNotFoundError as exc:  # pragma: no cover
            raise FirecrawlUnavailableError(
                "`shared.mcp.firecrawl_mcp_client` is missing – "
                "install MCP client requirements."
            ) from exc

    # --------------------------------------------------------------------- #
    # Public API                                                            #
    # --------------------------------------------------------------------- #

    def scrape(self, url: str) -> FirecrawlResult:
        """
        Scrape a single URL asynchronously.

        Parameters
        ----------
        url:
            The target URL.

        Returns
        -------
        FirecrawlResult
            A normalised object containing the markdown content.

        Raises
        ------
        FirecrawlUnavailableError
            If the underlying client or server is down / missing.
        """
        self._logger.debug("FirecrawlTool.scrape(url=%s)", url)

        try:
            client = self._client_cls()  # type: ignore[call-arg]
            loop = asyncio.get_event_loop()
            if loop.is_running():
                raw = loop.run_until_complete(client.scrape(url))  # pyright: ignore[reportUnknownMemberType]
            else:
                raw = asyncio.run(client.scrape(url))  # pyright: ignore[reportUnknownMemberType]
        except Exception as exc:  # noqa: BLE001
            self._logger.exception("Firecrawl scrape failed: %s", exc)
            raise FirecrawlUnavailableError(str(exc)) from exc

        # `raw.content` is a TextContent in the reference implementation.
        return FirecrawlResult(url=url, content_md=raw.content.markdown)


# --------------------------------------------------------------------------- #
# Stand-alone quick-check (invoked via `python -m capabilities.tools.firecrawl_tool URL`)
# --------------------------------------------------------------------------- #
if __name__ == "__main__":  # pragma: no cover
    import asyncio
    import json
    import sys

    async def _main() -> None:  # noqa: WPS430
        _url = sys.argv[1] if len(sys.argv) > 1 else "https://openai.com"
        result = await FirecrawlTool().scrape(_url)
        print(json.dumps(result._asdict(), indent=2))

    asyncio.run(_main())

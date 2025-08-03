"""
ArxivTool
=========

Thin asynchronous façade around either

* the internal `shared.mcp.arxiv_mcp_client.ArxivMCPClient`
  (preferred – mirrors the reference implementation), **or**
* the public `arxiv` PyPI client (automatic fallback).

Patterns extracted from reference code
--------------------------------------
1. _Lazy dependency import_ – heavy, optional dependencies are only imported
   when the tool is actually used (see Brave / Firecrawl tools).
2. _Uniform result object_ `ArxivPaperResult` (`NamedTuple`) for painless
   downstream handling (same idea as `BraveSearchResult`, `FirecrawlResult`).
3. _Async facade over sync client_ – uses `asyncio.to_thread(...)` so callers
   can integrate it into existing async pipelines without blocking the loop.

The public surface is intentionally minimal – a single coroutine
`search(query, max_results=5)` that returns a *list* of `ArxivPaperResult`.
"""

from __future__ import annotations

import asyncio
import logging
from typing import List, NamedTuple, Optional

logger = logging.getLogger(__name__)


class ArxivUnavailableError(RuntimeError):
    """Raised when neither the MCP client nor the PyPI `arxiv` client is available."""


class ArxivPaperResult(NamedTuple):
    """
    Normalised ArXiv search result.

    Attributes
    ----------
    paper_id : str
        ArXiv identifier, e.g. "2101.12345".
    title : str
        Paper title.
    abstract : str
        LaTeX-free abstract (still may contain math).
    pdf_url : str
        Direct link to the PDF.
    content : Optional[str]
        Downloaded paper content (if available).
    """

    paper_id: str
    title: str
    abstract: str
    pdf_url: str
    content: Optional[str] = None


class ArxivTool:  # pylint: disable=too-few-public-methods
    """Async ArXiv search helper."""

    _DEFAULT_MAX_RESULTS = 5

    def __init__(self) -> None:
        self._logger = logging.getLogger(self.__class__.__name__)
        self._client_variant = None  # "mcp" | "pypi"

        # Try internal MCP client first (preferred for prod)
        try:
            from shared.mcp.arxiv_mcp_client import ArxivMCPClient  # noqa: WPS433

            self._client_variant = "mcp"
            self._client_cls = ArxivMCPClient
        except ModuleNotFoundError:
            # Fallback to public PyPI `arxiv` package
            try:
                import arxiv  # noqa: WPS433  pylint: disable=unused-import

                self._client_variant = "pypi"
                self._client_cls = None  # type: ignore[assignment]
            except ModuleNotFoundError as exc:  # pragma: no cover
                raise ArxivUnavailableError(
                    "Neither `shared.mcp.arxiv_mcp_client` nor `arxiv` package found.",
                ) from exc

    # ------------------------------------------------------------------ #
    # Public API                                                         #
    # ------------------------------------------------------------------ #

    async def search(
        self,
        query: str,
        max_results: int | None = None,
        download_papers: bool = True,
    ) -> List[ArxivPaperResult]:
        """
        Search ArXiv asynchronously.

        Parameters
        ----------
        query:
            Free-text query string.
        max_results:
            Max number of results (defaults to ``_DEFAULT_MAX_RESULTS``).
        download_papers:
            Whether to download the actual paper content (defaults to True).

        Returns
        -------
        list[ArxivPaperResult]
        """
        max_results = max_results or self._DEFAULT_MAX_RESULTS
        self._logger.debug(
            "Arxiv search query=%s, k=%s, download=%s",
            query,
            max_results,
            download_papers,
        )

        if self._client_variant == "mcp":
            results = await self._search_via_mcp(query, max_results)
        else:
            # Fallback – run blocking PyPI client in thread
            results = await asyncio.to_thread(self._search_via_pypi, query, max_results)

        # Download paper content if requested
        if download_papers:
            results = await self._download_papers_content(results)

        return results

    async def download_paper_content(self, paper: ArxivPaperResult) -> ArxivPaperResult:
        """
        Download the content of a single paper.

        Parameters
        ----------
        paper:
            ArxivPaperResult with pdf_url.

        Returns
        -------
        ArxivPaperResult
            Updated result with content field populated.
        """
        try:
            # Try using research_papers MCP tool first
            content = await self._download_via_mcp_research_papers(paper.paper_id)
            if content:
                return paper._replace(content=content)
        except Exception as e:
            self._logger.debug(f"MCP research_papers download failed: {e}")

        try:
            # Fallback to direct PDF download
            content = await self._download_pdf_content(paper.pdf_url)
            return paper._replace(content=content)
        except Exception as e:
            self._logger.warning(f"PDF download failed for {paper.paper_id}: {e}")
            return paper

    # ------------------------------------------------------------------ #
    # Internal helpers                                                   #
    # ------------------------------------------------------------------ #

    async def _search_via_mcp(self, query: str, k: int) -> List[ArxivPaperResult]:
        client = self._client_cls()  # type: ignore[operator]
        raw_results = await client.search(
            query=query, max_results=k
        )  # pyright: ignore[reportUnknownMemberType]
        return [
            ArxivPaperResult(
                paper_id=paper.paper_id,
                title=paper.title,
                abstract=paper.abstract,
                pdf_url=paper.pdf_url,
            )
            for paper in raw_results
        ]

    @staticmethod
    def _search_via_pypi(query: str, k: int) -> List[ArxivPaperResult]:  # noqa: WPS110
        import arxiv  # lazy import already confirmed

        search = arxiv.Search(query=query, max_results=k)
        results: list[ArxivPaperResult] = []
        for paper in search.results():
            results.append(
                ArxivPaperResult(
                    paper_id=paper.get_short_id(),
                    title=paper.title,
                    abstract=paper.summary,
                    pdf_url=paper.pdf_url,
                ),
            )
        return results

    async def _download_papers_content(
        self, papers: List[ArxivPaperResult]
    ) -> List[ArxivPaperResult]:
        """Download content for all papers in parallel."""
        tasks = [self.download_paper_content(paper) for paper in papers]
        return await asyncio.gather(*tasks, return_exceptions=True)

    async def _download_via_mcp_research_papers(self, paper_id: str) -> Optional[str]:
        """Download paper content using MCP research_papers tool."""
        try:
            # Use the MCP research_papers tool if available
            from mcp_research_papers import download_paper

            # Download the paper
            result = await download_paper(paper_id=paper_id)

            # Read the paper content
            if result and hasattr(result, "content"):
                return result.content
            elif result and hasattr(result, "text"):
                return result.text
            else:
                return str(result) if result else None

        except ImportError:
            self._logger.debug("MCP research_papers tool not available")
            return None
        except Exception as e:
            self._logger.debug(f"MCP research_papers download failed: {e}")
            return None

    async def _download_pdf_content(self, pdf_url: str) -> Optional[str]:
        """Download PDF content directly."""
        try:
            import httpx

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(pdf_url)
                response.raise_for_status()

                # For now, return a placeholder since PDF parsing is complex
                # In a full implementation, you'd use a PDF parser like PyPDF2 or pdfplumber
                content_length = len(response.content)
                return f"[PDF Content - {content_length} bytes] Download successful. Use PDF parser for text extraction."

        except Exception as e:
            self._logger.warning(f"PDF download failed: {e}")
            return None


# --------------------------------------------------------------------------- #
# CLI quick-test: python -m capabilities.tools.arxiv_tool "machine learning"  #
# --------------------------------------------------------------------------- #
if __name__ == "__main__":  # pragma: no cover
    import asyncio
    import json
    import sys

    async def _main() -> None:  # noqa: WPS430
        _q = sys.argv[1] if len(sys.argv) > 1 else "large language models"
        res = await ArxivTool().search(_q, 3, download_papers=True)
        print(json.dumps([r._asdict() for r in res], indent=2))

    asyncio.run(_main())

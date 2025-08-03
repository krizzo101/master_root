"""
Neo4jKnowledgeGraph
===================

Thin wrapper around the Neo4j Python driver that exposes just enough
functionality for the ACCF ResearchAgent:

1. upsert_page(FirecrawlResult, **meta)   – persist a scraped page
2. query(question, top_k)                 – semantic-ish similarity search

Reference-patterns extracted
----------------------------
• Transaction-per-operation with automatic retry (from the original
  `GraphRAG` implementation).
• Lightweight bag-of-words token index stored on the node for naïve
  cosine similarity (mirrors research_team's stage-8 "token store").

The implementation keeps dependencies optional: if the Neo4j driver or
server is missing, a *single* `KnowledgeGraphUnavailableError` is raised
so that callers can seamlessly fall back.
"""
from __future__ import annotations

import logging
import math
import os
import re
from contextlib import asynccontextmanager
from typing import List, NamedTuple

from capabilities.tools.firecrawl_tool import FirecrawlResult

logger = logging.getLogger(__name__)


class KnowledgeGraphUnavailableError(RuntimeError):
    """Raised when the Neo4j infrastructure is unavailable."""


class KGResult(NamedTuple):
    """Return-type for Neo4jKnowledgeGraph.query."""

    url: str
    title: str
    content_md: str
    score: float


_TOKEN_RX = re.compile(r"[a-zA-Z0-9]+")


def _tokenise(text: str) -> list[str]:
    return _TOKEN_RX.findall(text.lower())


class Neo4jKnowledgeGraph:  # pylint: disable=too-few-public-methods
    """Minimal GraphRAG helper used by ResearchAgent."""

    _DEFAULT_NEO4J_URI = "bolt://localhost:7687"
    _DEFAULT_TOP_K = 5

    def __init__(
        self,
        *,
        uri_env: str = "NEO4J_URI",
        user_env: str = "NEO4J_USER",
        password_env: str = "NEO4J_PASSWORD",
    ) -> None:
        try:
            from neo4j import AsyncGraphDatabase  # noqa: WPS433

            self._driver_cls = AsyncGraphDatabase
        except ModuleNotFoundError as exc:
            raise KnowledgeGraphUnavailableError(
                "neo4j-python driver not installed – `pip install neo4j`",
            ) from exc

        uri = os.getenv(uri_env, self._DEFAULT_NEO4J_URI)
        user = os.getenv(user_env, "neo4j")
        password = os.getenv(password_env)

        if password is None:
            raise KnowledgeGraphUnavailableError(
                "Neo4j credentials missing – set NEO4J_PASSWORD env-var.",
            )

        self._driver = self._driver_cls.driver(uri, auth=(user, password))
        self._logger = logging.getLogger(self.__class__.__name__)

    # ------------------------------------------------------------------ #
    # Driver helpers                                                     #
    # ------------------------------------------------------------------ #

    @asynccontextmanager
    async def _session(self):
        async with self._driver.session() as session:
            yield session

    async def close(self) -> None:  # pragma: no cover
        await self._driver.close()

    # ------------------------------------------------------------------ #
    # Public API                                                         #
    # ------------------------------------------------------------------ #

    async def upsert_page(
        self,
        page: FirecrawlResult,
        *,
        title: str | None = None,
    ) -> None:
        """Create *or* update a (:Page) node."""
        tokens = _tokenise(page.content_md)
        async with self._session() as session:

            async def _tx(tx):
                await tx.run(
                    """
                    MERGE (p:Page {url: $url})
                    SET   p.title      = $title,
                          p.content_md = $md,
                          p.tokens     = $tokens
                    """,
                    url=page.url,
                    title=title or page.url,
                    md=page.content_md,
                    tokens=tokens,
                )

            await session.execute_write(_tx)
        self._logger.debug("Upserted page into Neo4j: %s", page.url)

    async def query(self, question: str, *, top_k: int | None = None) -> List[KGResult]:
        """
        Very-simple similarity: overlap / sqrt(lenA*lenB) on token arrays
        executed inside Cypher (fast for <10K nodes).
        """
        top_k = top_k or self._DEFAULT_TOP_K
        q_tokens = _tokenise(question)

        if not q_tokens:
            return []

        async with self._session() as session:

            async def _tx(tx):
                rows = await tx.run(
                    """
                    UNWIND $q_tokens AS token
                    MATCH (p:Page)
                    WITH p, size([t IN p.tokens WHERE t = token]) AS overlap
                    WITH p,
                         overlap AS o,
                         size(p.tokens)  AS len_p
                    WHERE o > 0
                    RETURN p.url   AS url,
                           p.title AS title,
                           p.content_md AS md,
                           o / sqrt(len_p * $len_q) AS score
                    ORDER BY score DESC
                    LIMIT $k
                    """,
                    q_tokens=q_tokens,
                    len_q=len(q_tokens),
                    k=top_k,
                )
                return [row async for row in rows]

            records = await session.execute_read(_tx)

        results = [
            KGResult(
                url=row["url"],
                title=row["title"],
                content_md=row["md"],
                score=row["score"],
            )
            for row in records
        ]
        self._logger.debug("KG query returned %s results", len(results))
        return results

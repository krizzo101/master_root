"""Research orchestrator for coordinating multiple MCP clients."""

import asyncio
import logging
import time

from .config import get_research_config
from .errors import OrchestrationError
from .mcp_clients import (
    ArxivClient,
    BraveClient,
    Context7Client,
    FirecrawlClient,
    SequentialThinkingClient,
)
from .models import (
    ClientConfig,
    QueryTransform,
    RankedResult,
    RankingScore,
    ResearchConfig,
    ResearchSummary,
    SearchResult,
)

logger = logging.getLogger(__name__)


class ResearchOrchestrator:
    """Orchestrates research across multiple MCP clients."""

    def __init__(self, config: ResearchConfig | None = None):
        self.config = config or get_research_config()
        self._client_factory = {
            "brave": BraveClient,
            "firecrawl": FirecrawlClient,
            "arxiv": ArxivClient,
            "context7": Context7Client,
            "sequential_thinking": SequentialThinkingClient,
        }

    async def execute_research(
        self,
        query: str,
        k: int = 10,
        enable_synthesis: bool | None = None,
        **kwargs,
    ) -> ResearchSummary:
        """Execute comprehensive research across all enabled clients."""
        start_time = time.time()

        # Transform query if needed
        transformed_query = await self._rewrite_query(query)

        # Get enabled clients
        enabled_clients = [
            (name, config)
            for name, config in self.config.clients.items()
            if config.enabled
        ]

        if not enabled_clients:
            raise OrchestrationError("No clients are enabled for research")

        # Execute parallel search across all clients
        all_results = await self._parallel_search(
            transformed_query, enabled_clients, **kwargs
        )

        # Score and rank results
        ranked_results = await self._score_results(
            all_results, transformed_query.transformed
        )

        # Take top-k results
        top_results = ranked_results[:k]

        # Generate synthesis if enabled
        synthesis = ""
        if enable_synthesis is None:
            enable_synthesis = self.config.enable_synthesis

        if enable_synthesis and top_results:
            synthesis = await self._generate_synthesis(
                top_results, transformed_query.transformed
            )

        execution_time = time.time() - start_time

        # Count successful and failed sources
        successful_sources = len(set(r.source for r in all_results))
        failed_sources = len(enabled_clients) - successful_sources

        return ResearchSummary(
            query=transformed_query.transformed,
            top_results=top_results,
            synthesis=synthesis,
            total_sources=len(enabled_clients),
            successful_sources=successful_sources,
            failed_sources=failed_sources,
            execution_time=execution_time,
            metadata={
                "original_query": query,
                "transformation_confidence": transformed_query.confidence,
                "transformation_reasoning": transformed_query.reasoning,
            },
        )

    async def _parallel_search(
        self,
        query_transform: QueryTransform,
        enabled_clients: list[tuple],
        **kwargs,
    ) -> list[SearchResult]:
        """Execute search in parallel across all enabled clients."""
        query = query_transform.transformed

        async def _search_client(
            client_name: str, client_config: ClientConfig
        ) -> list[SearchResult]:
            """Search using a single client."""
            try:
                client_class = self._client_factory.get(client_name)
                if not client_class:
                    logger.warning(f"Unknown client: {client_name}")
                    return []

                async with client_class(client_config) as client:
                    results = await client.search(query, **kwargs)
                    logger.info(f"Client {client_name} returned {len(results)} results")
                    return results

            except Exception as e:
                logger.error(f"Client {client_name} failed: {e}")
                return []

        # Execute all searches in parallel
        tasks = [
            _search_client(client_name, client_config)
            for client_name, client_config in enabled_clients
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Flatten results and handle exceptions
        all_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(
                    f"Client {enabled_clients[i][0]} failed with exception: {result}"
                )
                continue
            all_results.extend(result)

        logger.info(f"Total results from all clients: {len(all_results)}")
        return all_results

    async def _rewrite_query(self, query: str) -> QueryTransform:
        """Rewrite query using heuristics and optional SequentialThinking."""
        # Simple heuristics for query transformation
        original = query
        transformed = query

        # Basic transformations
        if len(query) < 10:
            # Expand short queries
            transformed = f"comprehensive information about {query}"
            confidence = 0.7
            reasoning = "Expanded short query for better search coverage"
        elif "how to" in query.lower():
            # Optimize for tutorials
            transformed = f"{query} tutorial guide examples"
            confidence = 0.8
            reasoning = "Enhanced tutorial-focused query"
        elif "api" in query.lower() or "documentation" in query.lower():
            # Optimize for technical docs
            transformed = f"{query} API reference documentation"
            confidence = 0.9
            reasoning = "Enhanced technical documentation query"
        else:
            confidence = 1.0
            reasoning = "Query kept as-is"

        return QueryTransform(
            original=original,
            transformed=transformed,
            confidence=confidence,
            reasoning=reasoning,
        )

    async def _score_results(
        self, results: list[SearchResult], query: str
    ) -> list[RankedResult]:
        """Score and rank search results."""
        if not results:
            return []

        # Calculate relevance scores
        scored_results = []
        for result in results:
            relevance_score = await self._calculate_relevance(result, query)
            ranking_factors = await self._calculate_ranking_factors(result, query)

            ranked_result = RankedResult(
                source=result.source,
                url=result.url,
                title=result.title,
                snippet=result.snippet,
                content=result.content,
                score=result.score,
                metadata=result.metadata,
                timestamp=result.timestamp,
                relevance=RankingScore(relevance_score),
                ranking_factors=ranking_factors,
            )
            scored_results.append(ranked_result)

        # Sort by relevance score (descending)
        scored_results.sort(key=lambda x: x.relevance, reverse=True)

        return scored_results

    async def _calculate_relevance(self, result: SearchResult, query: str) -> float:
        """Calculate relevance score for a result."""
        base_score = result.score

        # Source type weighting
        source_weights = {
            "paper": 1.2,  # Research papers get higher weight
            "docs": 1.1,  # Technical docs get higher weight
            "think": 1.0,  # Thinking results get standard weight
            "web": 0.9,  # Web results get slightly lower weight
            "scrape": 0.8,  # Scraped content gets lower weight
        }

        source_weight = source_weights.get(result.source.value, 1.0)

        # Content length bonus
        content_bonus = 0.0
        if result.content:
            content_length = len(result.content)
            if content_length > 1000:
                content_bonus = 0.1
            elif content_length > 500:
                content_bonus = 0.05

        # Query term matching bonus
        query_terms = query.lower().split()
        title_terms = result.title.lower().split()
        snippet_terms = result.snippet.lower().split()

        title_matches = sum(1 for term in query_terms if term in title_terms)
        snippet_matches = sum(1 for term in query_terms if term in snippet_terms)

        term_bonus = (title_matches * 0.1) + (snippet_matches * 0.05)

        # Calculate final relevance score
        relevance = (base_score * source_weight) + content_bonus + term_bonus

        # Ensure score is between 0 and 1
        return max(0.0, min(1.0, relevance))

    async def _calculate_ranking_factors(
        self, result: SearchResult, query: str
    ) -> dict[str, float]:
        """Calculate individual ranking factors for transparency."""
        factors = {
            "base_score": result.score,
            "source_weight": 1.0,
            "content_length": len(result.content) if result.content else 0,
            "title_relevance": 0.0,
            "snippet_relevance": 0.0,
        }

        # Source type weight
        source_weights = {
            "paper": 1.2,
            "docs": 1.1,
            "think": 1.0,
            "web": 0.9,
            "scrape": 0.8,
        }
        factors["source_weight"] = source_weights.get(result.source.value, 1.0)

        # Query term matching
        query_terms = query.lower().split()
        title_terms = result.title.lower().split()
        snippet_terms = result.snippet.lower().split()

        factors["title_relevance"] = sum(
            1 for term in query_terms if term in title_terms
        ) / len(query_terms)
        factors["snippet_relevance"] = sum(
            1 for term in query_terms if term in snippet_terms
        ) / len(query_terms)

        return factors

    async def _generate_synthesis(self, results: list[RankedResult], query: str) -> str:
        """Generate synthesis using SequentialThinking client."""
        try:
            # Get SequentialThinking client
            thinking_config = self.config.clients.get("sequential_thinking")
            if not thinking_config or not thinking_config.enabled:
                return f"Analysis of {len(results)} results for query: {query}"

            async with SequentialThinkingClient(thinking_config) as client:
                synthesis = await client.synthesize(results, query)
                return synthesis

        except Exception as e:
            logger.error(f"Synthesis generation failed: {e}")
            return f"Analysis of {len(results)} results for query: {query}"

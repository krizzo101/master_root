"""
Research Service for Code Generation

Thin wrapper around ResearchAgent + SynthesisAgent to provide
up-to-date technical insights for AI prompt enrichment.
"""

import asyncio
import logging
from typing import Optional

from cachetools import TTLCache

logger = logging.getLogger(__name__)


class ResearchService:
    """
    Service for fetching and caching research insights from multiple MCP sources.

    Uses TTL cache to avoid duplicate MCP calls for the same topic.
    """

    # Cache: topic -> insights (7 days TTL)
    _cache: TTLCache[str, str] = TTLCache(maxsize=128, ttl=604800)

    @classmethod
    async def get_insights(cls, topic: str, max_urls: int = 5) -> str:
        """
        Get research insights for a given topic.

        Args:
            topic: The research topic/query
            max_urls: Maximum URLs to scrape (passed to agents)

        Returns:
            Synthesized research insights as string, or empty string on failure
        """
        # Check cache first
        if topic in cls._cache:
            logger.info(f"Research cache hit for topic: {topic[:50]}...")
            return cls._cache[topic]

        logger.info(f"Fetching fresh research insights for: {topic[:50]}...")

        try:
            # Import MCP agents (may fail if research_team not available)
            from applications.research_team.agents.research_agent import (
                ResearchAgent,
            )
            from applications.research_team.agents.synthesis_agent import (
                SynthesisAgent,
            )

            # Gather raw research from all MCP sources
            research_agent = ResearchAgent()
            raw_results = await research_agent.gather(topic)

            logger.info(
                f"Raw results keys: {list(raw_results.keys()) if raw_results else 'None'}"
            )
            logger.info(
                f"Raw results check: {bool(raw_results)} and {any(raw_results.values()) if raw_results else False}"
            )

            if not raw_results or not any(raw_results.values()):
                logger.warning(f"No research results found for topic: {topic}")
                cls._cache[topic] = ""
                return ""

            # Synthesize and standardize results
            synthesis_agent = SynthesisAgent()
            synthesis = await synthesis_agent.synthesize_and_store(raw_results)

            logger.info(
                f"Synthesis result keys: {list(synthesis.keys()) if synthesis else 'None'}"
            )
            logger.info(
                f"Synthesis summary length: {len(synthesis.get('summary', '')) if synthesis else 0}"
            )

            # Extract summary and truncate if needed
            insights = synthesis.get("summary", "")
            if isinstance(insights, str) and len(insights) > 2000:
                insights = insights[:2000] + "... [truncated]"

            # Cache and return
            cls._cache[topic] = insights
            logger.info(
                f"Research insights cached for topic: {topic[:50]}... ({len(insights)} chars)"
            )
            return insights

        except ImportError as e:
            logger.warning(f"Research agents not available: {e}")
            logger.info(
                "Research service will use fallback mode - no external research data"
            )
            cls._cache[topic] = ""
            return ""
        except Exception as e:
            logger.error(f"Research failed for topic '{topic}': {e}")
            logger.info(
                "Research service will use fallback mode - no external research data"
            )
            cls._cache[topic] = ""
            return ""

    @classmethod
    def clear_cache(cls) -> None:
        """Clear the research cache (useful for testing)."""
        cls._cache.clear()
        logger.info("Research cache cleared")

    @classmethod
    def cache_info(cls) -> dict:
        """Get cache statistics."""
        return {
            "current_size": len(cls._cache),
            "max_size": cls._cache.maxsize,
            "ttl": cls._cache.ttl,
        }

    @classmethod
    async def test_connectivity(cls) -> dict:
        """Test research service connectivity and return status."""
        try:
            # Add src directory to Python path for imports
            import sys
            import os

            src_path = os.path.join(os.path.dirname(__file__), "..", "..")
            if src_path not in sys.path:
                sys.path.insert(0, src_path)

            # Test imports
            from applications.research_team.agents.research_agent import ResearchAgent
            from applications.research_team.agents.synthesis_agent import SynthesisAgent

            # Test basic functionality
            research_agent = ResearchAgent()
            synthesis_agent = SynthesisAgent()

            return {
                "status": "available",
                "research_agent": "loaded",
                "synthesis_agent": "loaded",
                "tools_count": len(research_agent.tools),
                "message": "Research service is fully operational",
            }

        except ImportError as e:
            return {
                "status": "unavailable",
                "error": str(e),
                "message": "Research agents cannot be imported - check Python path and dependencies",
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "message": f"Research service test failed: {e}",
            }

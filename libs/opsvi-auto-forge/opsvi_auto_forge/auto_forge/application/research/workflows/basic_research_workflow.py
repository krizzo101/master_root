"""Basic research workflow for simple queries."""

import logging

from ..errors import OrchestrationError
from ..models import RankedResult, ResearchSummary
from ..workflow_tool import ResearchWorkflowTool

logger = logging.getLogger(__name__)


class BasicResearchWorkflow:
    """Basic research workflow for simple, single-query research tasks."""

    def __init__(self, config=None):
        self.workflow_tool = ResearchWorkflowTool(config)

    async def execute(
        self,
        query: str,
        k: int = 5,
        enable_synthesis: bool = True,
        persist: bool = True,
    ) -> ResearchSummary:
        """Execute basic research workflow."""
        try:
            logger.info(f"Starting basic research workflow for query: {query}")

            # Execute research with basic parameters
            summary = await self.workflow_tool.execute(
                query=query,
                k=k,
                persist=persist,
                enable_synthesis=enable_synthesis,
            )

            logger.info(f"Basic research completed: {len(summary.top_results)} results")
            return summary

        except Exception as e:
            logger.error(f"Basic research workflow failed: {e}")
            raise OrchestrationError(f"Basic research failed: {e}")

    async def quick_search(
        self, query: str, max_results: int = 3
    ) -> list[RankedResult]:
        """Quick search without synthesis for fast results."""
        try:
            summary = await self.execute(
                query=query,
                k=max_results,
                enable_synthesis=False,
                persist=False,
            )
            return summary.top_results

        except Exception as e:
            logger.error(f"Quick search failed: {e}")
            return []

    async def get_summary_only(self, query: str) -> str:
        """Get only the synthesis summary for a query."""
        try:
            summary = await self.execute(
                query=query,
                k=10,
                enable_synthesis=True,
                persist=False,
            )
            return summary.synthesis

        except Exception as e:
            logger.error(f"Summary generation failed: {e}")
            return f"Failed to generate summary for query: {query}"

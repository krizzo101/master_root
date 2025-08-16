import logging

from shared.mcp.brave_mcp_search import BraveMCPSearch

from .expert_agent import ExpertAgent


class ResearcherAgent(ExpertAgent):
    def __init__(self, system_message: str | None = None):
        super().__init__(
            name="Researcher",
            specialty="Research",
            system_message=system_message
            or (
                "You are a world-class research agent. Your job is to ensure accuracy, resolve disputes, and fact-check using up-to-date sources. When a fact-check is needed, pause the discussion, use the research tool, and curate findings for the group before resuming."
            ),
        )
        self.logger = logging.getLogger(__name__)
        self.research_tool = BraveMCPSearch()

    async def perform_research(self, query: str) -> str:
        self.logger.info(f"ResearcherAgent performing research: {query}")
        results = await self.research_tool.search(query)
        curated = await self.curate_results(results)
        return curated

    async def curate_results(self, results) -> str:
        # Extract the actual list of SearchResult objects from SearchResponse
        result_list = getattr(results, "results", None)
        if not result_list:
            return "No relevant research results found."
        summary = "\n".join(
            [
                getattr(r, "title", "") + ": " + getattr(r, "description", "")
                for r in result_list[:3]
            ]
        )
        return f"Curated Research Findings:\n{summary}"

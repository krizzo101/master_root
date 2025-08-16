import logging

from shared.mcp.brave_mcp_search import BraveMCPSearch


class MCPSearchTool:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    async def run(self, parameters: dict) -> dict:
        self.logger.info(f"Running BraveMCPSearch with: {parameters}")
        searcher = BraveMCPSearch()
        result = await searcher.search(parameters["query"], count=5)
        return {
            "results": [r.__dict__ for r in result.results],
            "total_results": result.total_results,
        }

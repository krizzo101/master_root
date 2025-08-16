from shared.mcp.brave_mcp_search import BraveMCPSearch

from ..logging.research_logger import get_logger


class MCPSearchTool:
    def __init__(self):
        self.logger = get_logger(__name__)

    async def run(self, parameters: dict) -> dict:
        self.logger.info(f"Running BraveMCPSearch with: {parameters}")
        searcher = BraveMCPSearch()
        result = await searcher.search(parameters["query"], count=5)
        return {
            "results": [r.__dict__ for r in result.results],
            "total_results": result.total_results,
        }

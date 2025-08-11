import logging

from shared.mcp.firecrawl_mcp_client import FirecrawlMCPClient


class MCPFirecrawlTool:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    async def run(self, parameters: dict) -> dict:
        self.logger.info(f"Running FirecrawlMCPClient with: {parameters}")
        client = FirecrawlMCPClient()
        results = await client.search(parameters["query"], limit=5)
        return {"results": [r.__dict__ for r in results]}

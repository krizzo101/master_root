from shared.mcp.context7_mcp_client import Context7MCPClient

from ..logging.research_logger import get_logger


class MCPContext7Tool:
    def __init__(self):
        self.logger = get_logger(__name__)

    async def run(self, parameters: dict) -> dict:
        self.logger.info(f"Running Context7MCPClient with: {parameters}")
        client = Context7MCPClient()
        result = await client.search_and_get_docs(parameters["query"], tokens=2000)
        return result.__dict__

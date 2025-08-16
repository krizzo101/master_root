import asyncio
import logging

from ..tools.mcp_firecrawl_tool import MCPFirecrawlTool
from ..tools.mcp_search_tool import MCPSearchTool


class ResearchAgent:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.tools = {
            "search": MCPSearchTool(),
            "firecrawl": MCPFirecrawlTool(),
            # "context7": MCPContext7Tool(),
            # "arxiv": MCPArxivTool(),
        }

    async def gather(self, query: str) -> dict:
        self.logger.info(f"Gathering research for: {query}")

        # Transform queries intelligently for each tool
        transformed_queries = await self._transform_queries_for_tools(query)
        self.logger.info(f"Original query: {query}")
        self.logger.info(f"Transformed queries: {transformed_queries}")

        tasks = {
            name: tool.run({"query": transformed_queries[name]})
            for name, tool in self.tools.items()
        }
        results = await asyncio.gather(*tasks.values(), return_exceptions=True)
        output = {}
        for name, result in zip(tasks.keys(), results, strict=False):
            if isinstance(result, Exception):
                self.logger.error(f"{name} tool failed: {result}")
                output[name] = {"error": str(result)}
            else:
                output[name] = result
        return output

    async def _transform_queries_for_tools(self, original_query: str) -> dict:
        """Intelligently transform the original query for each research tool."""
        from shared.openai_interfaces.responses_interface import (
            OpenAIResponsesInterface,
        )

        interface = OpenAIResponsesInterface()

        system_prompt = """You are an intelligent query transformer for research tools. Transform the user's query to be optimal for each specific tool:

1. **search** (Brave Search): Keep the original query - it's good for general web search
2. **firecrawl** (Web Scraping): Keep the original query - it's good for finding relevant URLs

Return a JSON object with the transformed queries for each tool."""

        user_prompt = f"Transform this query for each research tool: '{original_query}'"

        try:
            result = await interface.create_structured_response(
                prompt=user_prompt,
                system_prompt=system_prompt,
                response_format={
                    "type": "json_object",
                    "properties": {
                        "search": {
                            "type": "string",
                            "description": "Query for Brave Search",
                        },
                        "firecrawl": {
                            "type": "string",
                            "description": "Query for Firecrawl",
                        },
                    },
                    "required": ["search", "firecrawl"],
                },
            )

            if result and hasattr(result, "content"):
                import json

                transformed = json.loads(result.content)
                self.logger.info(f"Query transformations: {transformed}")
                return transformed
            else:
                self.logger.warning("Failed to transform queries, using original")
                return {"search": original_query, "firecrawl": original_query}

        except Exception as e:
            self.logger.error(f"Query transformation failed: {e}")
            return {"search": original_query, "firecrawl": original_query}

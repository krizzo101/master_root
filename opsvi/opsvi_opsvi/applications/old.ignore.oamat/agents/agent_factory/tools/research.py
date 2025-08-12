"""
Enhanced Research Tool for OAMAT Agents

This tool provides intelligent research workflows that:
1. Search for information using multiple sources
2. Extract and present URLs to the agent for selection
3. Scrape selected URLs for detailed content
4. Compile research findings into structured reports

This tool is designed to be used by OAMAT agents for conducting thorough research
with agent-guided URL selection for optimal research quality.
"""

import logging
import sys
from pathlib import Path
from typing import Any

# Add src to path if needed
if "src" not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

from pydantic import BaseModel, Field

from src.applications.oamat.utils.mcp_tool_registry import create_mcp_tool_registry
from src.shared.mcp.research_workflow_tool import ResearchWorkflowTool

logger = logging.getLogger(__name__)


class ResearchRequest(BaseModel):
    """Research task input schema"""

    query: str = Field(..., min_length=3, description="Research query or topic")
    research_type: str = Field(
        "general", description="Type of research (academic, market, technical)"
    )
    depth: str = Field(
        "moderate", description="Research depth (basic, moderate, comprehensive)"
    )
    sources: list[str] = Field(default_factory=list, description="Preferred sources")


def create_research_search_tool(registry=None):
    """
    Create a research search tool that searches and presents URLs for agent selection

    Args:
        registry: Optional MCP tool registry

    Returns:
        Function that can be used as an agent tool
    """
    tool_registry = registry or create_mcp_tool_registry()
    research_tool = ResearchWorkflowTool(tool_registry)

    async def research_search(query: str, max_results: int = 8) -> str:
        """
        Search for information and present URLs for agent selection

        Args:
            query: Search query string
            max_results: Maximum number of URLs to return

        Returns:
            Formatted string with URLs for agent selection
        """
        try:
            # Search and extract URLs
            urls = await research_tool.search_and_extract_urls(query, max_results)

            if not urls:
                return f"No relevant URLs found for query: '{query}'"

            # Present URLs for selection
            return research_tool.present_urls_for_selection(
                urls, max_display=max_results
            )

        except Exception as e:
            logger.error(f"Research search failed: {e}")
            return f"Error during research search: {str(e)}"

    return research_search


def create_research_scrape_tool(registry=None):
    """
    Create a research scrape tool that scrapes selected URLs based on agent choice

    Args:
        registry: Optional MCP tool registry

    Returns:
        Function that can be used as an agent tool
    """
    tool_registry = registry or create_mcp_tool_registry()
    research_tool = ResearchWorkflowTool(tool_registry)

    async def research_scrape(
        query: str, selected_urls: list[str], max_results: int = 8
    ) -> str:
        """
        Scrape selected URLs and compile research report

        Args:
            query: Original search query
            selected_urls: List of URLs to scrape
            max_results: Maximum number of URLs that were originally found

        Returns:
            Formatted research report
        """
        try:
            # First, get the URLs again to have the full context
            urls = await research_tool.search_and_extract_urls(query, max_results)

            if not urls:
                return f"No URLs found for query: '{query}'"

            # Convert selected URLs to indices
            selected_indices = []
            for selected_url in selected_urls:
                for i, url_obj in enumerate(urls, 1):
                    if url_obj.url == selected_url:
                        selected_indices.append(i)
                        break

            if not selected_indices:
                return "None of the selected URLs were found in the search results"

            # Scrape selected URLs
            results = await research_tool.scrape_selected_urls(urls, selected_indices)

            # Compile and format report
            report = research_tool.compile_research_report(
                query, urls, selected_indices, results
            )
            return research_tool.format_research_report(report)

        except Exception as e:
            logger.error(f"Research scrape failed: {e}")
            return f"Error during research scraping: {str(e)}"

    return research_scrape


def create_research_complete_tool(registry=None):
    """
    Create a complete research tool that performs the full workflow with auto-selection

    Args:
        registry: Optional MCP tool registry

    Returns:
        Function that can be used as an agent tool
    """
    tool_registry = registry or create_mcp_tool_registry()
    research_tool = ResearchWorkflowTool(tool_registry)

    async def research_complete(
        query: str, max_results: int = 5, auto_select_top: int = 3
    ) -> str:
        """
        Perform complete research workflow with auto-selection of top URLs

        Args:
            query: Search query string
            max_results: Maximum number of URLs to find
            auto_select_top: Number of top URLs to auto-select for scraping

        Returns:
            Formatted research report
        """
        try:
            # Search and extract URLs
            urls = await research_tool.search_and_extract_urls(query, max_results)

            if not urls:
                return f"No relevant URLs found for query: '{query}'"

            # Auto-select top URLs
            selected_indices = list(range(1, min(auto_select_top + 1, len(urls) + 1)))

            # Scrape selected URLs
            results = await research_tool.scrape_selected_urls(urls, selected_indices)

            # Compile and format report
            report = research_tool.compile_research_report(
                query, urls, selected_indices, results
            )

            # Add URL selection information to report
            report_text = research_tool.format_research_report(report)

            # Add available URLs section
            available_urls = research_tool.present_urls_for_selection(
                urls, max_display=max_results
            )

            full_report = f"{available_urls}\n\n---\n\n**AUTO-SELECTED TOP {auto_select_top} URLs FOR SCRAPING:**\n\n{report_text}"

            return full_report

        except Exception as e:
            logger.error(f"Complete research failed: {e}")
            return f"Error during complete research: {str(e)}"

    return research_complete


# Tool registration for OAMAT agent factory
def create_web_research_tool(registry=None):
    """
    Create web research tool for OAMAT agents with URL selection capability

    This is the main function that should be used by the OAMAT agent factory
    to create research tools for agents.

    Args:
        registry: Optional MCP tool registry

    Returns:
        Dictionary of research tools
    """
    return {
        "research_search": create_research_search_tool(registry),
        "research_scrape": create_research_scrape_tool(registry),
        "research_complete": create_research_complete_tool(registry),
    }


# Alternative simplified interface for agents
class AgentResearchTool:
    """
    Simplified research tool interface for OAMAT agents
    """

    def __init__(self, registry=None):
        """Initialize the agent research tool"""
        self.registry = registry or create_mcp_tool_registry()
        self.research_tool = ResearchWorkflowTool(self.registry)

    async def search_and_present_urls(self, query: str, max_results: int = 8) -> str:
        """
        Search for information and present URLs for agent selection

        Returns formatted string with URLs for agent selection
        """
        urls = await self.research_tool.search_and_extract_urls(query, max_results)

        if not urls:
            return f"No relevant URLs found for query: '{query}'"

        return self.research_tool.present_urls_for_selection(
            urls, max_display=max_results
        )

    async def scrape_selected_urls(
        self, query: str, selected_indices: list[int], max_results: int = 8
    ) -> str:
        """
        Scrape selected URLs and compile research report

        Args:
            query: Original search query
            selected_indices: List of 1-based indices of URLs to scrape
            max_results: Maximum number of URLs that were originally found

        Returns:
            Formatted research report
        """
        # Get URLs again to have the full context
        urls = await self.research_tool.search_and_extract_urls(query, max_results)

        if not urls:
            return f"No URLs found for query: '{query}'"

        # Scrape selected URLs
        results = await self.research_tool.scrape_selected_urls(urls, selected_indices)

        # Compile and format report
        report = self.research_tool.compile_research_report(
            query, urls, selected_indices, results
        )
        return self.research_tool.format_research_report(report)

    async def complete_research(
        self, query: str, max_results: int = 5, auto_select_top: int = 3
    ) -> str:
        """
        Perform complete research workflow with auto-selection

        Returns formatted research report with URL selection information
        """
        tools = create_web_research_tool(self.registry)
        return await tools["research_complete"](query, max_results, auto_select_top)


# Usage example for agents
"""
Example usage in an OAMAT agent:

# Option 1: Use the tool functions directly
research_tools = create_web_research_tool()

# Step 1: Search and get URLs for selection
url_presentation = await research_tools["research_search"]("Python web frameworks 2025")
print(url_presentation)

# Step 2: Agent selects URLs (e.g., [1, 3, 5])
selected_urls = ["https://example1.com", "https://example2.com"]
research_report = await research_tools["research_scrape"]("Python web frameworks 2025", selected_urls)
print(research_report)

# Option 2: Use the complete tool with auto-selection
complete_report = await research_tools["research_complete"]("Python web frameworks 2025")
print(complete_report)

# Option 3: Use the simplified AgentResearchTool class
agent_research = AgentResearchTool()

# Search and present URLs
urls = await agent_research.search_and_present_urls("Python web frameworks 2025")
print(urls)

# Scrape selected URLs (by index)
report = await agent_research.scrape_selected_urls("Python web frameworks 2025", [1, 2, 3])
print(report)
"""


# Export all public functions and classes
__all__ = [
    "ResearchWorkflowTool",
    "AgentResearchTool",
    "ResearchRequest",
    "create_research_search_tool",
    "create_research_scrape_tool",
    "create_research_complete_tool",
    "create_web_research_tool",
    # Backward compatibility functions for existing tool registry
    "create_web_search_tool",
    "create_academic_search_tool",
    "create_mcp_research_tools",
    "create_knowledge_search_tool",
]


# =============================================================================
# BACKWARD COMPATIBILITY FUNCTIONS FOR EXISTING TOOL REGISTRY
# =============================================================================


def create_knowledge_search_tool(neo4j_client=None):
    """Create a knowledge search tool for Neo4j knowledge base"""
    from langchain_core.tools import tool

    @tool
    def knowledge_search(
        query: str, knowledge_types: list[str] | None = None, max_results: int = 10
    ) -> dict[str, Any]:
        """
        Searches the Neo4j knowledge base for relevant information.

        Args:
            query: The search query.
            knowledge_types: Optional list of knowledge types to search.
            max_results: The maximum number of results to return.

        Returns:
            A dictionary containing the search results.
        """
        if not neo4j_client:
            raise ValueError("Neo4j client is not configured.")
        return neo4j_client.search_by_text(query, limit=max_results)

    return knowledge_search


def create_web_search_tool(mcp_registry=None):
    """
    Create enhanced web search tool that searches and presents URLs for agent selection.

    This is a two-step research workflow:
    1. Call this tool to get numbered URL options
    2. Use the results to decide which URLs to investigate further

    For automatic scraping, use create_research_complete_tool() instead.
    """
    tool_registry = mcp_registry or create_mcp_tool_registry()
    research_tool = ResearchWorkflowTool(tool_registry)

    from langchain_core.tools import tool

    @tool
    async def web_search(query: str, max_results: int = 8) -> str:
        """
        Enhanced web search that finds and presents URLs for agent selection.

        Returns numbered URL options with relevance scores. To get actual content,
        the agent should parse the URL numbers and use research tools to scrape them.

        Args:
            query: Search query string
            max_results: Maximum number of URLs to present

        Returns:
            Formatted list of numbered URLs with titles, descriptions, and relevance scores
        """
        try:
            urls = await research_tool.search_and_extract_urls(query, max_results)
            if not urls:
                return f"No URLs found for query: '{query}'"

            return research_tool.present_urls_for_selection(urls, query)

        except Exception as e:
            logger.error(f"Enhanced web search failed: {e}")
            return f"Web search failed: {str(e)}"

    return web_search


def create_academic_search_tool(mcp_registry=None):
    """Create enhanced academic search tool with URL selection capabilities"""
    tool_registry = mcp_registry or create_mcp_tool_registry()

    from langchain_core.tools import tool

    @tool
    async def academic_search(query: str, max_results: int = 5) -> str:
        """
        Enhanced academic search using ArXiv with structured results.

        Searches academic papers and returns formatted results with paper details.

        Args:
            query: Academic search query
            max_results: Maximum number of papers to return

        Returns:
            Formatted academic paper results with titles, authors, abstracts, and URLs
        """
        try:
            result = await tool_registry.execute_tool(
                "arxiv.research",
                "search_papers",
                {"query": query, "max_results": max_results},
            )

            if not result or not result.success or not result.papers:
                return f"No academic papers found for query: '{query}'"

            # Format papers for agent consumption
            formatted_results = [f"Academic papers for: {query}"]
            formatted_results.append(f"Found {len(result.papers)} papers:")
            formatted_results.append("-" * 50)

            for i, paper in enumerate(result.papers, 1):
                formatted_results.append(f"{i}. {paper.title}")
                formatted_results.append(f"   Authors: {', '.join(paper.authors[:3])}")
                if len(paper.authors) > 3:
                    formatted_results.append(f"   (and {len(paper.authors) - 3} more)")
                formatted_results.append(f"   Published: {paper.published}")
                formatted_results.append(f"   ArXiv ID: {paper.paper_id}")
                formatted_results.append(f"   URL: {paper.arxiv_url}")
                formatted_results.append(f"   Abstract: {paper.abstract[:200]}...")
                formatted_results.append("")

            return "\n".join(formatted_results)

        except Exception as e:
            logger.error(f"Academic search failed: {e}")
            return f"Academic search failed: {str(e)}"

    return academic_search


def create_mcp_research_tools(mcp_registry=None):
    """
    Create enhanced MCP research tools that provide intelligent research workflows.

    Returns a list of tools for:
    1. Research search with URL selection
    2. Selective URL scraping
    3. Complete research workflow
    """
    tool_registry = mcp_registry or create_mcp_tool_registry()

    # Create the enhanced research tools
    search_tool = create_research_search_tool(tool_registry)
    scrape_tool = create_research_scrape_tool(tool_registry)
    complete_tool = create_research_complete_tool(tool_registry)

    return [search_tool, scrape_tool, complete_tool]

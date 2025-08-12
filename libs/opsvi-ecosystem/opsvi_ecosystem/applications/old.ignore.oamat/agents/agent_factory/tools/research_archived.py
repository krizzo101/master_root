"""
OAMAT Agent Factory - Research Tools

Research and knowledge gathering tools for LangGraph agents.
Extracted from agent_factory.py for better modularity and maintainability.
"""

from datetime import datetime
import logging
from typing import Any, Dict, List, Optional

from langchain_core.tools import tool
from pydantic import BaseModel, Field

# Import working MCP tools
# DEPRECATED: from src.shared.mcp.arxiv_mcp_client import quick_search as arxiv_quick_search

logger = logging.getLogger("OAMAT.AgentFactory.ResearchTools")


class ResearchRequest(BaseModel):
    """Research task input schema"""

    query: str = Field(..., min_length=3, description="Research query or topic")
    research_type: str = Field(
        "general", description="Type of research (academic, market, technical)"
    )
    depth: str = Field(
        "moderate", description="Research depth (basic, moderate, comprehensive)"
    )
    sources: List[str] = Field(default_factory=list, description="Preferred sources")


def create_knowledge_search_tool(neo4j_client=None):
    """Create a knowledge search tool"""

    @tool
    def knowledge_search(
        query: str, knowledge_types: Optional[List[str]] = None, max_results: int = 10
    ) -> Dict[str, Any]:
        """
        Searches the Neo4j knowledge base for relevant information.

        Args:
            query: The search query.
            knowledge_types: Optional list of knowledge types to search (e.g., "CodeChunk", "Document").
            max_results: The maximum number of results to return.

        Returns:
            A dictionary containing the search results.
        """
        if not neo4j_client:
            raise ValueError("Neo4j client is not configured.")
        # Use the correct search method: search_by_text
        return neo4j_client.search_by_text(query, limit=max_results)

    return knowledge_search


def create_web_search_tool(mcp_registry=None):
    """Create a web search tool that uses MCP tools"""

    @tool
    def web_search(query: str, max_results: int = 5) -> str:
        """
        Searches the web with date-aware queries and returns formatted results using MCP tools.

        Args:
            query: Search query
            max_results: Maximum number of results to return
        """
        if not mcp_registry:
            raise ValueError("MCP registry not available for web search")

        try:
            # Get current date for search context
            current_date = datetime.now()
            current_year = current_date.year

            # Enhance query with date awareness for recent results
            enhanced_query = _enhance_query_with_date_context(query, current_year)

            # Use MCP registry to execute web search
            result = mcp_registry.execute_tool(
                "brave.search",
                "search",
                {"query": enhanced_query, "count": max_results},
            )
            return f"✅ Web search results for '{enhanced_query}' ({current_year}):\n{result}"

        except Exception as e:
            logger.error(f"Web search failed: {e}")
            return f"❌ Web search failed: {e}"

    def _enhance_query_with_date_context(query: str, current_year: int) -> str:
        """Enhance search query with date context for recent results"""

        # Keywords that indicate the user wants current information
        current_keywords = [
            "latest",
            "current",
            "recent",
            "new",
            "modern",
            "updated",
            "best practices",
            "trends",
            "state of the art",
        ]

        # Check if query already contains current keywords
        query_lower = query.lower()
        has_current_keywords = any(
            keyword in query_lower for keyword in current_keywords
        )

        # If query doesn't have current keywords, add them
        if not has_current_keywords:
            # Add current year and "latest" to make results more current
            enhanced_query = f"{query} {current_year} latest"
        else:
            # Add just the current year for context
            enhanced_query = f"{query} {current_year}"

        return enhanced_query

    return web_search


def create_academic_search_tool(mcp_registry=None):
    """Create an academic search tool that uses MCP tools"""

    @tool
    def academic_search(query: str, max_results: int = 5) -> str:
        """
        Searches academic databases and returns formatted results using MCP tools.

        Args:
            query: Academic search query
            max_results: Maximum number of results to return
        """
        if not mcp_registry:
            raise ValueError("MCP registry not available for academic search")

        try:
            # Use MCP registry to execute academic search
            result = mcp_registry.execute_tool(
                "arxiv.research",
                "search_papers",
                {"query": query, "max_results": max_results},
            )
            return (
                result.data
                if hasattr(result, "data") and result.data
                else f"Academic search completed for: {query}"
            )
        except Exception as e:
            logger.error(f"Academic search failed: {e}")
            raise RuntimeError(f"Academic search failed: {str(e)}")

    return academic_search


def create_mcp_research_tools(mcp_registry=None):
    """Create MCP-based research tools that fail if MCP is not available"""

    @tool
    async def mcp_web_search(query: str, count: int = 5) -> str:
        """
        Performs web search using MCP tools.
        Fails if MCP client is not properly configured.

        Args:
            query: Search query
            count: Number of results to return
        """
        from datetime import datetime

        if not mcp_registry:
            raise RuntimeError("MCP registry not available for web search tool.")

        # Enhanced logging for research tool activity
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]

        research_log = f"""
========================================
🔍 RESEARCHER AGENT - WEB SEARCH TOOL
========================================
TIMESTAMP: {timestamp}
TOOL: brave.search (web_search)
QUERY: "{query}"
COUNT: {count}
MCP_REGISTRY_AVAILABLE: {mcp_registry is not None}
========================================
"""
        print(research_log)
        logger.info(
            f"Researcher Agent: Web search initiated for query: '{query}' (count: {count})"
        )

        try:
            # Execute brave web search with proper error handling
            result = await mcp_registry.execute_tool(
                "brave.search", "search", {"query": query, "count": count}
            )

            # Enhanced logging for tool results
            result_log = f"""
========================================
🔍 RESEARCHER AGENT - WEB SEARCH RESULTS
========================================
TIMESTAMP: {datetime.now().strftime("%H:%M:%S.%f")[:-3]}
QUERY: "{query}"
SUCCESS: {result is not None and hasattr(result, 'data') and result.data}
RESULTS_COUNT: {len(result.data.results) if result and hasattr(result, 'data') and result.data and hasattr(result.data, 'results') else 0}
========================================
"""
            print(result_log)

            if not result or not result.data or not result.data.results:
                logger.warning(
                    f"Researcher Agent: No results found for query: '{query}'"
                )
                print(f"🔍 RESEARCHER: ⚠️ No results found for: '{query}'")
                return f"No results found for query: {query}"

            # Format results for LangGraph agent consumption
            formatted_results = []
            formatted_results.append(f"Web search results for: {query}")
            formatted_results.append(f"Found {len(result.data.results)} results:")
            formatted_results.append("-" * 50)

            # Log each result for detailed analysis
            print(
                f"🔍 RESEARCHER: 📊 Processing {len(result.data.results)} search results:"
            )
            for i, search_result in enumerate(result.data.results, 1):
                formatted_results.append(f"{i}. {search_result.title}")
                formatted_results.append(f"   URL: {search_result.url}")
                formatted_results.append(f"   Description: {search_result.description}")
                formatted_results.append("")

                # Log individual result
                print(
                    f"   Result {i}: {search_result.title[:60]}... | {search_result.url}"
                )

            formatted_output = "\n".join(formatted_results)

            # Log final output preview
            output_preview = (
                formatted_output[:300] + "..."
                if len(formatted_output) > 300
                else formatted_output
            )
            print(
                f"🔍 RESEARCHER: ✅ Web search completed, returning {len(formatted_output)} characters"
            )
            logger.info(
                f"Researcher Agent: Web search completed successfully for '{query}', {len(result.data.results)} results found"
            )

            return formatted_output

        except Exception as e:
            error_msg = f"Web search failed for query '{query}': {str(e)}"

            # Enhanced error logging
            error_log = f"""
========================================
🔍 RESEARCHER AGENT - WEB SEARCH ERROR
========================================
TIMESTAMP: {datetime.now().strftime("%H:%M:%S.%f")[:-3]}
QUERY: "{query}"
ERROR: {str(e)}
ERROR_TYPE: {type(e).__name__}
========================================
"""
            print(error_log)
            logger.error(error_msg)
            raise RuntimeError(error_msg)

    @tool
    async def mcp_research_papers(query: str, max_results: int = 5) -> str:
        """
        Searches research papers using MCP tools.
        Fails if MCP client is not properly configured.

        Args:
            query: Research query
            max_results: Maximum number of papers to return
        """
        from datetime import datetime

        if not mcp_registry:
            raise RuntimeError("MCP registry not available for research papers tool.")

        # Enhanced logging for research papers tool activity
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]

        research_log = f"""
========================================
🔍 RESEARCHER AGENT - ARXIV SEARCH TOOL
========================================
TIMESTAMP: {timestamp}
TOOL: arxiv.research (search_papers)
QUERY: "{query}"
MAX_RESULTS: {max_results}
MCP_REGISTRY_AVAILABLE: {mcp_registry is not None}
========================================
"""
        print(research_log)
        logger.info(
            f"Researcher Agent: ArXiv search initiated for query: '{query}' (max_results: {max_results})"
        )

        try:
            # Execute ArXiv search with proper error handling via MCP Registry
            result = await mcp_registry.execute_tool(
                "arxiv.research",  # Tool name in registry
                "search_papers",  # Method name
                {"query": query, "max_results": max_results},
            )

            # Enhanced logging for tool results
            result_log = f"""
========================================
🔍 RESEARCHER AGENT - ARXIV SEARCH RESULTS
========================================
TIMESTAMP: {datetime.now().strftime("%H:%M:%S.%f")[:-3]}
QUERY: "{query}"
SUCCESS: {result is not None and hasattr(result, 'success') and result.success}
PAPERS_COUNT: {len(result.papers) if result and hasattr(result, 'papers') and result.papers else 0}
ERROR_MSG: {result.error if result and hasattr(result, 'error') and result.error else "None"}
========================================
"""
            print(result_log)

            if not result or not result.success:
                error_msg = f"ArXiv search failed for query '{query}'"
                if result and result.error:
                    error_msg += f": {result.error}"
                logger.warning(f"Researcher Agent: {error_msg}")
                print(f"🔍 RESEARCHER: ⚠️ ArXiv search failed for: '{query}'")
                raise RuntimeError(error_msg)

            if not result.papers:
                logger.warning(
                    f"Researcher Agent: No research papers found for query: '{query}'"
                )
                print(f"🔍 RESEARCHER: ⚠️ No papers found for: '{query}'")
                return f"No research papers found for query: {query}"

            # Format results for LangGraph agent consumption
            formatted_results = []
            formatted_results.append(f"Research papers for: {query}")
            formatted_results.append(f"Found {len(result.papers)} papers:")
            formatted_results.append("-" * 50)

            # Log each paper for detailed analysis
            print(f"🔍 RESEARCHER: 📚 Processing {len(result.papers)} research papers:")
            for i, paper in enumerate(result.papers, 1):
                formatted_results.append(f"{i}. {paper.title}")
                formatted_results.append(f"   Authors: {', '.join(paper.authors[:3])}")
                if len(paper.authors) > 3:
                    formatted_results.append(f"   (and {len(paper.authors) - 3} more)")
                formatted_results.append(f"   Published: {paper.published}")
                formatted_results.append(
                    f"   Categories: {', '.join(paper.categories)}"
                )
                formatted_results.append(f"   ArXiv ID: {paper.paper_id}")
                formatted_results.append(f"   URL: {paper.arxiv_url}")
                formatted_results.append(f"   Abstract: {paper.abstract[:200]}...")
                formatted_results.append("")

                # Log individual paper
                print(
                    f"   Paper {i}: {paper.title[:60]}... | {paper.paper_id} | {paper.published}"
                )

            formatted_output = "\n".join(formatted_results)

            # Log final output preview
            print(
                f"🔍 RESEARCHER: ✅ ArXiv search completed, returning {len(formatted_output)} characters"
            )
            logger.info(
                f"Researcher Agent: ArXiv search completed successfully for '{query}', {len(result.papers)} papers found"
            )

            return formatted_output

        except Exception as e:
            error_msg = f"Research papers search failed for query '{query}': {str(e)}"

            # Enhanced error logging
            error_log = f"""
========================================
🔍 RESEARCHER AGENT - ARXIV SEARCH ERROR
========================================
TIMESTAMP: {datetime.now().strftime("%H:%M:%S.%f")[:-3]}
QUERY: "{query}"
ERROR: {str(e)}
ERROR_TYPE: {type(e).__name__}
========================================
"""
            print(error_log)
            logger.error(error_msg)
            raise RuntimeError(error_msg)

    return [mcp_web_search, mcp_research_papers]


# Export all public functions and classes
__all__ = [
    "ResearchRequest",
    "create_knowledge_search_tool",
    "create_web_search_tool",
    "create_academic_search_tool",
    "create_mcp_research_tools",
]

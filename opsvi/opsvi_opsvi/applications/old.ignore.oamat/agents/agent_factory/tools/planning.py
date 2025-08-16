"""
OAMAT Agent Factory - Planning Framework Tools

Tools for accessing current project management methodologies, architectural patterns,
and planning templates to ensure high-quality, current planning output.
"""

from datetime import datetime
import logging

from langchain_core.tools import tool

logger = logging.getLogger("OAMAT.AgentFactory.PlanningTools")


def create_planning_frameworks_tools(mcp_registry=None, base_agent=None):
    """Create planning framework tools that provide current methodologies and patterns"""

    @tool
    def get_current_architectural_patterns() -> str:
        """
        Dynamically retrieves current architectural patterns and best practices for web applications.

        Returns:
            String containing current architectural patterns and recommendations
        """
        logger.info("Dynamically retrieving current architectural patterns...")

        if not mcp_registry:
            return "❌ MCP registry not available for dynamic architectural pattern research"

        try:
            # Get current date for search context
            current_date = datetime.now()
            current_year = current_date.year

            # Generate dynamic search queries for different architectural aspects
            search_queries = [
                f"modern web application architecture {current_year} best practices",
                f"React Next.js latest version {current_year} stack",
                f"full stack development architecture {current_year} patterns",
                f"microservices architecture {current_year} best practices",
            ]

            # Use web search to find current architectural patterns
            web_search_tool = mcp_registry.get_tool("brave.search")
            if not web_search_tool:
                return "❌ Web search tool not available"

            patterns_content = []
            for query in search_queries:
                try:
                    search_results = web_search_tool.search(query, count=3)
                    if search_results and search_results.get("web"):
                        for result in search_results["web"][
                            :2
                        ]:  # Top 2 results per query
                            if result.get("url") and result.get("description"):
                                patterns_content.append(
                                    f"Pattern: {query}\nSource: {result['url']}\nInsight: {result['description']}"
                                )
                except Exception as e:
                    logger.warning(f"Search failed for query '{query}': {e}")
                    continue

            if not patterns_content:
                return "❌ No current architectural patterns found"

            return (
                f"✅ Current architectural patterns ({current_year}):\n"
                + "\n\n---\n\n".join(patterns_content)
            )

        except Exception as e:
            logger.error(f"Error retrieving architectural patterns: {e}")
            return f"❌ Error retrieving architectural patterns: {e}"

    @tool
    def get_project_planning_methodologies() -> str:
        """
        Dynamically retrieves current project planning methodologies and frameworks.

        Returns:
            String containing current project planning approaches
        """
        logger.info("Dynamically retrieving current project planning methodologies...")

        if not mcp_registry:
            return "❌ MCP registry not available for dynamic methodology research"

        try:
            # Get current date for search context
            current_date = datetime.now()
            current_year = current_date.year

            # Generate search query for current project planning methodologies
            search_query = (
                f"project planning methodologies {current_year} agile scrum kanban"
            )

            # Use web search to find current planning methodologies
            web_search_tool = mcp_registry.get_tool("brave.search")
            if not web_search_tool:
                return "❌ Web search tool not available"

            # Search for current methodologies
            search_results = web_search_tool.search(search_query, count=3)

            if not search_results or not search_results.get("web"):
                return "❌ No current planning methodologies found"

            # Extract and summarize findings
            methodology_content = []
            for result in search_results["web"]:
                if result.get("url") and result.get("description"):
                    methodology_content.append(
                        f"Source: {result['url']}\nMethodology: {result['description']}"
                    )

            if not methodology_content:
                return "❌ No valid methodology information found"

            return (
                f"✅ Current project planning methodologies ({current_year}):\n"
                + "\n\n---\n\n".join(methodology_content)
            )

        except Exception as e:
            logger.error(f"Error retrieving methodologies: {e}")
            return f"❌ Error retrieving methodologies: {e}"

    @tool
    def get_technology_recommendations(project_type: str = "web_application") -> str:
        """
        Dynamically gets current technology recommendations for specific project types.

        Args:
            project_type: Type of project (web_application, api, mobile, etc.)

        Returns:
            String containing technology recommendations
        """
        logger.info(
            f"Dynamically getting technology recommendations for {project_type}..."
        )

        if not mcp_registry:
            return "❌ MCP registry not available for dynamic technology research"

        try:
            # Get current date for search context
            current_date = datetime.now()
            current_year = current_date.year

            # Generate dynamic search query based on project type
            search_query = _generate_technology_search_query(project_type, current_year)

            # Use web search to find current technology recommendations
            web_search_tool = mcp_registry.get_tool("brave.search")
            if not web_search_tool:
                return "❌ Web search tool not available"

            # Search for current technology recommendations
            search_results = web_search_tool.search(search_query, count=5)

            if not search_results or not search_results.get("web"):
                return (
                    f"❌ No current technology recommendations found for {project_type}"
                )

            # Extract and summarize findings
            recommendations_content = []
            for result in search_results["web"][:3]:
                if result.get("url") and result.get("description"):
                    recommendations_content.append(
                        f"Source: {result['url']}\nRecommendation: {result['description']}"
                    )

            if not recommendations_content:
                return f"❌ No valid technology recommendations found for {project_type}"

            return (
                f"✅ Current technology recommendations for {project_type} ({current_year}):\n"
                + "\n\n---\n\n".join(recommendations_content)
            )

        except Exception as e:
            logger.error(f"Error getting technology recommendations: {e}")
            return f"❌ Error getting technology recommendations: {e}"

    def _generate_technology_search_query(project_type: str, current_year: int) -> str:
        """Generate a dynamic search query for current technology recommendations"""

        # Base query patterns for different project types
        query_patterns = {
            "web_application": f"best web development tech stack {current_year} React Next.js",
            "api": f"best API framework {current_year} REST GraphQL",
            "mobile": f"best mobile development framework {current_year} React Native Flutter",
            "desktop": f"best desktop development framework {current_year} Electron Tauri",
            "ai_application": f"best AI application framework {current_year} OpenAI LangChain",
        }

        base_query = query_patterns.get(project_type, query_patterns["web_application"])

        # Add current technology terms
        current_terms = [
            "latest version",
            "best practices",
            "modern development",
            "popular framework",
        ]

        return f"{base_query} {' '.join(current_terms)}"

    @tool
    def get_quality_gates_framework() -> str:
        """
        Dynamically retrieves current quality gates and validation frameworks.

        Returns:
            String containing quality gates and validation approaches
        """
        logger.info("Dynamically retrieving quality gates framework...")

        if not mcp_registry:
            return "❌ MCP registry not available for dynamic quality gates research"

        try:
            # Get current date for search context
            current_date = datetime.now()
            current_year = current_date.year

            # Generate search query for current quality gates
            search_query = (
                f"software quality gates best practices {current_year} testing linting"
            )

            # Use web search to find current quality gates frameworks
            web_search_tool = mcp_registry.get_tool("brave.search")
            if not web_search_tool:
                return "❌ Web search tool not available"

            # Search for current quality gates
            search_results = web_search_tool.search(search_query, count=3)

            if not search_results or not search_results.get("web"):
                return "❌ No current quality gates frameworks found"

            # Extract and summarize findings
            quality_content = []
            for result in search_results["web"]:
                if result.get("url") and result.get("description"):
                    quality_content.append(
                        f"Source: {result['url']}\nFramework: {result['description']}"
                    )

            if not quality_content:
                return "❌ No valid quality gates information found"

            return (
                f"✅ Current quality gates framework ({current_year}):\n"
                + "\n\n---\n\n".join(quality_content)
            )

        except Exception as e:
            logger.error(f"Error retrieving quality gates: {e}")
            return f"❌ Error retrieving quality gates: {e}"

    @tool
    def generate_project_roadmap(
        project_description: str, timeline: str = "3_months"
    ) -> str:
        """
        Dynamically generates a project roadmap based on current best practices.

        Args:
            project_description: Description of the project
            timeline: Timeline for the project (3_months, 6_months, 1_year)

        Returns:
            String containing a structured project roadmap
        """
        logger.info(
            f"Dynamically generating project roadmap for: {project_description}"
        )

        if not mcp_registry:
            return "❌ MCP registry not available for dynamic roadmap generation"

        try:
            # Get current date for search context
            current_date = datetime.now()
            current_year = current_date.year

            # Generate search query for current project planning practices
            search_query = f"project roadmap methodology {current_year} {timeline} {project_description}"

            # Use web search to find current roadmap practices
            web_search_tool = mcp_registry.get_tool("brave.search")
            if not web_search_tool:
                return "❌ Web search tool not available"

            # Search for current roadmap practices
            search_results = web_search_tool.search(search_query, count=3)

            if not search_results or not search_results.get("web"):
                return "❌ No current roadmap practices found"

            # Extract and summarize findings
            roadmap_content = []
            for result in search_results["web"]:
                if result.get("url") and result.get("description"):
                    roadmap_content.append(
                        f"Source: {result['url']}\nInsight: {result['description']}"
                    )

            if not roadmap_content:
                return "❌ No valid roadmap information found"

            return (
                f"✅ Dynamic project roadmap for '{project_description}' ({timeline}, {current_year}):\n"
                + "\n\n---\n\n".join(roadmap_content)
            )

        except Exception as e:
            logger.error(f"Error generating roadmap: {e}")
            return f"❌ Error generating roadmap: {e}"

    return [
        get_current_architectural_patterns,
        get_project_planning_methodologies,
        get_technology_recommendations,
        get_quality_gates_framework,
        generate_project_roadmap,
    ]

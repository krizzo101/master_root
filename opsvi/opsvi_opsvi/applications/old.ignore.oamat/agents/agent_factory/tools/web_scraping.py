"""
OAMAT Agent Factory - Web Scraping Tools

Tools for accessing current documentation examples, API patterns, and real-world
implementations to ensure high-quality, current documentation and research output.
"""

from datetime import datetime
import logging

from langchain_core.tools import tool

logger = logging.getLogger("OAMAT.AgentFactory.WebScrapingTools")


def create_web_scraping_tools(mcp_registry=None, base_agent=None):
    """Create web scraping tools for current documentation and implementation examples"""

    @tool
    def scrape_current_documentation(topic: str, source_type: str = "official") -> str:
        """
        Dynamically finds and scrapes current documentation for a given topic using web search.

        Args:
            topic: The topic to scrape documentation for (e.g., "React", "OpenAI API", "Node.js")
            source_type: Type of source to scrape (official, community, examples)

        Returns:
            String containing scraped documentation and examples
        """
        logger.info(f"Dynamically scraping current documentation for: {topic}")

        if not mcp_registry:
            return "❌ MCP registry not available for dynamic web scraping"

        try:
            # Get current date for search context
            current_date = datetime.now()
            current_year = current_date.year

            # Generate dynamic search query based on current date and topic
            search_query = _generate_documentation_search_query(
                topic, source_type, current_year
            )

            # Use web search to find current documentation sources
            web_search_tool = mcp_registry.get_tool("brave.search")
            if not web_search_tool:
                return "❌ Web search tool not available"

            # Search for current documentation sources
            search_results = web_search_tool.search(search_query, count=3)

            if not search_results or not search_results.get("web"):
                return f"❌ No current documentation sources found for {topic}"

            # Extract URLs from search results
            urls_to_scrape = []
            for result in search_results["web"][:3]:  # Limit to top 3 results
                if result.get("url"):
                    urls_to_scrape.append(result["url"])

            if not urls_to_scrape:
                return f"❌ No valid URLs found in search results for {topic}"

            # Use firecrawl to scrape the dynamically found URLs
            firecrawl_client = mcp_registry.get_tool("firecrawl.scraping")
            if not firecrawl_client:
                return "❌ Firecrawl client not available for scraping"

            scraped_content = []
            for url in urls_to_scrape:
                try:
                    logger.info(f"Scraping: {url}")
                    result = firecrawl_client.scrape(url)
                    scraped_content.append(f"Source: {url}\n{result}")
                except Exception as e:
                    logger.warning(f"Failed to scrape {url}: {e}")
                    continue

            if not scraped_content:
                return f"❌ Failed to scrape any content for {topic}"

            return (
                f"✅ Dynamically scraped {source_type} documentation for {topic} ({current_year}):\n"
                + "\n\n---\n\n".join(scraped_content)
            )

        except Exception as e:
            logger.error(f"Error in dynamic documentation scraping: {e}")
            return f"❌ Error in dynamic documentation scraping: {e}"

    def _generate_documentation_search_query(
        topic: str, source_type: str, current_year: int
    ) -> str:
        """Generate a dynamic search query for current documentation"""

        # Base query patterns for different source types
        query_patterns = {
            "official": f"{topic} official documentation {current_year} latest",
            "community": f"{topic} community examples {current_year} github",
            "examples": f"{topic} examples tutorials {current_year} best practices",
        }

        base_query = query_patterns.get(source_type, query_patterns["official"])

        # Add version-specific terms for popular technologies
        version_terms = {
            "react": "latest version hooks",
            "openai": "API v4 latest",
            "nodejs": "latest LTS",
            "typescript": "latest version",
            "nextjs": "latest version app router",
            "vue": "latest version composition api",
            "angular": "latest version standalone components",
        }

        topic_key = topic.lower()
        if topic_key in version_terms:
            base_query += f" {version_terms[topic_key]}"

        return base_query

    @tool
    def get_current_api_patterns(api_type: str = "rest") -> str:
        """
        Dynamically retrieves current API design patterns and best practices using web search.

        Args:
            api_type: Type of API (rest, graphql, websocket, grpc)

        Returns:
            String containing current API patterns and examples
        """
        logger.info(f"Dynamically retrieving current {api_type} API patterns...")

        if not mcp_registry:
            return "❌ MCP registry not available for dynamic API pattern research"

        try:
            # Get current date for search context
            current_date = datetime.now()
            current_year = current_date.year

            # Generate dynamic search query for current API patterns
            search_query = _generate_api_patterns_search_query(api_type, current_year)

            # Use web search to find current API patterns
            web_search_tool = mcp_registry.get_tool("brave.search")
            if not web_search_tool:
                return "❌ Web search tool not available"

            # Search for current API patterns
            search_results = web_search_tool.search(search_query, count=5)

            if not search_results or not search_results.get("web"):
                return f"❌ No current API patterns found for {api_type}"

            # Extract and summarize findings
            patterns_content = []
            for result in search_results["web"][:3]:
                if result.get("url") and result.get("description"):
                    patterns_content.append(
                        f"Source: {result['url']}\nInsight: {result['description']}"
                    )

            if not patterns_content:
                return f"❌ No valid API pattern information found for {api_type}"

            return (
                f"✅ Current {api_type} API patterns ({current_year}):\n"
                + "\n\n---\n\n".join(patterns_content)
            )

        except Exception as e:
            logger.error(f"Error retrieving API patterns: {e}")
            return f"❌ Error retrieving API patterns: {e}"

    def _generate_api_patterns_search_query(api_type: str, current_year: int) -> str:
        """Generate a dynamic search query for current API patterns"""

        # Base query patterns for different API types
        query_patterns = {
            "rest": f"REST API best practices {current_year} design patterns OpenAPI",
            "graphql": f"GraphQL API best practices {current_year} schema design",
            "websocket": f"WebSocket API patterns {current_year} real-time",
            "grpc": f"gRPC API patterns {current_year} best practices",
        }

        base_query = query_patterns.get(api_type, query_patterns["rest"])

        # Add current technology terms
        current_terms = [
            "latest standards",
            "modern authentication",
            "security best practices",
            "performance optimization",
        ]

        return f"{base_query} {' '.join(current_terms)}"

    @tool
    def get_web_development_examples(technology: str = "react") -> str:
        """
        Dynamically retrieves current web development examples and patterns.

        Args:
            technology: The technology to get examples for (react, vue, angular, etc.)

        Returns:
            String containing current web development examples and patterns
        """
        logger.info(
            f"Dynamically retrieving web development examples for: {technology}"
        )

        if not mcp_registry:
            return "❌ MCP registry not available for dynamic web development examples"

        try:
            # Get current date for search context
            current_date = datetime.now()
            current_year = current_date.year

            # Generate search query for current web development examples
            search_query = (
                f"{technology} examples best practices {current_year} tutorial"
            )

            # Use web search to find current examples
            web_search_tool = mcp_registry.get_tool("brave.search")
            if not web_search_tool:
                return "❌ Web search tool not available"

            # Search for current examples
            search_results = web_search_tool.search(search_query, count=3)

            if not search_results or not search_results.get("web"):
                return f"❌ No current web development examples found for {technology}"

            # Extract and summarize findings
            examples_content = []
            for result in search_results["web"]:
                if result.get("url") and result.get("description"):
                    examples_content.append(
                        f"Source: {result['url']}\nExample: {result['description']}"
                    )

            if not examples_content:
                return f"❌ No valid web development examples found for {technology}"

            return (
                f"✅ Current web development examples for {technology} ({current_year}):\n"
                + "\n\n---\n\n".join(examples_content)
            )

        except Exception as e:
            logger.error(f"Error retrieving web development examples: {e}")
            return f"❌ Error retrieving web development examples: {e}"

    @tool
    def scrape_implementation_examples(framework: str, feature: str) -> str:
        """
        Dynamically scrapes real-world implementation examples for specific framework features.

        Args:
            framework: Framework to scrape examples for (react, vue, angular, etc.)
            feature: Specific feature to find examples for

        Returns:
            String containing implementation examples and patterns
        """
        logger.info(
            f"Dynamically scraping implementation examples for {framework} {feature}"
        )

        if not mcp_registry:
            return "❌ MCP registry not available for dynamic implementation examples"

        try:
            # Get current date for search context
            current_date = datetime.now()
            current_year = current_date.year

            # Generate search query for current implementation examples
            search_query = (
                f"{framework} {feature} implementation examples {current_year} github"
            )

            # Use web search to find current examples
            web_search_tool = mcp_registry.get_tool("brave.search")
            if not web_search_tool:
                return "❌ Web search tool not available"

            # Search for current examples
            search_results = web_search_tool.search(search_query, count=3)

            if not search_results or not search_results.get("web"):
                return f"❌ No current implementation examples found for {framework} {feature}"

            # Extract URLs and scrape them
            urls_to_scrape = []
            for result in search_results["web"]:
                if result.get("url") and "github" in result["url"]:
                    urls_to_scrape.append(result["url"])

            if not urls_to_scrape:
                return f"❌ No valid implementation URLs found for {framework} {feature}"

            # Use firecrawl to scrape the dynamically found URLs
            firecrawl_client = mcp_registry.get_tool("firecrawl.scraping")
            if not firecrawl_client:
                return "❌ Firecrawl client not available for scraping"

            scraped_examples = []
            for url in urls_to_scrape[:2]:  # Limit to top 2 URLs
                try:
                    logger.info(f"Scraping implementation example: {url}")
                    result = firecrawl_client.scrape(url)
                    scraped_examples.append(f"Source: {url}\nImplementation: {result}")
                except Exception as e:
                    logger.warning(f"Failed to scrape {url}: {e}")
                    continue

            if not scraped_examples:
                return f"❌ Failed to scrape any implementation examples for {framework} {feature}"

            return (
                f"✅ Dynamic implementation examples for {framework} {feature} ({current_year}):\n"
                + "\n\n---\n\n".join(scraped_examples)
            )

        except Exception as e:
            logger.error(f"Error scraping implementation examples: {e}")
            return f"❌ Error scraping implementation examples: {e}"

    return [
        scrape_current_documentation,
        get_current_api_patterns,
        get_web_development_examples,
        scrape_implementation_examples,
    ]

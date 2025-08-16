"""
Mock Tool Implementations

Mock implementations of MCP tools for testing and development.
Extracted from mcp_tool_registry.py for better modularity.
"""

import asyncio
from typing import Any, Dict, List


class MockBraveSearch:
    """Mock Brave Search interface."""

    async def web_search(self, query: str, **kwargs) -> Dict[str, Any]:
        await asyncio.sleep(0.1)  # Simulate network delay
        return {
            "query": query,
            "results": [
                {
                    "title": "Mock Result 1",
                    "url": "https://example1.com",
                    "snippet": "Mock snippet 1",
                },
                {
                    "title": "Mock Result 2",
                    "url": "https://example2.com",
                    "snippet": "Mock snippet 2",
                },
            ],
            "total": 2,
        }

    async def news_search(self, query: str, **kwargs) -> Dict[str, Any]:
        await asyncio.sleep(0.1)
        return {
            "query": query,
            "news": [{"title": "Mock News", "source": "Mock Source"}],
        }

    def health_check(self) -> Dict[str, Any]:
        return {"status": "healthy", "service": "brave_search"}


class MockArxivResearch:
    """Mock ArXiv Research interface."""

    async def search_papers(self, query: str, **kwargs) -> Dict[str, Any]:
        await asyncio.sleep(0.2)
        return {
            "query": query,
            "papers": [
                {"id": "2301.00001", "title": "Mock Paper 1", "authors": ["Author 1"]},
                {"id": "2301.00002", "title": "Mock Paper 2", "authors": ["Author 2"]},
            ],
        }

    def health_check(self) -> Dict[str, Any]:
        return {"status": "healthy", "service": "arxiv_research"}


class MockFirecrawl:
    """Mock Firecrawl interface."""

    async def scrape(self, url: str, **kwargs) -> Dict[str, Any]:
        await asyncio.sleep(0.3)
        return {"url": url, "content": "Mock scraped content", "success": True}

    def health_check(self) -> Dict[str, Any]:
        return {"status": "healthy", "service": "firecrawl"}


class MockContext7Docs:
    """Mock Context7 Docs interface."""

    async def resolve_library_id(self, library_name: str, **kwargs) -> Dict[str, Any]:
        await asyncio.sleep(0.1)
        return {"library_name": library_name, "library_id": f"/{library_name}/docs"}

    async def get_library_docs(self, library_id: str, **kwargs) -> Dict[str, Any]:
        await asyncio.sleep(0.2)
        return {"library_id": library_id, "docs": "Mock documentation content"}

    def health_check(self) -> Dict[str, Any]:
        return {"status": "healthy", "service": "context7_docs"}


class MockSequentialThinking:
    """Mock Sequential Thinking interface."""

    async def think(self, problem: str, **kwargs) -> Dict[str, Any]:
        await asyncio.sleep(0.5)  # Thinking takes time
        return {
            "problem": problem,
            "thoughts": ["Mock thought 1", "Mock thought 2"],
            "conclusion": "Mock conclusion",
        }

    def health_check(self) -> Dict[str, Any]:
        return {"status": "healthy", "service": "sequential_thinking"}


class MockNeo4j:
    """Mock Neo4j interface."""

    async def get_schema(self, **kwargs) -> Dict[str, Any]:
        await asyncio.sleep(0.1)
        return {"nodes": ["Node1", "Node2"], "relationships": ["REL1", "REL2"]}

    async def read_cypher(self, query: str, **kwargs) -> Dict[str, Any]:
        await asyncio.sleep(0.1)
        return {"query": query, "results": [{"mock": "data"}]}

    def health_check(self) -> Dict[str, Any]:
        return {"status": "healthy", "service": "neo4j"}


class MockResearchWorkflow:
    """Mock Research Workflow interface."""

    async def search_and_present(self, query: str, max_results: int) -> List[Any]:
        await asyncio.sleep(0.4)
        return [
            MockResearchUrl("https://example.com/1", "Example 1", 0.9),
            MockResearchUrl("https://example.com/2", "Example 2", 0.8),
        ]

    async def search_and_extract_urls(self, query: str, max_results: int) -> List[Any]:
        """Extract URLs for agent selection."""
        await asyncio.sleep(0.3)
        return [
            MockResearchUrl("https://example.com/1", "Mock URL 1", 0.9),
            MockResearchUrl("https://example.com/2", "Mock URL 2", 0.8),
        ]

    def present_urls_for_selection(self, urls: List[Any], max_results: int) -> str:
        """Present URLs for agent selection."""
        presentation = "## URLs Found for Selection:\n\n"
        for i, url in enumerate(urls[:max_results], 1):
            presentation += f"{i}. **{url.title}** (Score: {url.relevance_score:.2f})\n"
            presentation += f"   {url.url}\n\n"
        return presentation

    async def scrape_selected_urls(
        self, urls: List[Any], selected_indices: List[int]
    ) -> List[Any]:
        await asyncio.sleep(0.5)
        return [
            MockResearchResult(True, "Scraped content 1"),
            MockResearchResult(False, "Scrape failed 2"),
        ]

    def compile_research_report(
        self,
        query: str,
        urls: List[Any],
        selected_indices: List[int],
        results: List[Any],
    ) -> Dict[str, Any]:
        """Compile research report from scraped results."""
        return {
            "query": query,
            "urls": urls,
            "selected_indices": selected_indices,
            "results": results,
        }

    def format_research_report(self, report: Dict[str, Any]) -> str:
        """Format the research report."""
        return f"# Research Report for: {report['query']}\n\nMock research content..."

    def health_check(self) -> Dict[str, Any]:
        return {"status": "healthy", "service": "research_workflow"}


class MockResearchUrl:
    """Mock Research URL object."""

    def __init__(self, url: str, title: str, relevance_score: float):
        self.url = url
        self.title = title
        self.relevance_score = relevance_score


class MockResearchResult:
    """Mock Research Result object."""

    def __init__(self, success: bool, message: str):
        self.success = success
        self.message = message

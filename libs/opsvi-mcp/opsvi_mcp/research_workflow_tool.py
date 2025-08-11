#!/usr/bin/env python3
"""
Research Workflow Tool for OAMAT

This tool provides intelligent research workflows that:
1. Search for information using multiple sources
2. Extract and present URLs to the agent for selection
3. Scrape selected URLs for detailed content
4. Compile research findings into structured reports

Features:
- Multi-source search (Brave, Firecrawl)
- URL extraction and deduplication
- Agent-guided URL selection
- Intelligent content scraping
- Research report generation
"""

from dataclasses import dataclass
import logging
from pathlib import Path
import re
import sys
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

# Add src to path if needed
if "src" not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Lazy import to avoid circular dependency
# from src.applications.oamat.utils.mcp_tool_registry import (
#     MCPToolRegistry,
#     create_mcp_tool_registry,
# )
from src.shared.mcp.intelligent_relevance_scorer import IntelligentRelevanceScorer

logger = logging.getLogger(__name__)


@dataclass
class SearchResultURL:
    """Structured URL from search results"""

    url: str
    title: str
    description: str
    source: str  # 'brave_search', 'firecrawl_search', etc.
    relevance_score: float = 0.0
    content_preview: str = ""

    def __post_init__(self):
        # Clean up URL
        self.url = self.url.strip()
        if self.url and not self.url.startswith(("http://", "https://")):
            self.url = f"https://{self.url}"

    @property
    def domain(self) -> str:
        """Extract domain from URL"""
        try:
            return urlparse(self.url).netloc
        except:
            return ""

    @property
    def is_valid(self) -> bool:
        """Check if URL is valid"""
        return bool(self.url and self.url.startswith(("http://", "https://")))


@dataclass
class ResearchResult:
    """Result from scraping a selected URL"""

    url: str
    title: str
    content: str
    success: bool
    error_message: str = ""
    content_length: int = 0
    scrape_time: float = 0.0

    def __post_init__(self):
        self.content_length = len(self.content)


@dataclass
class ResearchReport:
    """Compiled research report"""

    query: str
    search_results: List[SearchResultURL]
    selected_urls: List[str]
    scraped_results: List[ResearchResult]
    total_search_time: float = 0.0
    total_scrape_time: float = 0.0
    created_at: str = ""

    def __post_init__(self):
        from datetime import datetime

        if not self.created_at:
            self.created_at = datetime.now().isoformat()


class ResearchWorkflowTool:
    """
    Research workflow tool for intelligent web research
    """

    def __init__(self, registry=None, use_intelligent_scoring: bool = True):
        """Initialize the research workflow tool"""
        self.registry = registry  # Can be None for standalone use
        self.use_intelligent_scoring = use_intelligent_scoring
        self.relevance_scorer = (
            IntelligentRelevanceScorer() if use_intelligent_scoring else None
        )
        self.logger = logging.getLogger(self.__class__.__name__)

        # URL extraction patterns
        self.url_patterns = [
            r'https?://[^\s<>"\[\]{}|\\^`]+',
            r'www\.[^\s<>"\[\]{}|\\^`]+',
        ]

    def _get_or_create_registry(self):
        """Lazily create MCP registry if needed"""
        if self.registry is None:
            try:
                # Lazy import to avoid circular dependency
                from src.applications.oamat.utils.mcp_tool_registry import (
                    create_mcp_tool_registry,
                )

                self.registry = create_mcp_tool_registry()
            except ImportError:
                # For standalone testing, we'll use mock web search
                self.logger.warning(
                    "MCP registry not available, using mock implementation"
                )
                self.registry = None
        return self.registry

    def _mock_search_results(
        self, query: str, max_results: int
    ) -> List[SearchResultURL]:
        """Provide mock search results for demo purposes"""
        # Generate realistic mock results based on the query
        mock_results = [
            SearchResultURL(
                url="https://arxiv.org/abs/2101.00001",
                title="Advanced Machine Learning Optimization Techniques",
                description="A comprehensive study of model optimization strategies for production deployment including quantization, pruning, and knowledge distillation.",
                source="mock_search",
            ),
            SearchResultURL(
                url="https://pytorch.org/docs/stable/optimization.html",
                title="PyTorch Model Optimization Documentation",
                description="Official PyTorch documentation covering optimization techniques, performance tuning, and deployment best practices.",
                source="mock_search",
            ),
            SearchResultURL(
                url="https://tensorflow.org/model_optimization",
                title="TensorFlow Model Optimization Toolkit",
                description="TensorFlow's official guide to model optimization including post-training quantization and pruning techniques.",
                source="mock_search",
            ),
            SearchResultURL(
                url="https://towardsdatascience.com/ml-model-optimization-2023",
                title="Machine Learning Model Optimization for Production (2023)",
                description="Latest techniques for optimizing ML models for production deployment, covering efficiency and performance improvements.",
                source="mock_search",
            ),
            SearchResultURL(
                url="https://mlops.org/model-optimization",
                title="MLOps Guide to Model Optimization",
                description="Best practices for optimizing machine learning models in production environments with real-world case studies.",
                source="mock_search",
            ),
            SearchResultURL(
                url="https://huggingface.co/docs/transformers/optimization",
                title="Transformer Model Optimization - Hugging Face",
                description="Guide to optimizing transformer models for inference including ONNX export, quantization, and hardware acceleration.",
                source="mock_search",
            ),
            SearchResultURL(
                url="https://github.com/microsoft/DeepSpeed",
                title="DeepSpeed: Extreme-scale model training and optimization",
                description="Microsoft's DeepSpeed library for training and optimizing large-scale models with memory and computation efficiency.",
                source="mock_search",
            ),
            SearchResultURL(
                url="https://blog.paperspace.com/model-optimization-techniques/",
                title="A Comprehensive Guide to Model Optimization Techniques",
                description="In-depth guide covering various model optimization techniques including pruning, quantization, and knowledge distillation.",
                source="mock_search",
            ),
        ]

        # Filter based on query relevance and limit results
        relevant_results = mock_results[:max_results]

        self.logger.info(
            f"Generated {len(relevant_results)} mock search results for query: {query}"
        )
        return relevant_results

    def _format_urls_for_agent(
        self, urls: List[SearchResultURL], max_display: int = 10
    ) -> str:
        """Format URLs for agent consumption with scores and metadata"""
        if not urls:
            return "No URLs found from search results."

        output = []
        scoring_method = (
            "🧠 Intelligent LLM Analysis"
            if self.use_intelligent_scoring
            else "🔤 Keyword Matching"
        )
        output.append(
            f"🔍 **Available URLs for Research Selection** (Ranked by {scoring_method}):"
        )
        output.append("")

        display_urls = urls[:max_display]

        for i, url_obj in enumerate(display_urls, 1):
            output.append(f"**[{i}]** {url_obj.title}")
            output.append(f"   📍 URL: {url_obj.url}")
            output.append(f"   🏷️  Source: {url_obj.source}")
            output.append(f"   📊 Relevance: {url_obj.relevance_score:.1f}")

            if url_obj.description:
                desc_preview = (
                    url_obj.description[:150] + "..."
                    if len(url_obj.description) > 150
                    else url_obj.description
                )
                output.append(f"   📝 Description: {desc_preview}")

            if url_obj.content_preview:
                output.append(f"   👁️  Preview: {url_obj.content_preview}")

            output.append("")

        if len(urls) > max_display:
            output.append(f"... and {len(urls) - max_display} more URLs available")

        output.append(
            "**Instructions:** Please select the URLs you want to scrape by providing their numbers (e.g., 1, 3, 5) or select 'all' for all URLs."
        )

        return "\n".join(output)

    def extract_urls_from_text(
        self, text: str, source: str = "unknown"
    ) -> List[SearchResultURL]:
        """Extract URLs from plain text search results"""
        urls = []

        # Find all URLs in the text
        found_urls = set()
        for pattern in self.url_patterns:
            matches = re.findall(pattern, text)
            found_urls.update(matches)

        # Process each found URL
        for url in found_urls:
            # Clean up URL
            url = url.strip(".,;:!?)\"'")

            # Extract title and description from surrounding text
            title = self._extract_title_for_url(text, url)
            description = self._extract_description_for_url(text, url)

            if url and len(url) > 10:  # Basic validation
                urls.append(
                    SearchResultURL(
                        url=url,
                        title=title or self._generate_title_from_url(url),
                        description=description,
                        source=source,
                    )
                )

        return urls

    def _extract_title_for_url(self, text: str, url: str) -> str:
        """Extract title for a URL from surrounding text"""
        # Look for "Title: some title" pattern before the URL
        title_pattern = r"Title:\s*([^\n\r]+?)(?=\s*(?:URL:|https?://|$))"
        matches = re.findall(title_pattern, text)

        if matches:
            return matches[0].strip()

        # Fallback: look for text before URL
        url_pos = text.find(url)
        if url_pos > 0:
            before_url = text[:url_pos].strip()
            # Get last line before URL
            lines = before_url.split("\n")
            if lines:
                last_line = lines[-1].strip()
                if last_line and not last_line.startswith(("http", "URL:")):
                    return last_line[:100]  # Limit length

        return ""

    def _extract_description_for_url(self, text: str, url: str) -> str:
        """Extract description for a URL from surrounding text"""
        url_pos = text.find(url)
        if url_pos >= 0:
            # Look for text after URL
            after_url = text[url_pos + len(url) :].strip()
            # Get first paragraph after URL
            paragraphs = after_url.split("\n\n")
            if paragraphs:
                first_para = paragraphs[0].strip()
                # Remove URL patterns from description
                for pattern in self.url_patterns:
                    first_para = re.sub(pattern, "", first_para)
                if first_para:
                    return first_para[:300]  # Limit length

        return ""

    def _generate_title_from_url(self, url: str) -> str:
        """Generate a title from URL"""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc
            path = parsed.path

            # Try to extract meaningful title from path
            if path and path != "/":
                path_parts = path.strip("/").split("/")
                if path_parts:
                    # Use last part of path as title
                    last_part = path_parts[-1]
                    if last_part:
                        # Convert dashes/underscores to spaces and title case
                        title = last_part.replace("-", " ").replace("_", " ").title()
                        return f"{title} - {domain}"

            return domain
        except:
            return url[:50] + "..." if len(url) > 50 else url

    async def search_and_extract_urls(
        self, query: str, max_results: int = 10
    ) -> List[SearchResultURL]:
        """
        Search for information and extract URLs from results

        Args:
            query: Search query string
            max_results: Maximum number of URLs to return

        Returns:
            List of SearchResultURL objects
        """
        all_urls = []

        # Get or create registry
        registry = self._get_or_create_registry()

        if registry is None:
            # Use mock data for demo when MCP registry is not available
            return self._mock_search_results(query, max_results)

        # Search with Brave Search
        try:
            brave_result = registry.execute_tool(
                "brave.search",
                "search",
                {"query": query, "count": min(max_results, 10)},
            )

            if brave_result.success and brave_result.data:
                if hasattr(brave_result.data, "results"):
                    # Structured results
                    for result in brave_result.data.results:
                        if hasattr(result, "url") and result.url:
                            all_urls.append(
                                SearchResultURL(
                                    url=result.url,
                                    title=(
                                        result.title if hasattr(result, "title") else ""
                                    ),
                                    description=(
                                        result.description
                                        if hasattr(result, "description")
                                        else ""
                                    ),
                                    source="brave_search",
                                )
                            )
                        elif hasattr(result, "description"):
                            # Extract URLs from description
                            extracted_urls = self.extract_urls_from_text(
                                result.description, "brave_search"
                            )
                            all_urls.extend(extracted_urls)
                else:
                    # Plain text results - extract URLs
                    result_text = str(brave_result.data)
                    extracted_urls = self.extract_urls_from_text(
                        result_text, "brave_search"
                    )
                    all_urls.extend(extracted_urls)

        except Exception as e:
            self.logger.error(f"Brave search failed: {e}")

        # Search with Firecrawl
        try:
            firecrawl_result = self.registry.execute_tool(
                "firecrawl.scraping",
                "search",
                {"query": query, "limit": min(max_results, 5)},
            )

            if firecrawl_result.success and firecrawl_result.data:
                for result in firecrawl_result.data:
                    if hasattr(result, "url") and result.url:
                        all_urls.append(
                            SearchResultURL(
                                url=result.url,
                                title=result.url,  # Firecrawl may not have titles
                                description="",
                                source="firecrawl_search",
                                content_preview=(
                                    result.content[:200]
                                    if hasattr(result, "content")
                                    else ""
                                ),
                            )
                        )

        except Exception as e:
            self.logger.error(f"Firecrawl search failed: {e}")

        # Deduplicate URLs
        seen_urls = set()
        unique_urls = []

        for url_obj in all_urls:
            if url_obj.is_valid and url_obj.url not in seen_urls:
                seen_urls.add(url_obj.url)
                unique_urls.append(url_obj)

        # Sort by relevance using intelligent LLM-based scoring
        for url_obj in unique_urls:
            url_obj.relevance_score = await self._calculate_relevance_score(
                url_obj, query, context={"research_type": "web_search"}
            )

        unique_urls.sort(key=lambda x: x.relevance_score, reverse=True)

        return unique_urls[:max_results]

    async def _calculate_relevance_score(
        self,
        url_obj: SearchResultURL,
        query: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> float:
        """Calculate relevance score for a URL using intelligent LLM analysis"""

        if self.use_intelligent_scoring and self.relevance_scorer:
            try:
                # Use intelligent LLM-based scoring
                evaluation = self.relevance_scorer.evaluate_relevance(
                    query=query,
                    url=url_obj.url,
                    title=url_obj.title,
                    description=url_obj.description,
                    context=context,
                )

                self.logger.info(
                    f"Intelligent relevance score for {url_obj.url[:50]}...: {evaluation.score:.2f}"
                )
                self.logger.debug(f"Reasoning: {evaluation.reasoning[:100]}...")

                return evaluation.score

            except Exception as e:
                self.logger.warning(
                    f"Intelligent scoring failed for {url_obj.url}, falling back to basic scoring: {e}"
                )
                # Fall through to basic scoring

        # Basic keyword-based scoring (fallback)
        score = 0.0
        query_lower = query.lower()

        # Title matching
        if url_obj.title:
            title_lower = url_obj.title.lower()
            if query_lower in title_lower:
                score += 2.0
            else:
                # Partial word matching
                query_words = query_lower.split()
                for word in query_words:
                    if word in title_lower:
                        score += 0.5

        # Description matching
        if url_obj.description:
            desc_lower = url_obj.description.lower()
            if query_lower in desc_lower:
                score += 1.0
            else:
                query_words = query_lower.split()
                for word in query_words:
                    if word in desc_lower:
                        score += 0.3

        # Domain scoring (prefer common domains)
        domain_scores = {
            "github.com": 0.5,
            "stackoverflow.com": 0.5,
            "docs.python.org": 0.5,
            "medium.com": 0.3,
            "dev.to": 0.3,
        }

        for domain, bonus in domain_scores.items():
            if domain in url_obj.domain:
                score += bonus

        return score

    def present_urls_for_selection(
        self, urls: List[SearchResultURL], max_display: int = 10
    ) -> str:
        """
        Present URLs to the agent for selection

        Args:
            urls: List of SearchResultURL objects
            max_display: Maximum number of URLs to display

        Returns:
            Formatted string for agent consumption
        """
        if not urls:
            return "No URLs found from search results."

        output = []
        scoring_method = (
            "🧠 Intelligent LLM Analysis"
            if self.use_intelligent_scoring
            else "🔤 Keyword Matching"
        )
        output.append(
            f"🔍 **Available URLs for Research Selection** (Ranked by {scoring_method}):"
        )
        output.append("")

        display_urls = urls[:max_display]

        for i, url_obj in enumerate(display_urls, 1):
            output.append(f"**[{i}]** {url_obj.title}")
            output.append(f"   📍 URL: {url_obj.url}")
            output.append(f"   🏷️  Source: {url_obj.source}")
            output.append(f"   📊 Relevance: {url_obj.relevance_score:.1f}")

            if url_obj.description:
                desc_preview = (
                    url_obj.description[:150] + "..."
                    if len(url_obj.description) > 150
                    else url_obj.description
                )
                output.append(f"   📝 Description: {desc_preview}")

            if url_obj.content_preview:
                output.append(f"   👁️  Preview: {url_obj.content_preview}")

            output.append("")

        if len(urls) > max_display:
            output.append(f"... and {len(urls) - max_display} more URLs available")

        output.append(
            "**Instructions:** Please select the URLs you want to scrape by providing their numbers (e.g., 1, 3, 5) or select 'all' for all URLs."
        )

        return "\n".join(output)

    async def search_and_present_urls(
        self, query: str, max_results: int = 10, use_intelligent_scoring: bool = None
    ) -> Dict[str, Any]:
        """
        Search for URLs and present them with scores for agent selection

        Args:
            query: Search query string
            max_results: Maximum number of URLs to return
            use_intelligent_scoring: Override intelligent scoring setting

        Returns:
            Dict containing search results, scoring method, and formatted agent prompt
        """
        # Temporarily override scoring setting if specified
        original_scoring = self.use_intelligent_scoring
        if use_intelligent_scoring is not None:
            self.use_intelligent_scoring = use_intelligent_scoring

        try:
            # Search and extract URLs with automatic scoring
            urls = await self.search_and_extract_urls(query, max_results)

            # Format for agent presentation
            agent_prompt = self._format_urls_for_agent(urls, max_display=max_results)

            # Prepare result data
            search_results = []
            for url_obj in urls:
                result_data = {
                    "url": url_obj.url,
                    "title": url_obj.title,
                    "description": url_obj.description,
                    "relevance_score": url_obj.relevance_score,
                    "source": url_obj.source,
                }

                # Add reasoning if available (from intelligent scoring)
                if hasattr(url_obj, "reasoning"):
                    result_data["reasoning"] = url_obj.reasoning
                elif (
                    self.use_intelligent_scoring
                    and hasattr(self, "relevance_scorer")
                    and self.relevance_scorer
                ):
                    # Try to get reasoning from the last evaluation
                    try:
                        evaluation = self.relevance_scorer.evaluate_relevance(
                            query=query,
                            url=url_obj.url,
                            title=url_obj.title,
                            description=url_obj.description,
                        )
                        result_data["reasoning"] = evaluation.reasoning
                    except:
                        result_data[
                            "reasoning"
                        ] = "Scored using intelligent LLM analysis"
                else:
                    result_data["reasoning"] = "Scored using keyword matching"

                search_results.append(result_data)

            scoring_method = (
                "intelligent_llm"
                if self.use_intelligent_scoring
                else "keyword_matching"
            )

            return {
                "search_results": search_results,
                "agent_prompt": agent_prompt,
                "scoring_method": scoring_method,
                "query": query,
                "total_results": len(urls),
            }

        finally:
            # Restore original scoring setting
            self.use_intelligent_scoring = original_scoring

    async def scrape_selected_urls(
        self, urls: List[SearchResultURL], selected_indices: List[int]
    ) -> List[ResearchResult]:
        """
        Scrape the selected URLs for detailed content

        Args:
            urls: List of available URLs
            selected_indices: List of selected indices (1-based)

        Returns:
            List of ResearchResult objects
        """
        results = []

        for index in selected_indices:
            if 1 <= index <= len(urls):
                url_obj = urls[index - 1]

                try:
                    import time

                    start_time = time.time()

                    scrape_result = self.registry.execute_tool(
                        "firecrawl.scraping",
                        "scrape",
                        {
                            "url": url_obj.url,
                            "formats": ["markdown"],
                            "only_main_content": True,
                        },
                    )

                    scrape_time = time.time() - start_time

                    if scrape_result.success and scrape_result.data:
                        content = (
                            scrape_result.data.content
                            if hasattr(scrape_result.data, "content")
                            else str(scrape_result.data)
                        )

                        results.append(
                            ResearchResult(
                                url=url_obj.url,
                                title=url_obj.title,
                                content=content,
                                success=True,
                                scrape_time=scrape_time,
                            )
                        )
                    else:
                        results.append(
                            ResearchResult(
                                url=url_obj.url,
                                title=url_obj.title,
                                content="",
                                success=False,
                                error_message=scrape_result.error_message
                                or "Unknown error",
                                scrape_time=scrape_time,
                            )
                        )

                except Exception as e:
                    results.append(
                        ResearchResult(
                            url=url_obj.url,
                            title=url_obj.title,
                            content="",
                            success=False,
                            error_message=str(e),
                        )
                    )

        return results

    def compile_research_report(
        self,
        query: str,
        urls: List[SearchResultURL],
        selected_indices: List[int],
        results: List[ResearchResult],
    ) -> ResearchReport:
        """
        Compile a research report from the results

        Args:
            query: Original search query
            urls: All found URLs
            selected_indices: Selected URL indices
            results: Scraping results

        Returns:
            ResearchReport object
        """
        selected_urls = [
            urls[i - 1].url for i in selected_indices if 1 <= i <= len(urls)
        ]

        return ResearchReport(
            query=query,
            search_results=urls,
            selected_urls=selected_urls,
            scraped_results=results,
            total_scrape_time=sum(r.scrape_time for r in results),
        )

    def format_research_report(self, report: ResearchReport) -> str:
        """
        Format research report for presentation

        Args:
            report: ResearchReport object

        Returns:
            Formatted report string
        """
        output = []
        output.append("📊 **Research Report**")
        output.append("=" * 50)
        output.append(f"**Query:** {report.query}")
        output.append(f"**Generated:** {report.created_at}")
        output.append(f"**URLs Found:** {len(report.search_results)}")
        output.append(f"**URLs Scraped:** {len(report.selected_urls)}")
        output.append(f"**Scraping Time:** {report.total_scrape_time:.2f}s")
        output.append("")

        # Successful results
        successful_results = [r for r in report.scraped_results if r.success]
        if successful_results:
            output.append("✅ **Successfully Scraped Content:**")
            output.append("")

            for i, result in enumerate(successful_results, 1):
                output.append(f"**{i}. {result.title}**")
                output.append(f"   📍 URL: {result.url}")
                output.append(
                    f"   📄 Content Length: {result.content_length} characters"
                )
                output.append(f"   ⏱️  Scrape Time: {result.scrape_time:.2f}s")
                output.append("")

                # Content preview
                if result.content:
                    preview = (
                        result.content[:500] + "..."
                        if len(result.content) > 500
                        else result.content
                    )
                    output.append("   📝 **Content Preview:**")
                    output.append(f"   {preview}")
                    output.append("")

        # Failed results
        failed_results = [r for r in report.scraped_results if not r.success]
        if failed_results:
            output.append("❌ **Failed to Scrape:**")
            output.append("")

            for result in failed_results:
                output.append(f"   • {result.url}")
                output.append(f"     Error: {result.error_message}")
                output.append("")

        return "\n".join(output)


# Utility functions for easy integration
async def research_query(query: str, registry=None) -> str:
    """
    Perform a complete research query workflow

    Args:
        query: Search query string
        registry: Optional MCP tool registry

    Returns:
        Formatted research report
    """
    tool = ResearchWorkflowTool(registry)

    # Search and extract URLs
    urls = await tool.search_and_extract_urls(query)

    if not urls:
        return f"No URLs found for query: {query}"

    # Present URLs for selection (auto-select top 3 for demo)
    selected_indices = list(range(1, min(4, len(urls) + 1)))

    # Scrape selected URLs
    results = await tool.scrape_selected_urls(urls, selected_indices)

    # Compile and format report
    report = tool.compile_research_report(query, urls, selected_indices, results)

    return tool.format_research_report(report)


# Command line interface
if __name__ == "__main__":
    import asyncio

    async def main():
        query = "Python web development frameworks 2025"
        report = await research_query(query)
        print(report)

    asyncio.run(main())

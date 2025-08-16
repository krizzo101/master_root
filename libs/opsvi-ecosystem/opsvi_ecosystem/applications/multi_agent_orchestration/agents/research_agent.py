"""
Research agent implementation.

Specializes in information gathering, web search coordination,
data analysis, and knowledge synthesis.
"""

import logging
from typing import Any

from ..common.types import AgentCapability, AgentError, Task
from ..tools.data_processor_tool import DataProcessorTool
from ..tools.web_search_tool import WebSearchTool
from .base_agent import BaseAgent

logger = logging.getLogger(__name__)


class ResearchAgent(BaseAgent):
    """
    Research agent specialized in information gathering and analysis.

    Capabilities:
    - Web search and information retrieval
    - Data analysis and text processing
    - Knowledge synthesis and summarization
    - Research coordination with other agents
    """

    def __init__(
        self,
        agent_id: str = "research_agent",
        name: str = "Research Agent",
        description: str = "Specialized agent for information gathering, web search, and data analysis",
        logger: logging.Logger | None = None,
    ):
        """
        Initialize the research agent.

        Args:
            agent_id: Unique agent identifier
            name: Human-readable agent name
            description: Agent description
            logger: Optional logger instance
        """
        super().__init__(
            agent_id=agent_id,
            name=name,
            description=description,
            logger=logger,
        )

        # Add default tools
        self.add_tool(WebSearchTool())
        self.add_tool(DataProcessorTool())

        # Initialize capabilities
        self._capabilities = [
            AgentCapability(
                name="web_search",
                description="Search the web for information on any topic",
                input_schema={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"},
                        "max_results": {"type": "integer", "default": 5},
                    },
                    "required": ["query"],
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "results": {"type": "array"},
                        "summary": {"type": "string"},
                    },
                },
                tools_required=["web_search"],
            ),
            AgentCapability(
                name="text_analysis",
                description="Analyze text for insights, keywords, and sentiment",
                input_schema={
                    "type": "object",
                    "properties": {
                        "text": {"type": "string"},
                        "include_keywords": {"type": "boolean", "default": True},
                        "include_sentiment": {"type": "boolean", "default": False},
                    },
                    "required": ["text"],
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "analysis": {"type": "object"},
                        "insights": {"type": "array"},
                    },
                },
                tools_required=["data_processor"],
            ),
            AgentCapability(
                name="research_synthesis",
                description="Synthesize research findings from multiple sources",
                input_schema={
                    "type": "object",
                    "properties": {
                        "sources": {"type": "array"},
                        "focus_areas": {"type": "array"},
                    },
                    "required": ["sources"],
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "synthesis": {"type": "string"},
                        "key_findings": {"type": "array"},
                        "recommendations": {"type": "array"},
                    },
                },
                tools_required=["web_search", "data_processor"],
            ),
        ]

        logger.info(
            f"ResearchAgent {self.agent_id} initialized with {len(self._capabilities)} capabilities"
        )

    async def execute_task(self, task: Task) -> dict[str, Any]:
        """
        Execute a research task.

        Args:
            task: Task to execute

        Returns:
            Task execution results

        Raises:
            AgentError: If task execution fails
        """
        try:
            logger.info(f"ResearchAgent executing task: {task.name}")

            # Route to appropriate execution method based on task parameters
            task_type = task.parameters.get("type", "general_research")

            if task_type == "web_search":
                return await self._execute_web_search(task)
            elif task_type == "text_analysis":
                return await self._execute_text_analysis(task)
            elif task_type == "research_synthesis":
                return await self._execute_research_synthesis(task)
            elif task_type == "general_research":
                return await self._execute_general_research(task)
            else:
                raise AgentError(f"Unknown task type: {task_type}")

        except Exception as e:
            logger.error(f"ResearchAgent task execution failed: {e}")
            raise AgentError(f"Research task failed: {str(e)}")

    def get_capabilities(self) -> list[AgentCapability]:
        """
        Get the research agent's capabilities.

        Returns:
            List of agent capabilities
        """
        return self._capabilities.copy()

    async def _execute_web_search(self, task: Task) -> dict[str, Any]:
        """
        Execute a web search task.

        Args:
            task: Web search task

        Returns:
            Search results and summary
        """
        query = task.parameters.get("query", "")
        max_results = task.parameters.get("max_results", 5)

        if not query:
            raise AgentError("Search query is required for web search task")

        # Perform web search
        search_result = await self.use_tool(
            "web_search", {"query": query, "max_results": max_results}
        )

        if not search_result.get("success"):
            raise AgentError(f"Web search failed: {search_result.get('error')}")

        search_data = search_result["result"]
        results = search_data.get("results", [])

        # Generate summary
        summary = await self._generate_search_summary(query, results)

        return {
            "query": query,
            "results": results,
            "total_results": len(results),
            "summary": summary,
            "search_time_ms": search_data.get("search_time_ms", 0),
        }

    async def _execute_text_analysis(self, task: Task) -> dict[str, Any]:
        """
        Execute a text analysis task.

        Args:
            task: Text analysis task

        Returns:
            Text analysis results and insights
        """
        text = task.parameters.get("text", "")
        include_keywords = task.parameters.get("include_keywords", True)
        include_sentiment = task.parameters.get("include_sentiment", False)

        if not text:
            raise AgentError("Text is required for text analysis task")

        # Perform text analysis
        analysis_result = await self.use_tool(
            "data_processor",
            {
                "operation": "text_analysis",
                "data": text,
                "options": {
                    "include_keywords": include_keywords,
                    "include_sentiment": include_sentiment,
                },
            },
        )

        if not analysis_result.get("success"):
            raise AgentError(f"Text analysis failed: {analysis_result.get('error')}")

        analysis_data = analysis_result["result"]

        # Generate insights
        insights = await self._generate_text_insights(analysis_data)

        return {
            "text_length": len(text),
            "analysis": analysis_data,
            "insights": insights,
            "processing_successful": True,
        }

    async def _execute_research_synthesis(self, task: Task) -> dict[str, Any]:
        """
        Execute a research synthesis task.

        Args:
            task: Research synthesis task

        Returns:
            Synthesized research findings
        """
        sources = task.parameters.get("sources", [])
        focus_areas = task.parameters.get("focus_areas", [])

        if not sources:
            raise AgentError("Sources are required for research synthesis task")

        # Analyze each source
        source_analyses = []
        for i, source in enumerate(sources):
            if isinstance(source, str):
                # Treat as text to analyze
                analysis_result = await self.use_tool(
                    "data_processor",
                    {
                        "operation": "text_analysis",
                        "data": source,
                        "options": {
                            "include_keywords": True,
                            "include_sentiment": False,
                        },
                    },
                )

                if analysis_result.get("success"):
                    source_analyses.append(
                        {
                            "source_id": f"source_{i+1}",
                            "type": "text",
                            "analysis": analysis_result["result"],
                        }
                    )
            elif isinstance(source, dict):
                # Already processed source
                source_analyses.append(
                    {"source_id": f"source_{i+1}", "type": "structured", "data": source}
                )

        # Synthesize findings
        synthesis = await self._synthesize_research_findings(
            source_analyses, focus_areas
        )

        return {
            "sources_analyzed": len(source_analyses),
            "focus_areas": focus_areas,
            "synthesis": synthesis["synthesis"],
            "key_findings": synthesis["key_findings"],
            "recommendations": synthesis["recommendations"],
            "confidence_score": synthesis.get("confidence_score", 0.8),
        }

    async def _execute_general_research(self, task: Task) -> dict[str, Any]:
        """
        Execute a general research task combining multiple capabilities.

        Args:
            task: General research task

        Returns:
            Comprehensive research results
        """
        topic = task.parameters.get("topic", "")
        depth = task.parameters.get("depth", "medium")  # shallow, medium, deep

        if not topic:
            raise AgentError("Research topic is required for general research task")

        logger.info(f"Conducting {depth} research on topic: {topic}")

        # Step 1: Web search
        search_results = await self._execute_web_search(
            Task(
                name="web_search_subtask",
                description=f"Search for information about {topic}",
                parameters={
                    "type": "web_search",
                    "query": topic,
                    "max_results": 8 if depth == "deep" else 5,
                },
            )
        )

        # Step 2: Analyze search results
        all_text = " ".join(
            [result.get("snippet", "") for result in search_results.get("results", [])]
        )

        if all_text.strip():
            text_analysis = await self._execute_text_analysis(
                Task(
                    name="text_analysis_subtask",
                    description=f"Analyze search results for {topic}",
                    parameters={
                        "type": "text_analysis",
                        "text": all_text,
                        "include_keywords": True,
                        "include_sentiment": depth == "deep",
                    },
                )
            )
        else:
            text_analysis = {"insights": [], "analysis": {}}

        # Step 3: Synthesize if deep research
        synthesis = None
        if depth == "deep":
            synthesis_sources = [all_text] if all_text.strip() else []
            if synthesis_sources:
                synthesis = await self._execute_research_synthesis(
                    Task(
                        name="synthesis_subtask",
                        description=f"Synthesize research findings for {topic}",
                        parameters={
                            "type": "research_synthesis",
                            "sources": synthesis_sources,
                            "focus_areas": [topic],
                        },
                    )
                )

        return {
            "topic": topic,
            "depth": depth,
            "search_results": search_results,
            "text_analysis": text_analysis,
            "synthesis": synthesis,
            "research_complete": True,
            "total_sources": len(search_results.get("results", [])),
            "research_quality": self._assess_research_quality(
                search_results, text_analysis, synthesis
            ),
        }

    async def _generate_search_summary(
        self, query: str, results: list[dict[str, Any]]
    ) -> str:
        """
        Generate a summary of search results.

        Args:
            query: Original search query
            results: Search results

        Returns:
            Summary text
        """
        if not results:
            return f"No results found for query: {query}"

        # Simple summary generation
        total_results = len(results)
        top_sources = [result.get("title", "Unknown") for result in results[:3]]

        summary = f"Found {total_results} results for '{query}'. "
        summary += f"Top sources include: {', '.join(top_sources)}. "

        # Analyze relevance scores if available
        scores = [result.get("relevance_score", 0) for result in results]
        if scores:
            avg_relevance = sum(scores) / len(scores)
            summary += f"Average relevance score: {avg_relevance:.2f}."

        return summary

    async def _generate_text_insights(self, analysis_data: dict[str, Any]) -> list[str]:
        """
        Generate insights from text analysis data.

        Args:
            analysis_data: Text analysis results

        Returns:
            List of insight strings
        """
        insights = []

        # Word count insights
        word_count = analysis_data.get("word_count", 0)
        if word_count > 1000:
            insights.append("This is a substantial text with comprehensive content")
        elif word_count > 500:
            insights.append("This is a moderate-length text with good detail")
        else:
            insights.append("This is a concise text with focused content")

        # Keyword insights
        top_keywords = analysis_data.get("top_keywords", [])
        if top_keywords:
            most_common = top_keywords[0][0] if top_keywords[0] else "unknown"
            insights.append(f"Most frequent topic appears to be: {most_common}")

            if len(top_keywords) > 5:
                insights.append("Text covers multiple diverse topics")

        # Sentiment insights
        sentiment = analysis_data.get("sentiment")
        if sentiment:
            overall = sentiment.get("overall", "neutral")
            insights.append(f"Overall sentiment of the text is {overall}")

        # Reading complexity
        avg_word_length = analysis_data.get("average_word_length", 0)
        if avg_word_length > 6:
            insights.append("Text uses complex vocabulary and may be technical")
        elif avg_word_length < 4:
            insights.append("Text uses simple vocabulary and is easily readable")

        return insights

    async def _synthesize_research_findings(
        self, source_analyses: list[dict[str, Any]], focus_areas: list[str]
    ) -> dict[str, Any]:
        """
        Synthesize research findings from multiple sources.

        Args:
            source_analyses: List of analyzed sources
            focus_areas: Areas to focus the synthesis on

        Returns:
            Synthesized research results
        """
        # Collect all keywords from sources
        all_keywords = []
        total_word_count = 0

        for source in source_analyses:
            if source["type"] == "text":
                analysis = source.get("analysis", {})
                keywords = analysis.get("top_keywords", [])
                all_keywords.extend(
                    [kw[0] for kw in keywords[:5]]
                )  # Top 5 from each source
                total_word_count += analysis.get("word_count", 0)

        # Find common themes
        from collections import Counter

        keyword_freq = Counter(all_keywords)
        common_themes = [kw for kw, count in keyword_freq.most_common(10) if count > 1]

        # Generate synthesis
        synthesis_text = (
            f"Analysis of {len(source_analyses)} sources reveals several key themes. "
        )

        if common_themes:
            synthesis_text += (
                f"The most prominent topics include: {', '.join(common_themes[:5])}. "
            )

        if focus_areas:
            synthesis_text += f"With specific focus on {', '.join(focus_areas)}, "
            synthesis_text += (
                "the research indicates strong relevance across multiple sources. "
            )

        synthesis_text += f"Total content analyzed: {total_word_count} words across {len(source_analyses)} sources."

        # Generate key findings
        key_findings = []
        if common_themes:
            key_findings.append(f"Primary theme: {common_themes[0]}")
            if len(common_themes) > 1:
                key_findings.append(
                    f"Secondary themes: {', '.join(common_themes[1:3])}"
                )

        key_findings.append(f"Sources show {len(set(all_keywords))} unique concepts")

        # Generate recommendations
        recommendations = [
            "Further research recommended on primary themes identified",
            "Consider expanding source diversity for comprehensive coverage",
        ]

        if len(source_analyses) < 3:
            recommendations.append(
                "Additional sources would strengthen the research foundation"
            )

        confidence_score = min(
            0.9, 0.5 + (len(source_analyses) * 0.1) + (len(common_themes) * 0.05)
        )

        return {
            "synthesis": synthesis_text,
            "key_findings": key_findings,
            "recommendations": recommendations,
            "common_themes": common_themes,
            "confidence_score": confidence_score,
        }

    def _assess_research_quality(
        self,
        search_results: dict[str, Any],
        text_analysis: dict[str, Any],
        synthesis: dict[str, Any] | None,
    ) -> str:
        """
        Assess the quality of the research conducted.

        Args:
            search_results: Search results data
            text_analysis: Text analysis data
            synthesis: Synthesis data (if available)

        Returns:
            Quality assessment string
        """
        score = 0
        factors = []

        # Search quality
        num_results = len(search_results.get("results", []))
        if num_results >= 5:
            score += 30
            factors.append("comprehensive search coverage")
        elif num_results >= 3:
            score += 20
            factors.append("adequate search coverage")
        else:
            score += 10
            factors.append("limited search coverage")

        # Analysis quality
        analysis = text_analysis.get("analysis", {})
        word_count = analysis.get("word_count", 0)
        if word_count > 500:
            score += 25
            factors.append("substantial content analysis")
        elif word_count > 200:
            score += 15
            factors.append("moderate content analysis")
        else:
            score += 5
            factors.append("basic content analysis")

        # Synthesis quality
        if synthesis:
            confidence = synthesis.get("confidence_score", 0)
            score += int(confidence * 25)
            factors.append("comprehensive synthesis")
        else:
            score += 10
            factors.append("no synthesis performed")

        # Insights quality
        insights = text_analysis.get("insights", [])
        if len(insights) > 3:
            score += 20
            factors.append("rich insights generated")
        else:
            score += 10
            factors.append("basic insights generated")

        # Determine quality level
        if score >= 80:
            quality = "excellent"
        elif score >= 60:
            quality = "good"
        elif score >= 40:
            quality = "fair"
        else:
            quality = "basic"

        return f"{quality} (score: {score}/100, factors: {', '.join(factors)})"

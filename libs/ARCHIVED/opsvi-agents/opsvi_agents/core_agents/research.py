"""ResearchAgent - Information gathering and research."""

import json
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

import structlog

from ..core import AgentConfig, AgentContext, AgentResult, BaseAgent

logger = structlog.get_logger()


class ResearchMethod(Enum):
    """Research methods available."""

    SEARCH = "search"
    ANALYZE = "analyze"
    SUMMARIZE = "summarize"
    EXTRACT = "extract"
    COMPARE = "compare"
    SYNTHESIZE = "synthesize"


class SourceType(Enum):
    """Types of information sources."""

    FILE = "file"
    API = "api"
    DATABASE = "database"
    WEB = "web"
    CACHE = "cache"
    TOOL = "tool"
    AGENT = "agent"


@dataclass
class Source:
    """Information source."""

    id: str
    type: SourceType
    location: str
    reliability: float = 1.0  # 0-1 reliability score
    accessed_at: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "type": self.type.value,
            "location": self.location,
            "reliability": self.reliability,
            "accessed_at": self.accessed_at,
            "metadata": self.metadata,
        }


@dataclass
class Finding:
    """Research finding."""

    id: str
    content: Any
    source: Source
    relevance: float = 1.0  # 0-1 relevance score
    confidence: float = 1.0  # 0-1 confidence score
    keywords: List[str] = field(default_factory=list)
    summary: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "content": self.content,
            "source": self.source.to_dict(),
            "relevance": self.relevance,
            "confidence": self.confidence,
            "keywords": self.keywords,
            "summary": self.summary,
        }


@dataclass
class ResearchResult:
    """Complete research result."""

    query: str
    findings: List[Finding]
    sources_searched: int
    time_taken: float
    method: ResearchMethod
    summary: Optional[str] = None
    conclusions: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def get_top_findings(self, n: int = 5) -> List[Finding]:
        """Get top N findings by relevance and confidence."""
        sorted_findings = sorted(
            self.findings, key=lambda f: f.relevance * f.confidence, reverse=True
        )
        return sorted_findings[:n]

    def get_findings_by_source(self, source_type: SourceType) -> List[Finding]:
        """Get findings from specific source type."""
        return [f for f in self.findings if f.source.type == source_type]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "query": self.query,
            "findings": [f.to_dict() for f in self.findings],
            "sources_searched": self.sources_searched,
            "time_taken": self.time_taken,
            "method": self.method.value,
            "summary": self.summary,
            "conclusions": self.conclusions,
            "recommendations": self.recommendations,
            "metadata": self.metadata,
        }


class ResearchAgent(BaseAgent):
    """Gathers and analyzes information from various sources."""

    def __init__(self, config: Optional[AgentConfig] = None):
        """Initialize research agent."""
        super().__init__(
            config
            or AgentConfig(
                name="ResearchAgent",
                description="Information gathering and research",
                capabilities=[
                    "search",
                    "analyze",
                    "summarize",
                    "extract",
                    "synthesize",
                ],
                max_retries=3,
                timeout=120,
            )
        )
        self.sources: Dict[str, Source] = {}
        self.findings_cache: Dict[str, List[Finding]] = {}
        self.research_history: List[ResearchResult] = []
        self._finding_counter = 0
        self._source_counter = 0
        self.max_history = 50

    def initialize(self) -> bool:
        """Initialize the research agent."""
        # Initialize available sources
        self._initialize_sources()
        logger.info("research_agent_initialized", agent=self.config.name)
        return True

    def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute research task."""
        action = task.get("action", "research")

        if action == "research":
            return self._conduct_research(task)
        elif action == "search":
            return self._search_sources(task)
        elif action == "analyze":
            return self._analyze_data(task)
        elif action == "summarize":
            return self._summarize_findings(task)
        elif action == "extract":
            return self._extract_information(task)
        elif action == "synthesize":
            return self._synthesize_knowledge(task)
        elif action == "history":
            return self._get_history(task)
        else:
            return {"error": f"Unknown action: {action}"}

    def research(
        self,
        query: str,
        method: ResearchMethod = ResearchMethod.SEARCH,
        sources: Optional[List[SourceType]] = None,
        max_results: int = 10,
    ) -> ResearchResult:
        """Conduct research on a query."""
        result = self.execute(
            {
                "action": "research",
                "query": query,
                "method": method.value,
                "sources": sources,
                "max_results": max_results,
            }
        )

        if "error" in result:
            raise RuntimeError(result["error"])

        return result["research_result"]

    def _conduct_research(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Conduct comprehensive research."""
        query = task.get("query", "")
        method = task.get("method", "search")
        source_types = task.get("sources")
        max_results = task.get("max_results", 10)

        if not query:
            return {"error": "Query is required"}

        start_time = time.time()

        # Determine research method
        method_enum = (
            ResearchMethod[method.upper()] if isinstance(method, str) else method
        )

        # Determine sources to search
        if source_types:
            sources_to_search = [
                SourceType[s.upper()] if isinstance(s, str) else s for s in source_types
            ]
        else:
            sources_to_search = list(SourceType)

        # Conduct research based on method
        if method_enum == ResearchMethod.SEARCH:
            findings = self._search_all_sources(query, sources_to_search, max_results)
        elif method_enum == ResearchMethod.ANALYZE:
            findings = self._analyze_query(query, sources_to_search)
        elif method_enum == ResearchMethod.EXTRACT:
            findings = self._extract_from_sources(query, sources_to_search)
        else:
            findings = self._general_research(query, sources_to_search, max_results)

        # Generate summary and conclusions
        summary = self._generate_summary(findings)
        conclusions = self._draw_conclusions(findings, query)
        recommendations = self._make_recommendations(findings, query)

        time_taken = time.time() - start_time

        # Create research result
        result = ResearchResult(
            query=query,
            findings=findings,
            sources_searched=len(sources_to_search),
            time_taken=time_taken,
            method=method_enum,
            summary=summary,
            conclusions=conclusions,
            recommendations=recommendations,
        )

        # Store in history
        self.research_history.append(result)
        if len(self.research_history) > self.max_history:
            self.research_history = self.research_history[-self.max_history :]

        logger.info(
            "research_completed",
            query=query,
            method=method_enum.value,
            findings_count=len(findings),
            time_taken=time_taken,
        )

        return {
            "research_result": result,
            "findings_count": len(findings),
            "top_findings": [f.to_dict() for f in result.get_top_findings(3)],
        }

    def _initialize_sources(self):
        """Initialize available information sources."""
        # Add default sources
        self._add_source("local_files", SourceType.FILE, ".", reliability=1.0)
        self._add_source("cache", SourceType.CACHE, "memory", reliability=0.9)
        self._add_source("web_search", SourceType.WEB, "internet", reliability=0.7)
        self._add_source("internal_api", SourceType.API, "localhost", reliability=0.95)

    def _add_source(
        self, id: str, type: SourceType, location: str, reliability: float = 1.0
    ) -> Source:
        """Add an information source."""
        source = Source(id=id, type=type, location=location, reliability=reliability)
        self.sources[id] = source
        return source

    def _search_all_sources(
        self, query: str, source_types: List[SourceType], max_results: int
    ) -> List[Finding]:
        """Search all specified source types."""
        all_findings = []

        for source_type in source_types:
            # Get sources of this type
            sources = [s for s in self.sources.values() if s.type == source_type]

            for source in sources:
                findings = self._search_source(
                    source, query, max_results // len(sources)
                )
                all_findings.extend(findings)

        # Sort by relevance
        all_findings.sort(key=lambda f: f.relevance * f.confidence, reverse=True)

        return all_findings[:max_results]

    def _search_source(
        self, source: Source, query: str, max_results: int
    ) -> List[Finding]:
        """Search a specific source."""
        findings = []

        # Check cache first
        cache_key = f"{source.id}:{query}"
        if cache_key in self.findings_cache:
            cached = self.findings_cache[cache_key]
            logger.debug(f"Using cached findings for {cache_key}")
            return cached[:max_results]

        # Simulate searching based on source type
        if source.type == SourceType.FILE:
            findings = self._search_files(query, max_results)
        elif source.type == SourceType.CACHE:
            findings = self._search_cache(query, max_results)
        elif source.type == SourceType.WEB:
            findings = self._search_web(query, max_results)
        elif source.type == SourceType.API:
            findings = self._search_api(query, max_results)
        else:
            findings = self._mock_search(source, query, max_results)

        # Set source for all findings
        for finding in findings:
            finding.source = source
            finding.confidence *= source.reliability

        # Cache findings
        self.findings_cache[cache_key] = findings

        # Update source access time
        source.accessed_at = time.time()

        return findings

    def _search_files(self, query: str, max_results: int) -> List[Finding]:
        """Search local files (mock implementation)."""
        findings = []

        # Mock file search results
        for i in range(min(3, max_results)):
            self._finding_counter += 1
            finding = Finding(
                id=f"finding_{self._finding_counter}",
                content=f"File content matching '{query}' in file_{i}.txt",
                source=Source(
                    id="files", type=SourceType.FILE, location=f"file_{i}.txt"
                ),
                relevance=0.8 - i * 0.1,
                confidence=0.9,
                keywords=query.split()[:3],
                summary=f"Found match in file_{i}.txt",
            )
            findings.append(finding)

        return findings

    def _search_cache(self, query: str, max_results: int) -> List[Finding]:
        """Search cached information."""
        findings = []

        # Check previous research results
        for result in self.research_history[-10:]:
            if query.lower() in result.query.lower():
                for finding in result.findings[:max_results]:
                    # Create new finding from cached
                    self._finding_counter += 1
                    new_finding = Finding(
                        id=f"finding_{self._finding_counter}",
                        content=finding.content,
                        source=Source(
                            id="cache", type=SourceType.CACHE, location="memory"
                        ),
                        relevance=finding.relevance * 0.9,  # Slightly lower for cached
                        confidence=finding.confidence,
                        keywords=finding.keywords,
                        summary=f"Cached: {finding.summary}",
                    )
                    findings.append(new_finding)

        return findings[:max_results]

    def _search_web(self, query: str, max_results: int) -> List[Finding]:
        """Search web (mock implementation)."""
        findings = []

        # Mock web search results
        for i in range(min(5, max_results)):
            self._finding_counter += 1
            finding = Finding(
                id=f"finding_{self._finding_counter}",
                content=f"Web result {i+1} for '{query}'",
                source=Source(
                    id="web",
                    type=SourceType.WEB,
                    location=f"http://example.com/result{i}",
                ),
                relevance=0.7 - i * 0.1,
                confidence=0.6,  # Lower confidence for web
                keywords=query.split()[:3],
                summary=f"Web result from example.com",
            )
            findings.append(finding)

        return findings

    def _search_api(self, query: str, max_results: int) -> List[Finding]:
        """Search via API (mock implementation)."""
        findings = []

        # Mock API results
        self._finding_counter += 1
        finding = Finding(
            id=f"finding_{self._finding_counter}",
            content={"api_response": f"Data for query: {query}"},
            source=Source(id="api", type=SourceType.API, location="internal_api"),
            relevance=0.9,
            confidence=0.95,
            keywords=query.split()[:3],
            summary="API response data",
        )
        findings.append(finding)

        return findings

    def _mock_search(
        self, source: Source, query: str, max_results: int
    ) -> List[Finding]:
        """Mock search for other source types."""
        findings = []

        self._finding_counter += 1
        finding = Finding(
            id=f"finding_{self._finding_counter}",
            content=f"Mock result from {source.type.value} for '{query}'",
            source=source,
            relevance=0.5,
            confidence=0.5,
            keywords=query.split()[:2],
            summary=f"Mock {source.type.value} result",
        )
        findings.append(finding)

        return findings

    def _analyze_query(
        self, query: str, source_types: List[SourceType]
    ) -> List[Finding]:
        """Analyze query to extract information."""
        findings = []

        # Extract key concepts from query
        keywords = self._extract_keywords(query)

        # Search for each keyword
        for keyword in keywords[:3]:
            keyword_findings = self._search_all_sources(keyword, source_types, 3)
            findings.extend(keyword_findings)

        return findings

    def _extract_from_sources(
        self, query: str, source_types: List[SourceType]
    ) -> List[Finding]:
        """Extract specific information from sources."""
        findings = []

        # Define extraction patterns based on query
        patterns = self._define_extraction_patterns(query)

        # Search and extract
        raw_findings = self._search_all_sources(query, source_types, 20)

        for finding in raw_findings:
            # Extract based on patterns
            extracted = self._apply_extraction_patterns(finding.content, patterns)
            if extracted:
                finding.content = extracted
                finding.relevance = min(1.0, finding.relevance * 1.2)  # Boost relevance
                findings.append(finding)

        return findings

    def _general_research(
        self, query: str, source_types: List[SourceType], max_results: int
    ) -> List[Finding]:
        """General research combining multiple methods."""
        findings = []

        # Search
        search_findings = self._search_all_sources(
            query, source_types, max_results // 2
        )
        findings.extend(search_findings)

        # Analyze
        analysis_findings = self._analyze_query(query, source_types)
        findings.extend(analysis_findings[: max_results // 4])

        # Extract
        extraction_findings = self._extract_from_sources(query, source_types)
        findings.extend(extraction_findings[: max_results // 4])

        # Deduplicate and sort
        seen = set()
        unique_findings = []
        for finding in findings:
            if finding.id not in seen:
                seen.add(finding.id)
                unique_findings.append(finding)

        unique_findings.sort(key=lambda f: f.relevance * f.confidence, reverse=True)

        return unique_findings[:max_results]

    def _extract_keywords(self, query: str) -> List[str]:
        """Extract keywords from query."""
        # Simple keyword extraction
        stop_words = {
            "the",
            "a",
            "an",
            "and",
            "or",
            "but",
            "in",
            "on",
            "at",
            "to",
            "for",
        }
        words = query.lower().split()
        keywords = [w for w in words if w not in stop_words and len(w) > 2]
        return keywords

    def _define_extraction_patterns(self, query: str) -> List[str]:
        """Define extraction patterns based on query."""
        patterns = []

        # Add patterns based on query keywords
        if "function" in query.lower():
            patterns.append("def ")
        if "class" in query.lower():
            patterns.append("class ")
        if "error" in query.lower():
            patterns.append("Error")
        if "config" in query.lower():
            patterns.append("config")

        return patterns

    def _apply_extraction_patterns(self, content: Any, patterns: List[str]) -> Any:
        """Apply extraction patterns to content."""
        if not patterns or not isinstance(content, str):
            return content

        extracted = []
        lines = content.split("\n") if isinstance(content, str) else []

        for line in lines:
            for pattern in patterns:
                if pattern in line:
                    extracted.append(line.strip())
                    break

        return "\n".join(extracted) if extracted else None

    def _generate_summary(self, findings: List[Finding]) -> str:
        """Generate summary of findings."""
        if not findings:
            return "No relevant findings discovered."

        top_findings = findings[:3]
        summary_parts = [
            f"Found {len(findings)} relevant results.",
            f"Top sources: {', '.join(set(f.source.type.value for f in top_findings))}.",
        ]

        if top_findings:
            avg_confidence = sum(f.confidence for f in top_findings) / len(top_findings)
            summary_parts.append(f"Average confidence: {avg_confidence:.2f}")

        return " ".join(summary_parts)

    def _draw_conclusions(self, findings: List[Finding], query: str) -> List[str]:
        """Draw conclusions from findings."""
        conclusions = []

        if not findings:
            conclusions.append("Insufficient data to draw conclusions")
            return conclusions

        # Analyze finding patterns
        high_confidence = [f for f in findings if f.confidence > 0.8]
        if high_confidence:
            conclusions.append(
                f"High confidence results found ({len(high_confidence)} findings)"
            )

        # Source diversity
        source_types = set(f.source.type for f in findings)
        if len(source_types) > 2:
            conclusions.append("Multiple source types corroborate findings")

        # Relevance analysis
        avg_relevance = sum(f.relevance for f in findings) / len(findings)
        if avg_relevance > 0.7:
            conclusions.append("Findings are highly relevant to the query")
        elif avg_relevance < 0.4:
            conclusions.append("Limited relevance found - consider refining the query")

        return conclusions

    def _make_recommendations(self, findings: List[Finding], query: str) -> List[str]:
        """Make recommendations based on findings."""
        recommendations = []

        if not findings:
            recommendations.append("Broaden search criteria or try alternative sources")
            return recommendations

        # Analyze gaps
        source_types_used = set(f.source.type for f in findings)
        unused_types = set(SourceType) - source_types_used

        if unused_types:
            recommendations.append(
                f"Consider searching: {', '.join(t.value for t in unused_types)}"
            )

        # Quality recommendations
        low_confidence = [f for f in findings if f.confidence < 0.5]
        if len(low_confidence) > len(findings) / 2:
            recommendations.append("Verify findings with more reliable sources")

        # Depth recommendations
        if len(findings) < 5:
            recommendations.append("Expand search to gather more comprehensive data")

        return recommendations

    def _search_sources(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Search specific sources."""
        query = task.get("query", "")
        source_ids = task.get("source_ids", [])
        max_results = task.get("max_results", 10)

        if not query:
            return {"error": "Query is required"}

        findings = []
        for source_id in source_ids:
            if source_id in self.sources:
                source = self.sources[source_id]
                source_findings = self._search_source(source, query, max_results)
                findings.extend(source_findings)

        return {"findings": [f.to_dict() for f in findings], "count": len(findings)}

    def _analyze_data(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze data."""
        data = task.get("data")
        analysis_type = task.get("analysis_type", "general")

        if data is None:
            return {"error": "Data is required"}

        analysis = {
            "type": analysis_type,
            "data_type": type(data).__name__,
            "size": len(str(data)),
        }

        if isinstance(data, (list, dict)):
            analysis["structure"] = "structured"
            analysis["elements"] = len(data)
        elif isinstance(data, str):
            analysis["structure"] = "text"
            analysis["lines"] = data.count("\n") + 1
            analysis["words"] = len(data.split())

        return {"analysis": analysis}

    def _summarize_findings(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Summarize findings."""
        findings_data = task.get("findings", [])
        max_length = task.get("max_length", 500)

        if not findings_data:
            return {"error": "Findings are required"}

        # Convert to Finding objects if needed
        findings = []
        for f in findings_data:
            if isinstance(f, dict):
                # Reconstruct Finding from dict
                source = Source(
                    id=f.get("source", {}).get("id", "unknown"),
                    type=SourceType[f.get("source", {}).get("type", "FILE").upper()],
                    location=f.get("source", {}).get("location", ""),
                )
                finding = Finding(
                    id=f.get("id", ""),
                    content=f.get("content"),
                    source=source,
                    relevance=f.get("relevance", 1.0),
                    confidence=f.get("confidence", 1.0),
                )
                findings.append(finding)
            else:
                findings.append(f)

        summary = self._generate_summary(findings)

        # Truncate if needed
        if len(summary) > max_length:
            summary = summary[: max_length - 3] + "..."

        return {"summary": summary}

    def _extract_information(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Extract specific information."""
        content = task.get("content", "")
        patterns = task.get("patterns", [])

        if not content:
            return {"error": "Content is required"}

        extracted = self._apply_extraction_patterns(content, patterns)

        return {"extracted": extracted, "patterns_used": patterns}

    def _synthesize_knowledge(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Synthesize knowledge from multiple sources."""
        sources_data = task.get("sources", [])

        if not sources_data:
            return {"error": "Sources are required"}

        # Combine and synthesize
        synthesis = {
            "source_count": len(sources_data),
            "combined_knowledge": [],
            "contradictions": [],
            "consensus": [],
        }

        # Simple synthesis (can be enhanced with NLP)
        all_content = []
        for source in sources_data:
            if isinstance(source, dict):
                all_content.append(source.get("content", ""))
            else:
                all_content.append(str(source))

        # Find common themes
        common_words = {}
        for content in all_content:
            words = content.lower().split() if isinstance(content, str) else []
            for word in words:
                if len(word) > 4:  # Focus on longer words
                    common_words[word] = common_words.get(word, 0) + 1

        # Top themes
        top_themes = sorted(common_words.items(), key=lambda x: x[1], reverse=True)[:5]
        synthesis["consensus"] = [theme[0] for theme in top_themes]

        return {"synthesis": synthesis}

    def _get_history(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Get research history."""
        limit = task.get("limit", 10)
        query_filter = task.get("query_filter")

        history = self.research_history[-limit:]

        if query_filter:
            history = [r for r in history if query_filter.lower() in r.query.lower()]

        return {
            "history": [r.to_dict() for r in history],
            "total_research": len(self.research_history),
        }

    def shutdown(self) -> bool:
        """Shutdown the research agent."""
        logger.info(
            "research_agent_shutdown",
            sources_count=len(self.sources),
            cache_size=len(self.findings_cache),
            history_size=len(self.research_history),
        )
        self.sources.clear()
        self.findings_cache.clear()
        self.research_history.clear()
        return True

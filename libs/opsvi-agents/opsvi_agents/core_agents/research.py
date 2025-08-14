"""ResearchAgent - Information gathering and research."""

from typing import Any, Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
import time
import json
import structlog

from ..core import BaseAgent, AgentConfig, AgentContext, AgentResult


logger = structlog.get_logger()


class ResearchDepth(Enum):
    """Depth levels for research."""
    SHALLOW = "shallow"  # Quick search, top results
    MEDIUM = "medium"    # Standard search, some analysis
    DEEP = "deep"        # Comprehensive search, detailed analysis
    EXHAUSTIVE = "exhaustive"  # All available sources, full analysis


class SourceType(Enum):
    """Types of information sources."""
    WEB = "web"
    DATABASE = "database"
    API = "api"
    FILE = "file"
    CACHE = "cache"
    MODEL = "model"
    EXPERT = "expert"


@dataclass
class Source:
    """Information source."""
    type: SourceType
    name: str
    url: Optional[str] = None
    reliability: float = 0.5  # 0-1 scale
    timestamp: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "type": self.type.value,
            "name": self.name,
            "url": self.url,
            "reliability": self.reliability,
            "timestamp": self.timestamp,
            "metadata": self.metadata
        }


@dataclass
class Finding:
    """Research finding."""
    content: str
    source: Source
    relevance: float = 0.5  # 0-1 scale
    confidence: float = 0.5  # 0-1 scale
    supporting_evidence: List[str] = field(default_factory=list)
    contradicting_evidence: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "content": self.content,
            "source": self.source.to_dict(),
            "relevance": self.relevance,
            "confidence": self.confidence,
            "supporting_evidence": self.supporting_evidence,
            "contradicting_evidence": self.contradicting_evidence,
            "tags": self.tags
        }


@dataclass
class ResearchResult:
    """Complete research result."""
    query: str
    depth: ResearchDepth
    findings: List[Finding]
    summary: str
    key_insights: List[str]
    gaps: List[str]
    sources_consulted: List[Source]
    duration: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def get_top_findings(self, n: int = 5) -> List[Finding]:
        """Get top N most relevant findings."""
        sorted_findings = sorted(
            self.findings,
            key=lambda f: f.relevance * f.confidence,
            reverse=True
        )
        return sorted_findings[:n]
    
    def get_high_confidence_findings(self, threshold: float = 0.7) -> List[Finding]:
        """Get findings above confidence threshold."""
        return [f for f in self.findings if f.confidence >= threshold]
    
    def get_conflicting_findings(self) -> List[Tuple[Finding, Finding]]:
        """Get pairs of conflicting findings."""
        conflicts = []
        
        for i, f1 in enumerate(self.findings):
            for f2 in self.findings[i+1:]:
                # Simple conflict detection based on contradicting evidence
                if (f1.content in f2.contradicting_evidence or 
                    f2.content in f1.contradicting_evidence):
                    conflicts.append((f1, f2))
        
        return conflicts
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "query": self.query,
            "depth": self.depth.value,
            "findings_count": len(self.findings),
            "summary": self.summary,
            "key_insights": self.key_insights,
            "gaps": self.gaps,
            "sources_count": len(self.sources_consulted),
            "duration": self.duration,
            "metadata": self.metadata
        }


class ResearchAgent(BaseAgent):
    """Information gathering and research agent."""
    
    def __init__(self, config: Optional[AgentConfig] = None):
        """Initialize research agent."""
        super().__init__(config or AgentConfig(
            name="ResearchAgent",
            description="Information gathering and research",
            capabilities=["search", "analyze", "summarize", "synthesize"],
            max_retries=3,
            timeout=120
        ))
        self.cache = {}  # Simple in-memory cache
        self.research_history = []
        self.sources = self._initialize_sources()
        self._research_counter = 0
    
    def initialize(self) -> bool:
        """Initialize the research agent."""
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
            return self._analyze_findings(task)
        elif action == "synthesize":
            return self._synthesize_information(task)
        elif action == "verify":
            return self._verify_information(task)
        elif action == "expand":
            return self._expand_research(task)
        else:
            return {"error": f"Unknown action: {action}"}
    
    def research(self, 
                topic: str,
                depth: ResearchDepth = ResearchDepth.MEDIUM,
                sources: Optional[List[str]] = None) -> ResearchResult:
        """Conduct research on a topic."""
        result = self.execute({
            "action": "research",
            "topic": topic,
            "depth": depth,
            "sources": sources
        })
        
        if "error" in result:
            raise RuntimeError(result["error"])
        
        return result["research_result"]
    
    def _conduct_research(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Conduct comprehensive research."""
        topic = task.get("topic", "")
        depth = task.get("depth", ResearchDepth.MEDIUM)
        specific_sources = task.get("sources", None)
        
        if not topic:
            return {"error": "Research topic is required"}
        
        # Convert depth if string
        if isinstance(depth, str):
            depth = ResearchDepth[depth.upper()]
        
        start_time = time.time()
        
        # Check cache first
        cache_key = f"{topic}_{depth.value}"
        if cache_key in self.cache:
            cached_result = self.cache[cache_key]
            if time.time() - cached_result["timestamp"] < 3600:  # 1 hour cache
                logger.info("research_cache_hit", topic=topic)
                return {"research_result": cached_result["result"]}
        
        # Generate research ID
        self._research_counter += 1
        research_id = f"research_{self._research_counter}"
        
        # Determine sources to use
        sources_to_use = self._select_sources(depth, specific_sources)
        
        # Gather information from sources
        raw_findings = []
        sources_consulted = []
        
        for source in sources_to_use:
            findings = self._search_source(source, topic, depth)
            raw_findings.extend(findings)
            sources_consulted.append(source)
        
        # Process and filter findings
        processed_findings = self._process_findings(raw_findings, topic)
        
        # Analyze findings
        analysis = self._analyze_findings_internal(processed_findings, topic)
        
        # Generate summary and insights
        summary = self._generate_summary(processed_findings, analysis)
        key_insights = self._extract_insights(processed_findings, analysis)
        gaps = self._identify_gaps(processed_findings, topic)
        
        # Create research result
        duration = time.time() - start_time
        
        research_result = ResearchResult(
            query=topic,
            depth=depth,
            findings=processed_findings,
            summary=summary,
            key_insights=key_insights,
            gaps=gaps,
            sources_consulted=sources_consulted,
            duration=duration,
            metadata={"research_id": research_id}
        )
        
        # Cache result
        self.cache[cache_key] = {
            "result": research_result,
            "timestamp": time.time()
        }
        
        # Track in history
        self.research_history.append({
            "id": research_id,
            "topic": topic,
            "depth": depth.value,
            "timestamp": time.time(),
            "duration": duration,
            "findings_count": len(processed_findings)
        })
        
        logger.info(
            "research_completed",
            research_id=research_id,
            topic=topic,
            depth=depth.value,
            findings_count=len(processed_findings),
            duration=duration
        )
        
        return {
            "research_result": research_result,
            "research_id": research_id
        }
    
    def _initialize_sources(self) -> List[Source]:
        """Initialize available information sources."""
        return [
            Source(
                type=SourceType.WEB,
                name="General Web Search",
                reliability=0.6
            ),
            Source(
                type=SourceType.DATABASE,
                name="Knowledge Base",
                reliability=0.9
            ),
            Source(
                type=SourceType.API,
                name="External APIs",
                reliability=0.8
            ),
            Source(
                type=SourceType.CACHE,
                name="Local Cache",
                reliability=1.0
            ),
            Source(
                type=SourceType.MODEL,
                name="AI Model Knowledge",
                reliability=0.7
            )
        ]
    
    def _select_sources(self, depth: ResearchDepth, 
                       specific_sources: Optional[List[str]]) -> List[Source]:
        """Select sources based on depth and requirements."""
        if specific_sources:
            # Use specific sources if provided
            return [s for s in self.sources if s.name in specific_sources]
        
        # Select based on depth
        if depth == ResearchDepth.SHALLOW:
            return [s for s in self.sources if s.type == SourceType.CACHE][:1]
        elif depth == ResearchDepth.MEDIUM:
            return [s for s in self.sources if s.type in [SourceType.CACHE, SourceType.DATABASE]][:2]
        elif depth == ResearchDepth.DEEP:
            return [s for s in self.sources if s.reliability >= 0.7][:4]
        else:  # EXHAUSTIVE
            return self.sources
    
    def _search_source(self, source: Source, query: str, 
                      depth: ResearchDepth) -> List[Finding]:
        """Search a specific source for information."""
        findings = []
        
        # Simulate source searching (would be real implementation)
        if source.type == SourceType.CACHE:
            # Check cache
            if query in self.cache:
                cached = self.cache[query]
                if isinstance(cached, dict) and "findings" in cached:
                    return cached["findings"]
        
        elif source.type == SourceType.MODEL:
            # Use model knowledge
            finding = Finding(
                content=f"Based on training data: {query} involves multiple aspects including technical, practical, and theoretical components.",
                source=source,
                relevance=0.7,
                confidence=0.6,
                tags=["model_knowledge", "general"]
            )
            findings.append(finding)
        
        elif source.type == SourceType.DATABASE:
            # Simulate database query
            finding = Finding(
                content=f"Database entry for '{query}': Comprehensive information available with high reliability.",
                source=source,
                relevance=0.9,
                confidence=0.8,
                tags=["database", "verified"]
            )
            findings.append(finding)
        
        else:
            # Generic search simulation
            num_findings = {
                ResearchDepth.SHALLOW: 1,
                ResearchDepth.MEDIUM: 3,
                ResearchDepth.DEEP: 5,
                ResearchDepth.EXHAUSTIVE: 10
            }.get(depth, 3)
            
            for i in range(num_findings):
                finding = Finding(
                    content=f"Finding {i+1} from {source.name}: Information about {query}",
                    source=source,
                    relevance=0.5 + (i * 0.1),
                    confidence=source.reliability,
                    tags=[source.type.value, f"result_{i+1}"]
                )
                findings.append(finding)
        
        return findings
    
    def _process_findings(self, findings: List[Finding], query: str) -> List[Finding]:
        """Process and filter findings."""
        processed = []
        
        for finding in findings:
            # Calculate relevance based on query terms
            query_terms = query.lower().split()
            content_lower = finding.content.lower()
            
            matches = sum(1 for term in query_terms if term in content_lower)
            finding.relevance = min(1.0, matches / len(query_terms) if query_terms else 0)
            
            # Deduplicate similar findings
            is_duplicate = False
            for p in processed:
                if self._similarity(finding.content, p.content) > 0.9:
                    # Merge evidence
                    p.supporting_evidence.extend(finding.supporting_evidence)
                    p.confidence = max(p.confidence, finding.confidence)
                    is_duplicate = True
                    break
            
            if not is_duplicate and finding.relevance > 0.3:
                processed.append(finding)
        
        return processed
    
    def _similarity(self, text1: str, text2: str) -> float:
        """Calculate simple text similarity."""
        # Simple word overlap similarity
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0
    
    def _analyze_findings_internal(self, findings: List[Finding], query: str) -> Dict[str, Any]:
        """Analyze findings for patterns and insights."""
        analysis = {
            "total_findings": len(findings),
            "avg_confidence": sum(f.confidence for f in findings) / len(findings) if findings else 0,
            "avg_relevance": sum(f.relevance for f in findings) / len(findings) if findings else 0,
            "source_distribution": {},
            "common_tags": {},
            "confidence_distribution": {
                "high": 0,
                "medium": 0,
                "low": 0
            }
        }
        
        # Analyze source distribution
        for finding in findings:
            source_type = finding.source.type.value
            analysis["source_distribution"][source_type] = \
                analysis["source_distribution"].get(source_type, 0) + 1
        
        # Analyze tags
        for finding in findings:
            for tag in finding.tags:
                analysis["common_tags"][tag] = analysis["common_tags"].get(tag, 0) + 1
        
        # Confidence distribution
        for finding in findings:
            if finding.confidence >= 0.7:
                analysis["confidence_distribution"]["high"] += 1
            elif finding.confidence >= 0.4:
                analysis["confidence_distribution"]["medium"] += 1
            else:
                analysis["confidence_distribution"]["low"] += 1
        
        return analysis
    
    def _generate_summary(self, findings: List[Finding], analysis: Dict[str, Any]) -> str:
        """Generate research summary."""
        if not findings:
            return "No relevant information found for the query."
        
        top_findings = sorted(findings, key=lambda f: f.relevance * f.confidence, reverse=True)[:3]
        
        summary_parts = [
            f"Found {len(findings)} relevant pieces of information.",
            f"Average confidence: {analysis['avg_confidence']:.2f}.",
            f"Top sources: {', '.join(list(analysis['source_distribution'].keys())[:3])}."
        ]
        
        if top_findings:
            summary_parts.append("Key findings: " + "; ".join(
                f.content[:100] + "..." if len(f.content) > 100 else f.content
                for f in top_findings[:2]
            ))
        
        return " ".join(summary_parts)
    
    def _extract_insights(self, findings: List[Finding], analysis: Dict[str, Any]) -> List[str]:
        """Extract key insights from findings."""
        insights = []
        
        # High confidence findings
        high_conf = [f for f in findings if f.confidence >= 0.8]
        if high_conf:
            insights.append(f"Found {len(high_conf)} highly reliable findings")
        
        # Consensus findings
        if len(findings) > 3:
            # Find common themes
            common_words = {}
            for finding in findings:
                words = finding.content.lower().split()
                for word in words:
                    if len(word) > 4:  # Skip short words
                        common_words[word] = common_words.get(word, 0) + 1
            
            top_themes = sorted(common_words.items(), key=lambda x: x[1], reverse=True)[:3]
            if top_themes:
                insights.append(f"Common themes: {', '.join(word for word, _ in top_themes)}")
        
        # Source reliability
        if analysis["source_distribution"]:
            most_used = max(analysis["source_distribution"].items(), key=lambda x: x[1])
            insights.append(f"Primary source type: {most_used[0]}")
        
        return insights
    
    def _identify_gaps(self, findings: List[Finding], query: str) -> List[str]:
        """Identify information gaps."""
        gaps = []
        
        # Check for low confidence areas
        if all(f.confidence < 0.5 for f in findings):
            gaps.append("No high-confidence information available")
        
        # Check for missing source types
        source_types = {f.source.type for f in findings}
        all_types = set(SourceType)
        missing_types = all_types - source_types
        
        if missing_types:
            gaps.append(f"No information from: {', '.join(t.value for t in missing_types)}")
        
        # Check for conflicting information
        conflicts = []
        for i, f1 in enumerate(findings):
            for f2 in findings[i+1:]:
                if f1.contradicting_evidence or f2.contradicting_evidence:
                    conflicts.append((f1, f2))
        
        if conflicts:
            gaps.append(f"Found {len(conflicts)} conflicting pieces of information")
        
        # Check query coverage
        query_terms = set(query.lower().split())
        covered_terms = set()
        
        for finding in findings:
            content_terms = set(finding.content.lower().split())
            covered_terms.update(query_terms.intersection(content_terms))
        
        uncovered = query_terms - covered_terms
        if uncovered:
            gaps.append(f"Limited information on: {', '.join(uncovered)}")
        
        return gaps
    
    def _search_sources(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Search specific sources."""
        query = task.get("query", "")
        sources = task.get("sources", [])
        
        if not query:
            return {"error": "Search query is required"}
        
        results = []
        for source_name in sources:
            source = next((s for s in self.sources if s.name == source_name), None)
            if source:
                findings = self._search_source(source, query, ResearchDepth.MEDIUM)
                results.extend(findings)
        
        return {
            "search_results": results,
            "count": len(results)
        }
    
    def _analyze_findings(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze research findings."""
        findings = task.get("findings", [])
        
        if not findings:
            return {"error": "Findings are required for analysis"}
        
        # Convert to Finding objects if needed
        if isinstance(findings[0], dict):
            findings = [
                Finding(
                    content=f.get("content", ""),
                    source=Source(
                        type=SourceType[f.get("source", {}).get("type", "WEB").upper()],
                        name=f.get("source", {}).get("name", "Unknown")
                    ),
                    relevance=f.get("relevance", 0.5),
                    confidence=f.get("confidence", 0.5)
                )
                for f in findings
            ]
        
        analysis = self._analyze_findings_internal(findings, "")
        
        return {"analysis": analysis}
    
    def _synthesize_information(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Synthesize information from multiple findings."""
        findings = task.get("findings", [])
        
        if not findings:
            return {"error": "Findings are required for synthesis"}
        
        # Group by theme
        themes = {}
        for finding in findings:
            # Simple theme extraction based on tags
            theme = finding.tags[0] if finding.tags else "general"
            if theme not in themes:
                themes[theme] = []
            themes[theme].append(finding)
        
        # Synthesize per theme
        synthesis = {}
        for theme, theme_findings in themes.items():
            synthesis[theme] = {
                "main_points": [f.content[:100] for f in theme_findings[:3]],
                "confidence": sum(f.confidence for f in theme_findings) / len(theme_findings),
                "sources": list(set(f.source.name for f in theme_findings))
            }
        
        return {"synthesis": synthesis}
    
    def _verify_information(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Verify information across sources."""
        claim = task.get("claim", "")
        sources_to_check = task.get("sources", [])
        
        if not claim:
            return {"error": "Claim to verify is required"}
        
        verification_results = []
        
        for source_name in sources_to_check:
            source = next((s for s in self.sources if s.name == source_name), None)
            if source:
                findings = self._search_source(source, claim, ResearchDepth.SHALLOW)
                
                # Check if findings support or contradict claim
                support_score = 0
                for finding in findings:
                    if self._similarity(claim, finding.content) > 0.5:
                        support_score += finding.confidence
                
                verification_results.append({
                    "source": source_name,
                    "support_score": support_score,
                    "findings_count": len(findings)
                })
        
        # Overall verification
        avg_support = sum(v["support_score"] for v in verification_results) / len(verification_results) \
            if verification_results else 0
        
        return {
            "verification": {
                "claim": claim,
                "verified": avg_support > 0.5,
                "confidence": avg_support,
                "source_results": verification_results
            }
        }
    
    def _expand_research(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Expand existing research with additional queries."""
        research_id = task.get("research_id")
        additional_queries = task.get("queries", [])
        
        if not additional_queries:
            return {"error": "Additional queries required for expansion"}
        
        expanded_findings = []
        
        for query in additional_queries:
            result = self._conduct_research({
                "topic": query,
                "depth": ResearchDepth.MEDIUM
            })
            
            if "research_result" in result:
                expanded_findings.extend(result["research_result"].findings)
        
        return {
            "expanded_findings": expanded_findings,
            "queries_processed": len(additional_queries)
        }
    
    def shutdown(self) -> bool:
        """Shutdown the research agent."""
        logger.info("research_agent_shutdown", 
                   cache_size=len(self.cache),
                   history_size=len(self.research_history))
        self.cache.clear()
        self.research_history.clear()
        return True
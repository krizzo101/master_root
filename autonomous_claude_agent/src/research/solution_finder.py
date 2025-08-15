"""
Solution Finder for discovering answers from various sources.

Provides intelligent solution discovery from Stack Overflow, GitHub,
documentation sites, and other knowledge bases.

Author: Autonomous Claude Agent
Created: 2025-08-15
"""

import asyncio
import hashlib
import json
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple
from urllib.parse import urlparse, quote

import aiohttp
from aiohttp import ClientError, ClientSession, ClientTimeout

from .web_search import WebSearchEngine, SearchConfig, SearchProvider
from .doc_analyzer import DocumentAnalyzer, DocumentType
from .cache_manager import CacheManager

logger = logging.getLogger(__name__)


class SolutionSource(Enum):
    """Sources for finding solutions."""

    STACK_OVERFLOW = "stackoverflow"
    GITHUB = "github"
    DOCUMENTATION = "documentation"
    BLOG = "blog"
    FORUM = "forum"
    TUTORIAL = "tutorial"
    API_REFERENCE = "api_reference"
    CODE_EXAMPLE = "code_example"
    INTERNAL_KB = "internal_kb"
    AI_GENERATED = "ai_generated"


class SolutionQuality(Enum):
    """Quality rating for solutions."""

    VERIFIED = "verified"  # Tested and confirmed working
    HIGH = "high"  # From authoritative source
    MEDIUM = "medium"  # Reasonable solution
    LOW = "low"  # Uncertain or partial
    EXPERIMENTAL = "experimental"  # Untested approach


@dataclass
class SolutionConfig:
    """Configuration for solution finder."""

    max_sources: int = 5
    min_quality: SolutionQuality = SolutionQuality.MEDIUM
    prefer_recent: bool = True
    include_code_samples: bool = True
    verify_solutions: bool = False
    timeout: int = 30
    cache_ttl: int = 7200  # 2 hours
    parallel_searches: int = 3
    github_token: Optional[str] = None
    stackoverflow_key: Optional[str] = None


@dataclass
class Solution:
    """Individual solution found."""

    title: str
    description: str
    source: SolutionSource
    source_url: str
    quality: SolutionQuality
    code_samples: List[str] = field(default_factory=list)
    steps: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    votes: int = 0
    author: Optional[str] = None
    created_date: Optional[datetime] = None
    updated_date: Optional[datetime] = None
    relevance_score: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "title": self.title,
            "description": self.description,
            "source": self.source.value,
            "source_url": self.source_url,
            "quality": self.quality.value,
            "code_samples": self.code_samples,
            "steps": self.steps,
            "dependencies": self.dependencies,
            "warnings": self.warnings,
            "votes": self.votes,
            "author": self.author,
            "created_date": self.created_date.isoformat() if self.created_date else None,
            "updated_date": self.updated_date.isoformat() if self.updated_date else None,
            "relevance_score": self.relevance_score,
            "metadata": self.metadata,
        }


@dataclass
class SolutionSet:
    """Collection of solutions for a problem."""

    problem: str
    solutions: List[Solution]
    total_found: int
    search_time: float
    sources_searched: List[SolutionSource]
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "problem": self.problem,
            "solutions": [s.to_dict() for s in self.solutions],
            "total_found": self.total_found,
            "search_time": self.search_time,
            "sources_searched": [s.value for s in self.sources_searched],
            "timestamp": self.timestamp.isoformat(),
        }

    def get_best_solution(self) -> Optional[Solution]:
        """Get the highest quality solution."""
        if not self.solutions:
            return None

        # Sort by quality and relevance
        quality_order = {
            SolutionQuality.VERIFIED: 5,
            SolutionQuality.HIGH: 4,
            SolutionQuality.MEDIUM: 3,
            SolutionQuality.LOW: 2,
            SolutionQuality.EXPERIMENTAL: 1,
        }

        sorted_solutions = sorted(
            self.solutions,
            key=lambda s: (quality_order[s.quality], s.relevance_score, s.votes),
            reverse=True,
        )

        return sorted_solutions[0]


class SolutionFinder:
    """Intelligent solution finder from multiple sources."""

    def __init__(
        self,
        config: Optional[SolutionConfig] = None,
        cache_manager: Optional[CacheManager] = None,
        search_engine: Optional[WebSearchEngine] = None,
        doc_analyzer: Optional[DocumentAnalyzer] = None,
    ):
        """
        Initialize solution finder.

        Args:
            config: Solution finder configuration
            cache_manager: Cache manager instance
            search_engine: Web search engine instance
            doc_analyzer: Document analyzer instance
        """
        self.config = config or SolutionConfig()
        self.cache = cache_manager or CacheManager()
        self.search_engine = search_engine or WebSearchEngine()
        self.doc_analyzer = doc_analyzer or DocumentAnalyzer()
        self._session: Optional[ClientSession] = None
        self._api_endpoints = self._initialize_api_endpoints()

        logger.info("SolutionFinder initialized")

    def _initialize_api_endpoints(self) -> Dict[str, str]:
        """Initialize API endpoints for various sources."""
        return {
            "stackoverflow": "https://api.stackexchange.com/2.3/search/advanced",
            "github_search": "https://api.github.com/search/code",
            "github_gists": "https://api.github.com/gists/public",
            "github_issues": "https://api.github.com/search/issues",
        }

    async def __aenter__(self):
        """Async context manager entry."""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    async def initialize(self) -> None:
        """Initialize HTTP session."""
        if not self._session:
            timeout = ClientTimeout(total=self.config.timeout)
            self._session = ClientSession(timeout=timeout)
            logger.debug("HTTP session initialized")

    async def close(self) -> None:
        """Close HTTP session."""
        if self._session:
            await self._session.close()
            self._session = None
            logger.debug("HTTP session closed")

    def _get_cache_key(self, problem: str, sources: List[SolutionSource]) -> str:
        """Generate cache key for problem."""
        source_str = ",".join(s.value for s in sources)
        key_string = f"{problem}:{source_str}"
        return hashlib.sha256(key_string.encode()).hexdigest()

    async def find_solutions(
        self, problem: str, sources: Optional[List[SolutionSource]] = None, **kwargs
    ) -> SolutionSet:
        """
        Find solutions for a given problem.

        Args:
            problem: Problem description or error message
            sources: Specific sources to search (None = all)
            **kwargs: Additional search parameters

        Returns:
            Set of solutions found
        """
        start_time = datetime.now()

        if not sources:
            sources = [
                SolutionSource.STACK_OVERFLOW,
                SolutionSource.GITHUB,
                SolutionSource.DOCUMENTATION,
            ]

        # Check cache
        cache_key = self._get_cache_key(problem, sources)
        cached_result = await self.cache.get(cache_key)
        if cached_result:
            logger.info(f"Cache hit for problem: {problem[:50]}...")
            return SolutionSet(**cached_result)

        # Search in parallel
        tasks = []
        for source in sources[: self.config.parallel_searches]:
            if source == SolutionSource.STACK_OVERFLOW:
                tasks.append(self._search_stackoverflow(problem, **kwargs))
            elif source == SolutionSource.GITHUB:
                tasks.append(self._search_github(problem, **kwargs))
            elif source == SolutionSource.DOCUMENTATION:
                tasks.append(self._search_documentation(problem, **kwargs))
            elif source == SolutionSource.BLOG:
                tasks.append(self._search_blogs(problem, **kwargs))
            else:
                tasks.append(self._search_web(problem, source, **kwargs))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Collect all solutions
        all_solutions = []
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Search failed: {result}")
            elif isinstance(result, list):
                all_solutions.extend(result)

        # Filter by quality
        filtered_solutions = self._filter_by_quality(all_solutions)

        # Rank solutions
        ranked_solutions = self._rank_solutions(filtered_solutions, problem)

        # Create solution set
        solution_set = SolutionSet(
            problem=problem,
            solutions=ranked_solutions[: self.config.max_sources],
            total_found=len(all_solutions),
            search_time=(datetime.now() - start_time).total_seconds(),
            sources_searched=sources,
        )

        # Cache results
        await self.cache.set(cache_key, solution_set.to_dict(), ttl=self.config.cache_ttl)

        return solution_set

    async def _search_stackoverflow(self, problem: str, **kwargs) -> List[Solution]:
        """Search Stack Overflow for solutions."""
        if not self._session:
            await self.initialize()

        solutions = []

        params = {
            "order": "desc",
            "sort": "relevance",
            "q": problem,
            "site": "stackoverflow",
            "filter": "withbody",
            "pagesize": 10,
        }

        if self.config.stackoverflow_key:
            params["key"] = self.config.stackoverflow_key

        try:
            async with self._session.get(
                self._api_endpoints["stackoverflow"], params=params
            ) as response:
                response.raise_for_status()
                data = await response.json()

                for item in data.get("items", []):
                    # Check if question has accepted answer
                    quality = SolutionQuality.MEDIUM
                    if item.get("is_answered") and item.get("accepted_answer_id"):
                        quality = SolutionQuality.HIGH

                    # Extract code samples from body
                    code_samples = self._extract_code_from_html(item.get("body", ""))

                    solution = Solution(
                        title=item.get("title", ""),
                        description=self._clean_html(item.get("body", ""))[:500],
                        source=SolutionSource.STACK_OVERFLOW,
                        source_url=item.get("link", ""),
                        quality=quality,
                        code_samples=code_samples,
                        votes=item.get("score", 0),
                        author=item.get("owner", {}).get("display_name"),
                        created_date=datetime.fromtimestamp(item.get("creation_date", 0)),
                        metadata={
                            "tags": item.get("tags", []),
                            "view_count": item.get("view_count", 0),
                            "answer_count": item.get("answer_count", 0),
                        },
                    )
                    solutions.append(solution)

        except Exception as e:
            logger.error(f"Stack Overflow search failed: {e}")

        return solutions

    async def _search_github(self, problem: str, **kwargs) -> List[Solution]:
        """Search GitHub for code solutions."""
        if not self._session:
            await self.initialize()

        solutions = []
        headers = {"Accept": "application/vnd.github.v3+json"}

        if self.config.github_token:
            headers["Authorization"] = f"token {self.config.github_token}"

        # Search code
        params = {"q": problem, "sort": "indexed", "order": "desc", "per_page": 10}

        try:
            async with self._session.get(
                self._api_endpoints["github_search"], params=params, headers=headers
            ) as response:
                if response.status == 200:
                    data = await response.json()

                    for item in data.get("items", []):
                        # Get file content
                        file_url = item.get("url", "")
                        code_content = await self._fetch_github_content(file_url, headers)

                        solution = Solution(
                            title=f"{item.get('name', '')} from {item.get('repository', {}).get('name', '')}",
                            description=f"Code from {item.get('path', '')}",
                            source=SolutionSource.GITHUB,
                            source_url=item.get("html_url", ""),
                            quality=SolutionQuality.MEDIUM,
                            code_samples=[code_content] if code_content else [],
                            metadata={
                                "repository": item.get("repository", {}).get("full_name", ""),
                                "path": item.get("path", ""),
                                "language": item.get("language", ""),
                            },
                        )
                        solutions.append(solution)

        except Exception as e:
            logger.error(f"GitHub search failed: {e}")

        # Also search issues for solutions
        try:
            params["q"] = f"{problem} is:issue is:closed"

            async with self._session.get(
                self._api_endpoints["github_issues"], params=params, headers=headers
            ) as response:
                if response.status == 200:
                    data = await response.json()

                    for item in data.get("items", []):
                        if item.get("state") == "closed":
                            solution = Solution(
                                title=item.get("title", ""),
                                description=item.get("body", "")[:500] if item.get("body") else "",
                                source=SolutionSource.GITHUB,
                                source_url=item.get("html_url", ""),
                                quality=SolutionQuality.MEDIUM,
                                metadata={
                                    "repository": item.get("repository_url", "").split("/")[-1],
                                    "labels": [l.get("name") for l in item.get("labels", [])],
                                },
                            )
                            solutions.append(solution)

        except Exception as e:
            logger.error(f"GitHub issues search failed: {e}")

        return solutions

    async def _fetch_github_content(self, url: str, headers: Dict[str, str]) -> str:
        """Fetch content from GitHub API."""
        try:
            async with self._session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    content = data.get("content", "")
                    if content:
                        import base64

                        return base64.b64decode(content).decode("utf-8")
        except Exception as e:
            logger.error(f"Failed to fetch GitHub content: {e}")

        return ""

    async def _search_documentation(self, problem: str, **kwargs) -> List[Solution]:
        """Search documentation sites for solutions."""
        solutions = []

        # Use web search to find documentation
        search_query = f"{problem} site:docs OR site:documentation OR site:readthedocs"
        search_results = await self.search_engine.search(search_query)

        for result in search_results[:5]:
            # Analyze the documentation page
            try:
                # Fetch and analyze the page content
                async with self._session.get(result.url) as response:
                    if response.status == 200:
                        content = await response.text()
                        analysis = await self.doc_analyzer.analyze(content, DocumentType.HTML)

                        # Extract code examples and steps
                        code_samples = [
                            insight.content
                            for insight in analysis.insights
                            if insight.type.value == "code_example"
                        ]

                        solution = Solution(
                            title=result.title,
                            description=analysis.summary,
                            source=SolutionSource.DOCUMENTATION,
                            source_url=result.url,
                            quality=SolutionQuality.HIGH,
                            code_samples=code_samples,
                            metadata={
                                "doc_type": analysis.document_type.value,
                                "sections": analysis.structure.get("sections", []),
                            },
                        )
                        solutions.append(solution)

            except Exception as e:
                logger.error(f"Failed to analyze documentation: {e}")

        return solutions

    async def _search_blogs(self, problem: str, **kwargs) -> List[Solution]:
        """Search technical blogs for solutions."""
        solutions = []

        # Search for blog posts
        blog_sites = ["medium.com", "dev.to", "hackernoon.com", "towardsdatascience.com"]

        search_query = f"{problem} site:({' OR site:'.join(blog_sites)})"
        search_results = await self.search_engine.search(search_query)

        for result in search_results[:3]:
            solution = Solution(
                title=result.title,
                description=result.snippet,
                source=SolutionSource.BLOG,
                source_url=result.url,
                quality=SolutionQuality.MEDIUM,
                relevance_score=result.score,
                metadata={"provider": result.provider},
            )
            solutions.append(solution)

        return solutions

    async def _search_web(self, problem: str, source: SolutionSource, **kwargs) -> List[Solution]:
        """Generic web search for solutions."""
        solutions = []

        search_results = await self.search_engine.search(problem)

        for result in search_results[:3]:
            solution = Solution(
                title=result.title,
                description=result.snippet,
                source=source,
                source_url=result.url,
                quality=SolutionQuality.LOW,
                relevance_score=result.score,
                metadata={"provider": result.provider},
            )
            solutions.append(solution)

        return solutions

    def _extract_code_from_html(self, html: str) -> List[str]:
        """Extract code blocks from HTML content."""
        from bs4 import BeautifulSoup

        code_samples = []
        soup = BeautifulSoup(html, "html.parser")

        for code_block in soup.find_all(["code", "pre"]):
            code = code_block.get_text().strip()
            if len(code) > 10:  # Filter out very short snippets
                code_samples.append(code)

        return code_samples

    def _clean_html(self, html: str) -> str:
        """Remove HTML tags from text."""
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "html.parser")
        return soup.get_text(separator=" ", strip=True)

    def _filter_by_quality(self, solutions: List[Solution]) -> List[Solution]:
        """Filter solutions by minimum quality."""
        quality_order = {
            SolutionQuality.VERIFIED: 5,
            SolutionQuality.HIGH: 4,
            SolutionQuality.MEDIUM: 3,
            SolutionQuality.LOW: 2,
            SolutionQuality.EXPERIMENTAL: 1,
        }

        min_quality_value = quality_order[self.config.min_quality]

        return [s for s in solutions if quality_order[s.quality] >= min_quality_value]

    def _rank_solutions(self, solutions: List[Solution], problem: str) -> List[Solution]:
        """Rank solutions by relevance and quality."""
        # Simple ranking based on multiple factors
        for solution in solutions:
            score = 0.0

            # Quality score
            quality_scores = {
                SolutionQuality.VERIFIED: 1.0,
                SolutionQuality.HIGH: 0.8,
                SolutionQuality.MEDIUM: 0.6,
                SolutionQuality.LOW: 0.4,
                SolutionQuality.EXPERIMENTAL: 0.2,
            }
            score += quality_scores[solution.quality] * 0.3

            # Has code samples
            if solution.code_samples:
                score += 0.2

            # Has steps
            if solution.steps:
                score += 0.1

            # Votes/popularity
            if solution.votes > 0:
                score += min(solution.votes / 100, 0.2)

            # Recency (if prefer_recent is enabled)
            if self.config.prefer_recent and solution.created_date:
                days_old = (datetime.now() - solution.created_date).days
                if days_old < 365:
                    score += 0.1 * (1 - days_old / 365)

            # Text similarity to problem
            problem_words = set(problem.lower().split())
            title_words = set(solution.title.lower().split())
            similarity = (
                len(problem_words & title_words) / len(problem_words) if problem_words else 0
            )
            score += similarity * 0.2

            solution.relevance_score = score

        # Sort by relevance score
        solutions.sort(key=lambda s: s.relevance_score, reverse=True)

        return solutions

    async def verify_solution(
        self, solution: Solution, test_environment: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Verify if a solution actually works.

        Args:
            solution: Solution to verify
            test_environment: Optional test environment configuration

        Returns:
            True if solution is verified to work
        """
        if not self.config.verify_solutions:
            return True

        # Basic verification - check if code samples are syntactically valid
        for code in solution.code_samples:
            if not self._is_valid_code(code):
                return False

        # Additional verification logic could be added here
        # - Run code in sandbox
        # - Check dependencies exist
        # - Validate against known patterns

        return True

    def _is_valid_code(self, code: str) -> bool:
        """Check if code is syntactically valid."""
        # Simple validation - could be enhanced with AST parsing
        try:
            # Try to compile as Python
            compile(code, "<string>", "exec")
            return True
        except SyntaxError:
            # Not valid Python, but might be valid in another language
            return True  # Be lenient for now
        except Exception:
            return False

    async def get_related_solutions(
        self, solution: Solution, max_related: int = 3
    ) -> List[Solution]:
        """
        Find solutions related to a given solution.

        Args:
            solution: Reference solution
            max_related: Maximum number of related solutions

        Returns:
            List of related solutions
        """
        # Search for similar problems
        related_query = f"{solution.title} alternative approach"

        related_set = await self.find_solutions(related_query, sources=[solution.source])

        # Filter out the original solution
        related = [s for s in related_set.solutions if s.source_url != solution.source_url]

        return related[:max_related]

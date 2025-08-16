"""
Research Module for Autonomous Claude Agent.

This module provides comprehensive research capabilities including web search,
documentation analysis, solution finding, and intelligent caching.

Author: Autonomous Claude Agent
Created: 2025-08-15
"""

from .web_search import WebSearchEngine, SearchResult, SearchConfig
from .doc_analyzer import DocumentAnalyzer, DocumentInsight, AnalysisConfig
from .solution_finder import SolutionFinder, Solution, SolutionSource
from .cache_manager import CacheManager, CacheConfig, CacheEntry

__version__ = "1.0.0"

__all__ = [
    # Web Search
    "WebSearchEngine",
    "SearchResult",
    "SearchConfig",
    # Document Analysis
    "DocumentAnalyzer",
    "DocumentInsight",
    "AnalysisConfig",
    # Solution Finding
    "SolutionFinder",
    "Solution",
    "SolutionSource",
    # Cache Management
    "CacheManager",
    "CacheConfig",
    "CacheEntry",
]

# Module-level configuration defaults
DEFAULT_CACHE_TTL = 3600  # 1 hour
DEFAULT_MAX_RETRIES = 3
DEFAULT_TIMEOUT = 30  # seconds
DEFAULT_RATE_LIMIT = 10  # requests per minute

"""
Web Search Engine with Caching and Rate Limiting.

Provides async web search capabilities with intelligent caching,
rate limiting, and result ranking.

Author: Autonomous Claude Agent
Created: 2025-08-15
"""

import asyncio
import hashlib
import json
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple
from urllib.parse import quote, urljoin

import aiohttp
from aiohttp import ClientError, ClientSession, ClientTimeout

from .cache_manager import CacheManager

logger = logging.getLogger(__name__)


class SearchProvider(Enum):
    """Supported search providers."""
    BRAVE = "brave"
    GOOGLE = "google"
    DUCKDUCKGO = "duckduckgo"
    BING = "bing"
    INTERNAL = "internal"  # For searching internal documentation


@dataclass
class SearchConfig:
    """Configuration for web search engine."""
    provider: SearchProvider = SearchProvider.BRAVE
    api_key: Optional[str] = None
    max_results: int = 10
    timeout: int = 30
    cache_ttl: int = 3600  # 1 hour
    rate_limit: int = 10  # requests per minute
    retry_count: int = 3
    retry_delay: float = 1.0
    user_agent: str = "AutonomousClaudeAgent/1.0"
    proxy: Optional[str] = None
    verify_ssl: bool = True


@dataclass
class SearchResult:
    """Individual search result."""
    title: str
    url: str
    snippet: str
    score: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)
    provider: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "title": self.title,
            "url": self.url,
            "snippet": self.snippet,
            "score": self.score,
            "timestamp": self.timestamp.isoformat(),
            "provider": self.provider,
            "metadata": self.metadata
        }


class RateLimiter:
    """Token bucket rate limiter."""
    
    def __init__(self, rate: int, per: float = 60.0):
        """
        Initialize rate limiter.
        
        Args:
            rate: Number of allowed requests
            per: Time period in seconds (default 60)
        """
        self.rate = rate
        self.per = per
        self.allowance = rate
        self.last_check = time.monotonic()
        self._lock = asyncio.Lock()
    
    async def acquire(self) -> None:
        """Acquire permission to make a request."""
        async with self._lock:
            current = time.monotonic()
            time_passed = current - self.last_check
            self.last_check = current
            
            # Replenish tokens
            self.allowance += time_passed * (self.rate / self.per)
            if self.allowance > self.rate:
                self.allowance = self.rate
            
            # Wait if necessary
            if self.allowance < 1.0:
                sleep_time = (1.0 - self.allowance) * (self.per / self.rate)
                await asyncio.sleep(sleep_time)
                self.allowance = 0.0
            else:
                self.allowance -= 1.0


class WebSearchEngine:
    """Async web search engine with caching and rate limiting."""
    
    def __init__(
        self,
        config: Optional[SearchConfig] = None,
        cache_manager: Optional[CacheManager] = None
    ):
        """
        Initialize web search engine.
        
        Args:
            config: Search configuration (SearchConfig object or dict)
            cache_manager: Cache manager instance
        """
        # Handle both SearchConfig and dict
        if isinstance(config, dict):
            # Filter only valid SearchConfig fields from dict
            valid_fields = {
                'provider', 'api_key', 'max_results', 'timeout', 
                'cache_ttl', 'rate_limit', 'retry_count', 'retry_delay',
                'user_agent', 'proxy', 'verify_ssl'
            }
            filtered_config = {k: v for k, v in config.items() if k in valid_fields}
            self.config = SearchConfig(**filtered_config) if filtered_config else SearchConfig()
        else:
            self.config = config or SearchConfig()
        
        self.cache = cache_manager or CacheManager()
        self.rate_limiter = RateLimiter(
            self.config.rate_limit,
            per=60.0
        )
        self._session: Optional[ClientSession] = None
        self._providers: Dict[SearchProvider, Any] = {}
        self._initialize_providers()
        
        logger.info(f"WebSearchEngine initialized with provider: {self.config.provider}")
    
    def _initialize_providers(self) -> None:
        """Initialize search provider configurations."""
        self._providers = {
            SearchProvider.BRAVE: {
                "base_url": "https://api.search.brave.com/res/v1/web/search",
                "headers": {
                    "X-Subscription-Token": self.config.api_key or "",
                    "Accept": "application/json"
                }
            },
            SearchProvider.DUCKDUCKGO: {
                "base_url": "https://api.duckduckgo.com/",
                "headers": {"Accept": "application/json"}
            },
            SearchProvider.GOOGLE: {
                "base_url": "https://www.googleapis.com/customsearch/v1",
                "headers": {"Accept": "application/json"}
            },
            SearchProvider.BING: {
                "base_url": "https://api.bing.microsoft.com/v7.0/search",
                "headers": {
                    "Ocp-Apim-Subscription-Key": self.config.api_key or "",
                    "Accept": "application/json"
                }
            }
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
            connector = aiohttp.TCPConnector(
                limit=100,
                verify_ssl=self.config.verify_ssl
            )
            self._session = ClientSession(
                timeout=timeout,
                connector=connector,
                headers={"User-Agent": self.config.user_agent}
            )
            logger.debug("HTTP session initialized")
    
    async def close(self) -> None:
        """Close HTTP session."""
        if self._session:
            await self._session.close()
            self._session = None
            logger.debug("HTTP session closed")
    
    def _get_cache_key(self, query: str, **kwargs) -> str:
        """Generate cache key for search query."""
        key_parts = [
            str(self.config.provider.value),
            query,
            str(self.config.max_results)
        ]
        key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
        key_string = "|".join(key_parts)
        return hashlib.sha256(key_string.encode()).hexdigest()
    
    async def search(
        self,
        query: str,
        **kwargs
    ) -> List[SearchResult]:
        """
        Perform web search with caching and rate limiting.
        
        Args:
            query: Search query
            **kwargs: Additional search parameters
            
        Returns:
            List of search results
        """
        if not query.strip():
            logger.warning("Empty search query provided")
            return []
        
        # Check cache
        cache_key = self._get_cache_key(query, **kwargs)
        cached_results = await self.cache.get(cache_key)
        if cached_results:
            logger.info(f"Cache hit for query: {query}")
            return [SearchResult(**r) for r in cached_results]
        
        # Rate limiting
        await self.rate_limiter.acquire()
        
        # Perform search
        try:
            results = await self._perform_search(query, **kwargs)
            
            # Cache results
            if results:
                cache_data = [r.to_dict() for r in results]
                await self.cache.set(cache_key, cache_data, ttl=self.config.cache_ttl)
                logger.info(f"Cached {len(results)} results for query: {query}")
            
            return results
            
        except Exception as e:
            logger.error(f"Search failed for query '{query}': {e}")
            return []
    
    async def _perform_search(
        self,
        query: str,
        **kwargs
    ) -> List[SearchResult]:
        """
        Perform actual search request.
        
        Args:
            query: Search query
            **kwargs: Additional parameters
            
        Returns:
            List of search results
        """
        if not self._session:
            await self.initialize()
        
        provider_config = self._providers.get(self.config.provider)
        if not provider_config:
            raise ValueError(f"Unsupported provider: {self.config.provider}")
        
        # Build request based on provider
        if self.config.provider == SearchProvider.BRAVE:
            results = await self._search_brave(query, **kwargs)
        elif self.config.provider == SearchProvider.DUCKDUCKGO:
            results = await self._search_duckduckgo(query, **kwargs)
        elif self.config.provider == SearchProvider.GOOGLE:
            results = await self._search_google(query, **kwargs)
        elif self.config.provider == SearchProvider.BING:
            results = await self._search_bing(query, **kwargs)
        else:
            results = []
        
        # Rank results
        return self._rank_results(results)
    
    async def _search_brave(
        self,
        query: str,
        **kwargs
    ) -> List[SearchResult]:
        """Search using Brave API."""
        provider_config = self._providers[SearchProvider.BRAVE]
        
        params = {
            "q": query,
            "count": self.config.max_results,
            **kwargs
        }
        
        headers = provider_config["headers"].copy()
        
        try:
            async with self._session.get(
                provider_config["base_url"],
                params=params,
                headers=headers
            ) as response:
                response.raise_for_status()
                data = await response.json()
                
                results = []
                for item in data.get("web", {}).get("results", []):
                    result = SearchResult(
                        title=item.get("title", ""),
                        url=item.get("url", ""),
                        snippet=item.get("description", ""),
                        score=item.get("relevance_score", 0.0),
                        provider=self.config.provider.value,
                        metadata={
                            "age": item.get("age", ""),
                            "language": item.get("language", "")
                        }
                    )
                    results.append(result)
                
                return results
                
        except ClientError as e:
            logger.error(f"Brave search API error: {e}")
            return []
    
    async def _search_duckduckgo(
        self,
        query: str,
        **kwargs
    ) -> List[SearchResult]:
        """Search using DuckDuckGo API."""
        provider_config = self._providers[SearchProvider.DUCKDUCKGO]
        
        params = {
            "q": query,
            "format": "json",
            "no_html": "1",
            **kwargs
        }
        
        try:
            async with self._session.get(
                provider_config["base_url"],
                params=params,
                headers=provider_config["headers"]
            ) as response:
                response.raise_for_status()
                data = await response.json()
                
                results = []
                for item in data.get("RelatedTopics", [])[:self.config.max_results]:
                    if isinstance(item, dict) and "Text" in item:
                        result = SearchResult(
                            title=item.get("Text", "").split(" - ")[0],
                            url=item.get("FirstURL", ""),
                            snippet=item.get("Text", ""),
                            provider=self.config.provider.value
                        )
                        results.append(result)
                
                return results
                
        except ClientError as e:
            logger.error(f"DuckDuckGo search API error: {e}")
            return []
    
    async def _search_google(
        self,
        query: str,
        **kwargs
    ) -> List[SearchResult]:
        """Search using Google Custom Search API."""
        # Implementation requires Google API key and Custom Search Engine ID
        logger.warning("Google search not fully implemented")
        return []
    
    async def _search_bing(
        self,
        query: str,
        **kwargs
    ) -> List[SearchResult]:
        """Search using Bing API."""
        provider_config = self._providers[SearchProvider.BING]
        
        params = {
            "q": query,
            "count": self.config.max_results,
            **kwargs
        }
        
        headers = provider_config["headers"].copy()
        
        try:
            async with self._session.get(
                provider_config["base_url"],
                params=params,
                headers=headers
            ) as response:
                response.raise_for_status()
                data = await response.json()
                
                results = []
                for item in data.get("webPages", {}).get("value", []):
                    result = SearchResult(
                        title=item.get("name", ""),
                        url=item.get("url", ""),
                        snippet=item.get("snippet", ""),
                        provider=self.config.provider.value,
                        metadata={
                            "dateLastCrawled": item.get("dateLastCrawled", ""),
                            "language": item.get("language", "")
                        }
                    )
                    results.append(result)
                
                return results
                
        except ClientError as e:
            logger.error(f"Bing search API error: {e}")
            return []
    
    def _rank_results(self, results: List[SearchResult]) -> List[SearchResult]:
        """
        Rank search results by relevance.
        
        Args:
            results: List of search results
            
        Returns:
            Ranked list of results
        """
        # Simple ranking by score if available
        if results and results[0].score > 0:
            results.sort(key=lambda x: x.score, reverse=True)
        
        return results
    
    async def batch_search(
        self,
        queries: List[str],
        **kwargs
    ) -> Dict[str, List[SearchResult]]:
        """
        Perform multiple searches in parallel.
        
        Args:
            queries: List of search queries
            **kwargs: Additional parameters
            
        Returns:
            Dictionary mapping queries to results
        """
        tasks = [
            self.search(query, **kwargs)
            for query in queries
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        output = {}
        for query, result in zip(queries, results):
            if isinstance(result, Exception):
                logger.error(f"Batch search failed for '{query}': {result}")
                output[query] = []
            else:
                output[query] = result
        
        return output
    
    async def search_with_retry(
        self,
        query: str,
        **kwargs
    ) -> List[SearchResult]:
        """
        Search with automatic retry on failure.
        
        Args:
            query: Search query
            **kwargs: Additional parameters
            
        Returns:
            List of search results
        """
        last_error = None
        
        for attempt in range(self.config.retry_count):
            try:
                return await self.search(query, **kwargs)
            except Exception as e:
                last_error = e
                if attempt < self.config.retry_count - 1:
                    delay = self.config.retry_delay * (2 ** attempt)
                    logger.warning(
                        f"Search attempt {attempt + 1} failed, "
                        f"retrying in {delay}s: {e}"
                    )
                    await asyncio.sleep(delay)
        
        logger.error(f"All search attempts failed for '{query}': {last_error}")
        return []
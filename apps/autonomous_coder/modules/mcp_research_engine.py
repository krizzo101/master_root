"""Enhanced Research Engine with MCP Integration."""

import json
import re
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict, field
from enum import Enum
import hashlib
from collections import OrderedDict

from core.base import BaseModule, TechInfo


class MCPService(Enum):
    """Available MCP services."""
    BRAVE_SEARCH = "brave_search"
    FIRECRAWL = "firecrawl"
    CONTEXT7 = "context7"


@dataclass
class MCPResponse:
    """Normalized response from MCP services."""
    success: bool
    data: Any
    source: MCPService
    timestamp: datetime
    error: Optional[str] = None
    latency_ms: float = 0.0


@dataclass
class VersionInfo:
    """Structured version information."""
    version: str
    release_date: Optional[datetime] = None
    is_stable: bool = True
    is_lts: bool = False
    source: str = ""
    confidence: float = 1.0


class CircuitBreaker:
    """Circuit breaker for fault tolerance."""
    
    def __init__(self, failure_threshold: int = 5, timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failures = 0
        self.last_failure_time = None
        self.state = "closed"  # closed, open, half-open
    
    def is_open(self) -> bool:
        """Check if circuit is open."""
        if self.state == "open":
            if self.last_failure_time:
                if datetime.now() - self.last_failure_time > timedelta(seconds=self.timeout):
                    self.state = "half-open"
                    return False
            return True
        return False
    
    def record_success(self):
        """Record successful call."""
        self.failures = 0
        self.state = "closed"
    
    def record_failure(self):
        """Record failed call."""
        self.failures += 1
        self.last_failure_time = datetime.now()
        if self.failures >= self.failure_threshold:
            self.state = "open"


class MultiTierCache:
    """Multi-tier caching system."""
    
    def __init__(self, memory_size: int = 100, cache_dir: Path = Path(".cache")):
        self.memory_cache = OrderedDict()
        self.memory_size = memory_size
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(exist_ok=True)
    
    def _get_cache_key(self, key: str) -> str:
        """Generate cache key."""
        return hashlib.md5(key.encode()).hexdigest()
    
    async def get(self, key: str, ttl: int = 3600) -> Optional[Dict]:
        """Get from cache with TTL check."""
        # Check memory cache
        if key in self.memory_cache:
            entry = self.memory_cache[key]
            if datetime.now() - entry["timestamp"] < timedelta(seconds=ttl):
                # Move to end (LRU)
                self.memory_cache.move_to_end(key)
                return entry["data"]
            else:
                del self.memory_cache[key]
        
        # Check disk cache
        cache_file = self.cache_dir / f"{self._get_cache_key(key)}.json"
        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    entry = json.load(f)
                
                cached_time = datetime.fromisoformat(entry["timestamp"])
                if datetime.now() - cached_time < timedelta(seconds=ttl):
                    # Promote to memory cache
                    self._add_to_memory(key, entry["data"])
                    return entry["data"]
                else:
                    cache_file.unlink()
            except:
                pass
        
        return None
    
    async def set(self, key: str, value: Dict):
        """Set cache value."""
        # Add to memory cache
        self._add_to_memory(key, value)
        
        # Write to disk cache
        cache_file = self.cache_dir / f"{self._get_cache_key(key)}.json"
        entry = {
            "timestamp": datetime.now().isoformat(),
            "data": value
        }
        
        with open(cache_file, 'w') as f:
            json.dump(entry, f, indent=2, default=str)
    
    def _add_to_memory(self, key: str, value: Dict):
        """Add to memory cache with LRU eviction."""
        if key in self.memory_cache:
            self.memory_cache.move_to_end(key)
        else:
            if len(self.memory_cache) >= self.memory_size:
                # Evict oldest
                self.memory_cache.popitem(last=False)
        
        self.memory_cache[key] = {
            "timestamp": datetime.now(),
            "data": value
        }


class MCPAdapter:
    """Base adapter for MCP services."""
    
    def __init__(self, service: MCPService, timeout: int = 30, max_retries: int = 3):
        self.service = service
        self.timeout = timeout
        self.max_retries = max_retries
        self.circuit_breaker = CircuitBreaker()
    
    async def execute(self, **kwargs) -> MCPResponse:
        """Execute with retry and circuit breaker."""
        start_time = datetime.now()
        
        if self.circuit_breaker.is_open():
            return MCPResponse(
                success=False,
                data=None,
                source=self.service,
                timestamp=datetime.now(),
                error="Circuit breaker open"
            )
        
        for attempt in range(self.max_retries):
            try:
                result = await asyncio.wait_for(
                    self._call(**kwargs),
                    timeout=self.timeout
                )
                
                self.circuit_breaker.record_success()
                latency = (datetime.now() - start_time).total_seconds() * 1000
                
                return MCPResponse(
                    success=True,
                    data=self._normalize(result),
                    source=self.service,
                    timestamp=datetime.now(),
                    latency_ms=latency
                )
                
            except asyncio.TimeoutError:
                error = f"Timeout after {self.timeout}s"
            except Exception as e:
                error = str(e)
            
            if attempt < self.max_retries - 1:
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
        
        self.circuit_breaker.record_failure()
        latency = (datetime.now() - start_time).total_seconds() * 1000
        
        return MCPResponse(
            success=False,
            data=None,
            source=self.service,
            timestamp=datetime.now(),
            error=error,
            latency_ms=latency
        )
    
    async def _call(self, **kwargs) -> Any:
        """Override in subclasses."""
        raise NotImplementedError
    
    def _normalize(self, response: Any) -> Any:
        """Override in subclasses."""
        return response


class BraveSearchAdapter(MCPAdapter):
    """Adapter for Brave Search MCP."""
    
    def __init__(self):
        super().__init__(MCPService.BRAVE_SEARCH)
    
    async def _call(self, query: str, count: int = 10, 
                    freshness: Optional[str] = None, **kwargs) -> Any:
        """Call Brave Search MCP."""
        try:
            # Import dynamically to avoid issues if not available
            from mcp__mcp_web_search import brave_web_search
            return await brave_web_search(
                query=query,
                count=count,
                freshness=freshness
            )
        except ImportError:
            # Fallback to mock for testing
            return self._mock_search(query, count)
    
    def _normalize(self, response: Any) -> List[Dict]:
        """Normalize Brave search results."""
        if not response:
            return []
        
        normalized = []
        for result in response:
            if isinstance(result, dict):
                normalized.append({
                    "title": result.get("Title", ""),
                    "url": result.get("URL", ""),
                    "description": self._clean_html(result.get("Description", "")),
                    "source": "brave"
                })
        
        return normalized
    
    def _clean_html(self, text: str) -> str:
        """Remove HTML tags from text."""
        return re.sub(r'<[^>]+>', '', text)
    
    def _mock_search(self, query: str, count: int) -> List[Dict]:
        """Mock search for testing."""
        return [
            {
                "Title": f"Result for {query}",
                "URL": f"https://example.com/{i}",
                "Description": f"Mock result {i} for query: {query}"
            }
            for i in range(min(count, 3))
        ]


class FirecrawlAdapter(MCPAdapter):
    """Adapter for Firecrawl MCP."""
    
    def __init__(self):
        super().__init__(MCPService.FIRECRAWL)
    
    async def _call(self, url: str, formats: List[str] = ["markdown"],
                    only_main_content: bool = True, **kwargs) -> Any:
        """Call Firecrawl MCP."""
        try:
            from mcp__firecrawl import firecrawl_scrape
            return await firecrawl_scrape(
                url=url,
                formats=formats,
                onlyMainContent=only_main_content
            )
        except ImportError:
            # Fallback to mock
            return self._mock_scrape(url)
    
    def _normalize(self, response: Any) -> str:
        """Extract markdown content."""
        if isinstance(response, str):
            return response
        elif isinstance(response, dict):
            return response.get("markdown", response.get("content", ""))
        return ""
    
    def _mock_scrape(self, url: str) -> str:
        """Mock scrape for testing."""
        return f"# Mock Content\n\nScraped from {url}\n\nVersion: 1.0.0\nRelease Date: 2025-01-15"


class Context7Adapter(MCPAdapter):
    """Adapter for Context7/Tech Docs MCP."""
    
    def __init__(self):
        super().__init__(MCPService.CONTEXT7)
    
    async def resolve_library(self, library_name: str) -> Optional[Dict]:
        """Resolve library name to Context7 ID."""
        try:
            from mcp__tech_docs import resolve_library_id
            result = await resolve_library_id(libraryName=library_name)
            return self._parse_library_results(result)
        except ImportError:
            return self._mock_resolve(library_name)
    
    async def get_docs(self, library_id: str, topic: str = "", 
                      tokens: int = 2000) -> Optional[str]:
        """Get documentation for library."""
        try:
            from mcp__tech_docs import get_library_docs
            result = await get_library_docs(
                context7CompatibleLibraryID=library_id,
                topic=topic,
                tokens=tokens
            )
            return result
        except ImportError:
            return self._mock_docs(library_id, topic)
    
    async def _call(self, operation: str, **kwargs) -> Any:
        """Route to appropriate method."""
        if operation == "resolve":
            return await self.resolve_library(kwargs.get("library_name", ""))
        elif operation == "get_docs":
            return await self.get_docs(
                kwargs.get("library_id", ""),
                kwargs.get("topic", ""),
                kwargs.get("tokens", 2000)
            )
        return None
    
    def _normalize(self, response: Any) -> Any:
        """Pass through normalization."""
        return response
    
    def _parse_library_results(self, result: str) -> Optional[Dict]:
        """Parse library resolution results."""
        if not result:
            return None
        
        # Parse the text format response
        libraries = []
        current = {}
        
        for line in result.split('\n'):
            if line.startswith('- Title:'):
                if current:
                    libraries.append(current)
                current = {"title": line.replace('- Title:', '').strip()}
            elif line.startswith('- Context7-compatible library ID:'):
                current["id"] = line.replace('- Context7-compatible library ID:', '').strip()
            elif line.startswith('- Trust Score:'):
                try:
                    current["trust_score"] = float(line.replace('- Trust Score:', '').strip())
                except:
                    current["trust_score"] = 0
            elif line.startswith('- Code Snippets:'):
                try:
                    current["snippets"] = int(line.replace('- Code Snippets:', '').strip())
                except:
                    current["snippets"] = 0
        
        if current:
            libraries.append(current)
        
        # Select best match
        if libraries:
            return max(libraries, key=lambda x: (x.get("trust_score", 0), x.get("snippets", 0)))
        
        return None
    
    def _mock_resolve(self, library_name: str) -> Dict:
        """Mock library resolution."""
        return {
            "id": f"/mock/{library_name.lower()}",
            "title": library_name,
            "trust_score": 8.0,
            "snippets": 100
        }
    
    def _mock_docs(self, library_id: str, topic: str) -> str:
        """Mock documentation."""
        return f"# {library_id} Documentation\n\n## {topic}\n\nLatest version: 1.0.0"


class MCPResearchEngine(BaseModule):
    """Enhanced research engine with MCP integration."""
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize the research engine."""
        super().__init__(config)
        
        # Initialize adapters
        self.brave = BraveSearchAdapter()
        self.firecrawl = FirecrawlAdapter()
        self.context7 = Context7Adapter()
        
        # Initialize cache
        self.cache = MultiTierCache()
        
        # Fallback data (same as original)
        self.fallback_versions = {
            "react": "19.1.1",
            "vue": "3.5.13",
            "angular": "19.0.0",
            "nextjs": "15.2.0",
            "vite": "7.1.1",
            "typescript": "5.7.2",
            "nodejs": "22.13.0",
            "python": "3.13.1",
            "fastapi": "0.117.1",
            # ... include all original versions
        }
    
    async def research_technology(self, name: str) -> TechInfo:
        """Research technology with MCP services."""
        self.log(f"Researching technology: {name}")
        
        # Check cache first
        cache_key = f"tech_{name.lower()}"
        cached = await self.cache.get(cache_key, ttl=3600)
        if cached:
            self.log(f"Using cached data for {name}")
            return TechInfo(**cached)
        
        # Try MCP services
        try:
            version_info = await self._discover_version(name)
            best_practices = await self._discover_best_practices(name)
            deprecations = await self._check_deprecations(name)
            doc_url = await self._find_documentation_url(name)
            
            tech_info = TechInfo(
                name=name,
                version=version_info.version if version_info else "latest",
                latest_stable=version_info.version if version_info else "latest",
                release_date=version_info.release_date if version_info else datetime.now(),
                best_practices=best_practices[:5],  # Top 5
                deprecations=deprecations,
                documentation_url=doc_url or f"https://www.google.com/search?q={name}+documentation"
            )
            
            # Cache the result
            await self.cache.set(cache_key, asdict(tech_info))
            
            return tech_info
            
        except Exception as e:
            self.log(f"MCP research failed for {name}: {e}, using fallback")
            return self._get_fallback_info(name)
    
    async def _discover_version(self, name: str) -> Optional[VersionInfo]:
        """Discover version using multiple sources."""
        tasks = []
        
        # Strategy 1: Search for latest version
        tasks.append(self._search_version(name))
        
        # Strategy 2: Check Context7 documentation
        tasks.append(self._context7_version(name))
        
        # Strategy 3: Scrape official site if known
        if official_url := self._get_official_url(name):
            tasks.append(self._scrape_version(official_url, name))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Select best result
        valid_results = [r for r in results if isinstance(r, VersionInfo)]
        if valid_results:
            # Prefer results with higher confidence
            return max(valid_results, key=lambda x: x.confidence)
        
        return None
    
    async def _search_version(self, name: str) -> Optional[VersionInfo]:
        """Search for version using Brave."""
        response = await self.brave.execute(
            query=f"{name} latest version release 2025",
            count=5,
            freshness="pw"  # Past week
        )
        
        if response.success and response.data:
            for result in response.data:
                # Look for version patterns in title/description
                text = f"{result['title']} {result['description']}"
                if version := self._extract_version_pattern(text):
                    return VersionInfo(
                        version=version,
                        source=result['url'],
                        confidence=0.7
                    )
        
        return None
    
    async def _context7_version(self, name: str) -> Optional[VersionInfo]:
        """Get version from Context7 docs."""
        # Resolve library
        library = await self.context7.resolve_library(name)
        if not library:
            return None
        
        # Get documentation
        docs = await self.context7.get_docs(
            library["id"],
            topic="version latest",
            tokens=1000
        )
        
        if docs:
            # Extract version from docs
            if version := self._extract_version_pattern(docs):
                return VersionInfo(
                    version=version,
                    source="context7",
                    confidence=0.9
                )
        
        return None
    
    async def _scrape_version(self, url: str, name: str) -> Optional[VersionInfo]:
        """Scrape version from official site."""
        response = await self.firecrawl.execute(
            url=url,
            formats=["markdown"],
            only_main_content=True
        )
        
        if response.success and response.data:
            # Look for version in scraped content
            if version := self._extract_version_pattern(response.data):
                return VersionInfo(
                    version=version,
                    source=url,
                    confidence=0.95  # High confidence for official sites
                )
        
        return None
    
    async def _discover_best_practices(self, name: str) -> List[str]:
        """Discover best practices."""
        practices = []
        
        # Search for best practices
        response = await self.brave.execute(
            query=f"{name} best practices 2025 modern",
            count=10
        )
        
        if response.success and response.data:
            for result in response.data:
                # Extract practices from descriptions
                if "best practice" in result["description"].lower():
                    practices.append(self._clean_practice(result["description"]))
        
        # Add generic practices if none found
        if not practices:
            practices = [
                f"Use TypeScript with {name} for better type safety",
                f"Follow official {name} documentation guidelines",
                f"Implement proper testing for {name} components",
                f"Use modern {name} features and patterns",
                f"Optimize {name} performance and bundle size"
            ]
        
        return practices
    
    async def _check_deprecations(self, name: str) -> List[str]:
        """Check for deprecations."""
        deprecations = []
        
        # Search for deprecation notices
        response = await self.brave.execute(
            query=f"{name} deprecated removed migration 2025",
            count=5
        )
        
        if response.success and response.data:
            for result in response.data:
                if any(word in result["description"].lower() 
                      for word in ["deprecated", "removed", "obsolete"]):
                    deprecations.append(result["description"][:200])
        
        return deprecations
    
    async def _find_documentation_url(self, name: str) -> Optional[str]:
        """Find official documentation URL."""
        # Search for official docs
        response = await self.brave.execute(
            query=f"{name} official documentation",
            count=3
        )
        
        if response.success and response.data:
            for result in response.data:
                if self._is_official_url(name, result["url"]):
                    return result["url"]
        
        return None
    
    def _extract_version_pattern(self, text: str) -> Optional[str]:
        """Extract version number from text."""
        # Semantic versioning pattern
        patterns = [
            r'(?:version|v)?\s*(\d+\.\d+\.\d+)',
            r'(?:version|v)?\s*(\d+\.\d+)',
            r'latest.*?(\d+\.\d+\.\d+)',
            r'release.*?(\d+\.\d+\.\d+)'
        ]
        
        for pattern in patterns:
            if match := re.search(pattern, text, re.IGNORECASE):
                return match.group(1)
        
        return None
    
    def _is_official_url(self, name: str, url: str) -> bool:
        """Check if URL is likely official."""
        official_domains = {
            "react": ["react.dev", "reactjs.org"],
            "vue": ["vuejs.org"],
            "angular": ["angular.io"],
            "nextjs": ["nextjs.org"],
            "vite": ["vitejs.dev"],
            "typescript": ["typescriptlang.org"],
            "python": ["python.org"],
            "nodejs": ["nodejs.org"],
        }
        
        if domains := official_domains.get(name.lower()):
            return any(domain in url.lower() for domain in domains)
        
        # Generic check
        return name.lower() in url.lower() and any(
            indicator in url for indicator in [".org", ".dev", ".io", "github.com"]
        )
    
    def _get_official_url(self, name: str) -> Optional[str]:
        """Get known official URL."""
        urls = {
            "react": "https://react.dev",
            "vue": "https://vuejs.org",
            "angular": "https://angular.io",
            "nextjs": "https://nextjs.org",
            "vite": "https://vitejs.dev",
            "typescript": "https://www.typescriptlang.org",
            "python": "https://python.org",
            "nodejs": "https://nodejs.org",
        }
        return urls.get(name.lower())
    
    def _clean_practice(self, text: str) -> str:
        """Clean and format practice text."""
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        # Truncate to reasonable length
        if len(text) > 150:
            text = text[:147] + "..."
        return text.strip()
    
    def _get_fallback_info(self, name: str) -> TechInfo:
        """Get fallback information."""
        version = self.fallback_versions.get(name.lower(), "latest")
        
        return TechInfo(
            name=name,
            version=version,
            latest_stable=version,
            release_date=datetime.now(),
            best_practices=["Follow official documentation"],
            deprecations=[],
            documentation_url=self._get_official_url(name) or 
                           f"https://www.google.com/search?q={name}+documentation"
        )
    
    async def get_current_versions(self, packages: List[str]) -> Dict[str, str]:
        """Get current versions for multiple packages."""
        self.log(f"Getting versions for {len(packages)} packages")
        
        # Use parallel execution for efficiency
        tasks = [self.research_technology(pkg) for pkg in packages]
        results = await asyncio.gather(*tasks)
        
        return {
            pkg: result.version 
            for pkg, result in zip(packages, results)
        }
    
    def get_research_summary(self) -> Dict[str, Any]:
        """Get summary of research activities."""
        return {
            "cache_size": len(self.cache.memory_cache),
            "brave_status": "open" if not self.brave.circuit_breaker.is_open() else "closed",
            "firecrawl_status": "open" if not self.firecrawl.circuit_breaker.is_open() else "closed",
            "context7_status": "open" if not self.context7.circuit_breaker.is_open() else "closed",
            "fallback_packages": len(self.fallback_versions)
        }
"""
MCP Enhanced Research Engine - Live technology research using MCP servers
Integrates Brave Search, Firecrawl, and Context7 for real-time technology information
"""

import json
import re
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from functools import lru_cache
import logging

from core.base import BaseModule, TechInfo

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ResearchResult:
    """Structured research result from MCP servers"""
    source: str  # brave, firecrawl, context7
    confidence: float  # 0.0 to 1.0
    data: Dict[str, Any]
    timestamp: datetime
    
    def is_fresh(self, max_age_hours: int = 24) -> bool:
        """Check if result is still fresh"""
        age = datetime.now() - self.timestamp
        return age < timedelta(hours=max_age_hours)


class MCPAdapter:
    """Base adapter for MCP services"""
    
    async def search(self, query: str) -> List[ResearchResult]:
        raise NotImplementedError
    
    async def extract(self, url: str) -> Optional[ResearchResult]:
        raise NotImplementedError


class BraveSearchAdapter(MCPAdapter):
    """Adapter for Brave Search MCP server"""
    
    async def search(self, query: str) -> List[ResearchResult]:
        """Search using Brave Search API"""
        try:
            # Import the actual MCP tool
            from mcp__mcp_web_search__brave_web_search import brave_web_search
            
            # Perform search
            results = await brave_web_search(query=query, count=5)
            
            research_results = []
            for result in results:
                research_results.append(ResearchResult(
                    source="brave_search",
                    confidence=0.7,  # Web search has moderate confidence
                    data={
                        "title": result.get("title", ""),
                        "url": result.get("url", ""),
                        "description": result.get("description", ""),
                        "query": query
                    },
                    timestamp=datetime.now()
                ))
            
            return research_results
        except Exception as e:
            logger.error(f"Brave search failed: {e}")
            return []


class FirecrawlAdapter(MCPAdapter):
    """Adapter for Firecrawl MCP server"""
    
    async def extract(self, url: str) -> Optional[ResearchResult]:
        """Extract content from URL using Firecrawl"""
        try:
            from mcp__firecrawl__firecrawl_scrape import firecrawl_scrape
            
            # Scrape the page
            result = await firecrawl_scrape(
                url=url,
                formats=["markdown"],
                onlyMainContent=True
            )
            
            # Extract version information from content
            content = result.get("markdown", "")
            version_info = self._extract_version_info(content)
            
            return ResearchResult(
                source="firecrawl",
                confidence=0.8,  # Direct extraction has high confidence
                data={
                    "url": url,
                    "content": content[:2000],  # Limit content size
                    "version_info": version_info,
                    "extracted_at": datetime.now().isoformat()
                },
                timestamp=datetime.now()
            )
        except Exception as e:
            logger.error(f"Firecrawl extraction failed: {e}")
            return None
    
    def _extract_version_info(self, content: str) -> Dict[str, str]:
        """Extract version numbers from content"""
        versions = {}
        
        # Pattern for version numbers
        patterns = [
            r'version[:\s]+(\d+\.\d+(?:\.\d+)?)',
            r'v(\d+\.\d+(?:\.\d+)?)',
            r'(\d+\.\d+(?:\.\d+)?)\s+•\s+Public',  # npm pattern
            r'"version":\s*"(\d+\.\d+(?:\.\d+)?)"',  # package.json
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                versions["latest"] = matches[0]
                break
        
        return versions


class Context7Adapter(MCPAdapter):
    """Adapter for Context7 tech_docs MCP server"""
    
    async def get_docs(self, library_name: str) -> Optional[ResearchResult]:
        """Get documentation from Context7"""
        try:
            from mcp__tech_docs__resolve_library_id import resolve_library_id
            from mcp__tech_docs__get_library_docs import get_library_docs
            
            # Resolve library ID
            library_info = await resolve_library_id(library_name)
            
            if not library_info:
                return None
            
            # Get the best match (highest trust score)
            best_match = self._select_best_library(library_info)
            
            # Get documentation
            docs = await get_library_docs(
                context7CompatibleLibraryID=best_match["id"],
                tokens=1000,
                topic="version api latest"
            )
            
            return ResearchResult(
                source="context7",
                confidence=0.95,  # Official docs have highest confidence
                data={
                    "library": library_name,
                    "library_id": best_match["id"],
                    "trust_score": best_match.get("trust_score", 0),
                    "docs": docs,
                    "snippets": best_match.get("snippets", 0)
                },
                timestamp=datetime.now()
            )
        except Exception as e:
            logger.error(f"Context7 docs failed: {e}")
            return None
    
    def _select_best_library(self, library_info: List[Dict]) -> Dict:
        """Select the best library match based on trust score and snippets"""
        # Sort by trust score and snippet count
        sorted_libs = sorted(
            library_info,
            key=lambda x: (x.get("trust_score", 0), x.get("snippets", 0)),
            reverse=True
        )
        return sorted_libs[0] if sorted_libs else {}


class MCPEnhancedResearchEngine(BaseModule):
    """Enhanced research engine using live MCP servers"""
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize with MCP adapters"""
        super().__init__(config)
        
        # Initialize adapters
        self.brave = BraveSearchAdapter()
        self.firecrawl = FirecrawlAdapter()
        self.context7 = Context7Adapter()
        
        # Cache settings
        self.cache_dir = Path(".mcp_cache")
        self.cache_dir.mkdir(exist_ok=True)
        self.cache_ttl = config.get("cache_ttl", 3600) if config else 3600  # 1 hour
        
        # In-memory cache for fast lookups
        self._memory_cache = {}
        
        # Fallback to static data if all MCP servers fail
        self.static_fallback = self._load_static_fallback()
    
    async def research_technology(self, name: str) -> TechInfo:
        """Research a technology using multiple MCP sources"""
        self.log(f"Researching technology: {name}")
        
        # Check memory cache first
        cache_key = f"tech_{name}"
        if cache_key in self._memory_cache:
            cached = self._memory_cache[cache_key]
            if cached.is_fresh(self.cache_ttl / 3600):
                self.log(f"Using memory cache for {name}")
                return self._result_to_techinfo(cached)
        
        # Parallel research from multiple sources
        research_tasks = [
            self._research_via_context7(name),
            self._research_via_brave(name),
            self._research_via_npm_pypi(name)
        ]
        
        results = await asyncio.gather(*research_tasks, return_exceptions=True)
        
        # Filter out errors and None results
        valid_results = [r for r in results if r and not isinstance(r, Exception)]
        
        if not valid_results:
            self.log(f"All MCP sources failed for {name}, using fallback")
            return self._get_fallback_techinfo(name)
        
        # Merge results with confidence weighting
        merged = self._merge_research_results(valid_results)
        
        # Cache the result
        self._memory_cache[cache_key] = merged
        
        return self._result_to_techinfo(merged)
    
    async def _research_via_context7(self, name: str) -> Optional[ResearchResult]:
        """Research using Context7 documentation"""
        return await self.context7.get_docs(name)
    
    async def _research_via_brave(self, name: str) -> Optional[ResearchResult]:
        """Research using Brave search"""
        # Search for latest version
        query = f"{name} latest version 2025 npm pypi github"
        search_results = await self.brave.search(query)
        
        if not search_results:
            return None
        
        # Extract the most relevant URL
        for result in search_results:
            url = result.data.get("url", "")
            if "npmjs.com" in url or "pypi.org" in url or "github.com" in url:
                # Extract detailed info from the page
                extracted = await self.firecrawl.extract(url)
                if extracted:
                    # Merge search and extraction data
                    extracted.data.update(result.data)
                    return extracted
        
        return search_results[0] if search_results else None
    
    async def _research_via_npm_pypi(self, name: str) -> Optional[ResearchResult]:
        """Direct research from NPM or PyPI"""
        # Determine if it's likely a Python or JS package
        if name in ["django", "flask", "fastapi", "pandas", "numpy", "pytest"]:
            url = f"https://pypi.org/project/{name}/"
        else:
            url = f"https://www.npmjs.com/package/{name}"
        
        return await self.firecrawl.extract(url)
    
    def _merge_research_results(self, results: List[ResearchResult]) -> ResearchResult:
        """Merge multiple research results with confidence weighting"""
        # Sort by confidence
        results.sort(key=lambda x: x.confidence, reverse=True)
        
        # Start with highest confidence result
        merged_data = results[0].data.copy()
        
        # Add data from other sources
        for result in results[1:]:
            for key, value in result.data.items():
                if key not in merged_data:
                    merged_data[key] = value
        
        # Extract version from all sources
        version = self._extract_best_version(results)
        if version:
            merged_data["version"] = version
        
        return ResearchResult(
            source="merged",
            confidence=max(r.confidence for r in results),
            data=merged_data,
            timestamp=datetime.now()
        )
    
    def _extract_best_version(self, results: List[ResearchResult]) -> Optional[str]:
        """Extract the most reliable version from results"""
        for result in results:
            # Check for explicit version in data
            if "version" in result.data:
                return result.data["version"]
            
            # Check version_info
            if "version_info" in result.data:
                info = result.data["version_info"]
                if "latest" in info:
                    return info["latest"]
            
            # Try to extract from content
            content = result.data.get("content", "") + result.data.get("description", "")
            patterns = [
                r'(\d+\.\d+\.\d+)',  # x.y.z
                r'v(\d+\.\d+\.\d+)',  # vx.y.z
                r'version[:\s]+(\d+\.\d+\.\d+)',
            ]
            
            for pattern in patterns:
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    return match.group(1)
        
        return None
    
    def _result_to_techinfo(self, result: ResearchResult) -> TechInfo:
        """Convert ResearchResult to TechInfo"""
        data = result.data
        
        # Extract version
        version = data.get("version", "latest")
        
        # Extract best practices from docs
        best_practices = []
        if "docs" in data:
            # Simple extraction from documentation
            docs_text = str(data["docs"])
            if "best practice" in docs_text.lower():
                best_practices.append("Follow official documentation guidelines")
        
        return TechInfo(
            name=data.get("library", data.get("name", "unknown")),
            version=version,
            latest_stable=version,
            release_date=datetime.now(),
            best_practices=best_practices,
            deprecations=[],
            documentation_url=data.get("url", "")
        )
    
    def _get_fallback_techinfo(self, name: str) -> TechInfo:
        """Get fallback TechInfo from static data"""
        version = self.static_fallback.get(name.lower(), "latest")
        
        return TechInfo(
            name=name,
            version=version,
            latest_stable=version,
            best_practices=["Follow official documentation"],
            deprecations=[]
        )
    
    def _load_static_fallback(self) -> Dict[str, str]:
        """Load static fallback versions"""
        # Minimal fallback for critical packages
        return {
            "react": "19.1.1",
            "vue": "3.5.13",
            "vite": "7.1.1",
            "typescript": "5.7.2",
            "fastapi": "0.117.1",
            "django": "5.1.5",
            "python": "3.13.1",
            "nodejs": "22.13.0",
            "nextjs": "15.2.0",
            "tailwindcss": "3.4.17"
        }
    
    async def find_best_practices(self, topic: str) -> List[str]:
        """Find best practices using web search"""
        query = f"{topic} best practices 2024 2025 modern development"
        results = await self.brave.search(query)
        
        practices = []
        for result in results[:3]:
            desc = result.data.get("description", "")
            # Extract key points from descriptions
            if "best practice" in desc.lower():
                practices.append(desc[:200])
        
        if not practices:
            practices = [
                "Use TypeScript for type safety",
                "Implement proper error handling",
                "Write comprehensive tests",
                "Follow security best practices",
                "Optimize for performance"
            ]
        
        return practices
    
    async def check_deprecations(self, tech_stack: Dict[str, str]) -> List[str]:
        """Check for deprecated technologies"""
        warnings = []
        
        for tech, version in tech_stack.items():
            # Search for deprecation info
            query = f"{tech} {version} deprecated EOL end of life 2025"
            results = await self.brave.search(query)
            
            for result in results[:2]:
                desc = result.data.get("description", "").lower()
                if "deprecated" in desc or "eol" in desc or "end of life" in desc:
                    warnings.append(f"{tech} {version} may be deprecated: {desc[:100]}")
        
        return warnings
    
    async def research_project_requirements(self, description: str) -> Dict[str, Any]:
        """Research requirements for a project using web search"""
        self.log(f"Researching project requirements: {description}")
        
        # Search for similar projects and tech stacks
        query = f"{description} tech stack 2025 modern best architecture"
        results = await self.brave.search(query)
        
        # Extract technology recommendations
        recommended_stack = {}
        
        # Analyze search results for technology mentions
        for result in results:
            content = result.data.get("description", "").lower()
            
            # Look for technology mentions
            if "react" in content and "frontend" not in recommended_stack:
                recommended_stack["frontend"] = "react"
            if "fastapi" in content and "backend" not in recommended_stack:
                recommended_stack["backend"] = "fastapi"
            if "postgresql" in content and "database" not in recommended_stack:
                recommended_stack["database"] = "postgresql"
        
        # Get versions for recommended technologies
        for key, tech in recommended_stack.items():
            tech_info = await self.research_technology(tech)
            recommended_stack[key] = f"{tech}@{tech_info.version}"
        
        # Get best practices
        best_practices = await self.find_best_practices(description)
        
        return {
            "recommended_stack": recommended_stack,
            "best_practices": best_practices,
            "warnings": [],
            "research_sources": [r.data.get("url") for r in results[:3]]
        }


# Example usage for testing
async def test_mcp_research():
    """Test the MCP research engine"""
    engine = MCPEnhancedResearchEngine()
    
    # Test researching React
    react_info = await engine.research_technology("react")
    print(f"React version: {react_info.version}")
    
    # Test researching FastAPI  
    fastapi_info = await engine.research_technology("fastapi")
    print(f"FastAPI version: {fastapi_info.version}")
    
    # Test project requirements
    project = await engine.research_project_requirements("Build a modern dashboard with auth")
    print(f"Recommended stack: {project['recommended_stack']}")


if __name__ == "__main__":
    asyncio.run(test_mcp_research())
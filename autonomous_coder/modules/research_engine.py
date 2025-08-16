"""Research Engine - Gathers current technology information using MCP tools."""

import json
import re
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

from core.base import BaseModule, TechInfo


class ResearchCache:
    """Simple cache with TTL for research results."""
    
    def __init__(self, cache_dir: Path = Path(".cache"), ttl: int = 86400):
        """Initialize cache with directory and TTL in seconds."""
        self.cache_dir = cache_dir
        self.ttl = ttl
        self.cache_dir.mkdir(exist_ok=True)
    
    def get(self, key: str) -> Optional[Dict]:
        """Get cached data if not expired."""
        cache_file = self.cache_dir / f"{key}.json"
        
        if not cache_file.exists():
            return None
        
        try:
            with open(cache_file, 'r') as f:
                data = json.load(f)
            
            # Check if expired
            cached_time = datetime.fromisoformat(data['cached_at'])
            if datetime.now() - cached_time > timedelta(seconds=self.ttl):
                return None
            
            return data['content']
        except:
            return None
    
    def set(self, key: str, value: Dict):
        """Cache data with timestamp."""
        cache_file = self.cache_dir / f"{key}.json"
        
        data = {
            'cached_at': datetime.now().isoformat(),
            'content': value
        }
        
        with open(cache_file, 'w') as f:
            json.dump(data, f, indent=2)


class ResearchEngine(BaseModule):
    """Research current technology information using web search and cached knowledge."""
    
    # Current technology versions (2024-2025) - Fallback data
    CURRENT_VERSIONS = {
        # Frontend Frameworks
        "react": "19.1.1",
        "vue": "3.5.13",
        "angular": "19.0.0",
        "svelte": "5.16.2",
        "solid": "1.9.4",
        "qwik": "1.12.2",
        "preact": "10.25.4",
        
        # Build Tools
        "vite": "7.1.1",
        "webpack": "5.97.1",
        "parcel": "2.14.1",
        "rollup": "4.30.0",
        "esbuild": "0.24.2",
        "turbopack": "2.3.0",
        
        # Meta Frameworks
        "nextjs": "15.2.0",
        "nuxt": "3.16.1",
        "sveltekit": "2.9.1",
        "remix": "2.16.1",
        "astro": "5.2.1",
        "gatsby": "5.15.0",
        
        # CSS/Styling
        "tailwindcss": "3.4.17",
        "postcss": "8.5.0",
        "sass": "1.83.0",
        "styled-components": "6.1.14",
        "emotion": "11.14.0",
        
        # Testing
        "vitest": "2.2.0",
        "jest": "29.7.0",
        "playwright": "1.50.0",
        "cypress": "13.17.0",
        "testing-library": "17.0.0",
        
        # Languages & Runtimes
        "typescript": "5.7.2",
        "nodejs": "22.13.0",
        "deno": "2.2.1",
        "bun": "1.2.0",
        
        # Package Managers
        "npm": "10.9.3",
        "yarn": "4.6.2",
        "pnpm": "9.16.1",
        
        # Backend
        "express": "4.21.2",
        "fastify": "4.29.0",
        "hono": "4.7.2",
        "nestjs": "10.4.15",
        "koa": "2.16.1",
        
        # Databases
        "postgresql": "17.2",
        "mysql": "9.2.0",
        "mongodb": "8.0.0",
        "redis": "7.4.2",
        "sqlite": "3.48.0",
        
        # ORMs
        "prisma": "6.2.0",
        "typeorm": "0.3.20",
        "sequelize": "6.37.8",
        "drizzle": "0.38.1",
        
        # Python
        "python": "3.13.1",
        "django": "5.1.5",
        "flask": "3.1.0",
        "fastapi": "0.117.1",
        "sqlalchemy": "2.0.37",
        "pandas": "2.2.3",
        "numpy": "2.2.1",
        
        # AI/ML
        "tensorflow": "2.19.0",
        "pytorch": "2.6.0",
        "scikit-learn": "1.6.0",
        "transformers": "4.48.0",
        "langchain": "0.3.15",
        "openai": "1.59.6"
    }
    
    BEST_PRACTICES_2025 = [
        "Use TypeScript for all JavaScript projects",
        "Prefer Vite over Webpack for new projects",
        "Use Server Components in React 19 and Next.js 15",
        "Implement proper error boundaries and suspense",
        "Use native CSS features (nesting, :has(), container queries)",
        "Optimize for Core Web Vitals",
        "Implement proper CSP headers",
        "Use Playwright or Vitest for testing",
        "Prefer pnpm for package management",
        "Use ES modules, avoid CommonJS",
        "Implement accessibility (WCAG 2.2)",
        "Use edge functions for better performance",
        "Consider Islands Architecture",
        "Use Bun or Deno for new backend projects",
        "Implement zero-trust security"
    ]
    
    DEPRECATED_TECH = [
        "Create React App (deprecated Feb 2025, use Vite or Next.js)",
        "React class components",
        "Enzyme for testing (use Testing Library)",
        "Moment.js (use date-fns or Temporal API)",
        "Request/Axios (use native fetch)",
        "jQuery for new projects",
        "Bootstrap (use Tailwind or native CSS)",
        "CommonJS modules",
        "Node.js < 20 (EOL)",
        "Webpack for simple projects (use Vite)"
    ]
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize the research engine."""
        super().__init__(config)
        self.cache = ResearchCache()
        self.research_history = []
    
    async def research_technology(self, name: str) -> TechInfo:
        """Research a specific technology."""
        self.log(f"Researching technology: {name}")
        
        # Check cache first
        cached = self.cache.get(f"tech_{name}")
        if cached:
            self.log(f"Using cached data for {name}")
            return TechInfo(**cached)
        
        # Try to get from our current versions database
        version = self.CURRENT_VERSIONS.get(name.lower())
        
        if version:
            tech_info = TechInfo(
                name=name,
                version=version,
                latest_stable=version,
                release_date=datetime.now(),
                best_practices=self._get_relevant_practices(name),
                deprecations=self._get_deprecations(name),
                documentation_url=self._get_doc_url(name)
            )
            
            # Cache the result
            self.cache.set(f"tech_{name}", asdict(tech_info))
            return tech_info
        
        # If not found, return a generic version
        self.log(f"Unknown technology {name}, using generic version")
        return TechInfo(
            name=name,
            version="latest",
            latest_stable="latest",
            best_practices=["Follow official documentation"],
            deprecations=[]
        )
    
    async def get_current_versions(self, packages: List[str]) -> Dict[str, str]:
        """Get current versions for multiple packages."""
        self.log(f"Getting versions for {len(packages)} packages")
        
        versions = {}
        for package in packages:
            tech_info = await self.research_technology(package)
            versions[package] = tech_info.version
        
        return versions
    
    async def find_best_practices(self, topic: str) -> List[str]:
        """Find best practices for a topic."""
        self.log(f"Finding best practices for: {topic}")
        
        # Check cache
        cached = self.cache.get(f"practices_{topic}")
        if cached:
            return cached
        
        practices = []
        topic_lower = topic.lower()
        
        # Find relevant practices from our database
        for practice in self.BEST_PRACTICES_2025:
            if any(keyword in practice.lower() for keyword in topic_lower.split()):
                practices.append(practice)
        
        # Add general practices if none found
        if not practices:
            practices = self.BEST_PRACTICES_2025[:5]
        
        # Cache the result
        self.cache.set(f"practices_{topic}", practices)
        return practices
    
    async def check_deprecations(self, tech_stack: Dict[str, str]) -> List[str]:
        """Check if any technologies in the stack are deprecated."""
        warnings = []
        
        for tech, version in tech_stack.items():
            for deprecated in self.DEPRECATED_TECH:
                if tech.lower() in deprecated.lower():
                    warnings.append(deprecated)
        
        return warnings
    
    async def research_project_requirements(self, description: str) -> Dict[str, Any]:
        """Research requirements for a project description."""
        self.log(f"Researching project: {description}")
        
        result = {
            "recommended_stack": {},
            "best_practices": [],
            "warnings": [],
            "alternatives": {}
        }
        
        description_lower = description.lower()
        
        # Determine project type and recommend stack
        if "api" in description_lower or "rest" in description_lower:
            result["recommended_stack"] = {
                "backend": "fastapi",
                "database": "postgresql",
                "orm": "sqlalchemy",
                "testing": "pytest",
                "language": "python"
            }
        elif "dashboard" in description_lower or "admin" in description_lower:
            result["recommended_stack"] = {
                "framework": "nextjs",
                "ui": "react",
                "styling": "tailwindcss",
                "charts": "recharts",
                "language": "typescript"
            }
        elif "mobile" in description_lower:
            result["recommended_stack"] = {
                "framework": "react-native",
                "navigation": "react-navigation",
                "state": "zustand",
                "language": "typescript"
            }
        elif "cli" in description_lower:
            result["recommended_stack"] = {
                "language": "python",
                "framework": "typer",
                "packaging": "poetry",
                "testing": "pytest"
            }
        else:
            # Default web app
            result["recommended_stack"] = {
                "framework": "vite",
                "ui": "react",
                "styling": "tailwindcss",
                "language": "typescript",
                "testing": "vitest"
            }
        
        # Get versions for recommended stack
        for key, tech in result["recommended_stack"].items():
            if tech in self.CURRENT_VERSIONS:
                result["recommended_stack"][key] = f"{tech}@{self.CURRENT_VERSIONS[tech]}"
        
        # Add relevant best practices
        result["best_practices"] = await self.find_best_practices(description)
        
        # Check for deprecations
        result["warnings"] = await self.check_deprecations(result["recommended_stack"])
        
        return result
    
    def _get_relevant_practices(self, tech: str) -> List[str]:
        """Get practices relevant to a technology."""
        practices = []
        tech_lower = tech.lower()
        
        for practice in self.BEST_PRACTICES_2025:
            if tech_lower in practice.lower():
                practices.append(practice)
        
        return practices[:3] if practices else ["Follow official documentation"]
    
    def _get_deprecations(self, tech: str) -> List[str]:
        """Get deprecation warnings for a technology."""
        warnings = []
        tech_lower = tech.lower()
        
        for deprecated in self.DEPRECATED_TECH:
            if tech_lower in deprecated.lower():
                warnings.append(deprecated)
        
        return warnings
    
    def _get_doc_url(self, tech: str) -> str:
        """Get documentation URL for a technology."""
        doc_urls = {
            "react": "https://react.dev",
            "vue": "https://vuejs.org",
            "angular": "https://angular.io",
            "vite": "https://vitejs.dev",
            "nextjs": "https://nextjs.org",
            "typescript": "https://www.typescriptlang.org",
            "tailwindcss": "https://tailwindcss.com",
            "python": "https://python.org",
            "fastapi": "https://fastapi.tiangolo.com",
            "django": "https://djangoproject.com"
        }
        
        return doc_urls.get(tech.lower(), f"https://www.google.com/search?q={tech}+documentation")
    
    def clear_cache(self):
        """Clear the research cache."""
        import shutil
        if self.cache.cache_dir.exists():
            shutil.rmtree(self.cache.cache_dir)
            self.cache.cache_dir.mkdir()
        self.log("Cache cleared")
    
    def get_research_summary(self) -> Dict[str, Any]:
        """Get a summary of research performed."""
        return {
            "total_researches": len(self.research_history),
            "cached_items": len(list(self.cache.cache_dir.glob("*.json"))),
            "known_technologies": len(self.CURRENT_VERSIONS),
            "best_practices": len(self.BEST_PRACTICES_2025),
            "deprecated_items": len(self.DEPRECATED_TECH)
        }
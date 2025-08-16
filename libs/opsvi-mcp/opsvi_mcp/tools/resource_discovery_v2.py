#!/usr/bin/env python3
"""
Resource Discovery Tool V2 - Binary Decision Support
Core Purpose: Answer "Do we have this capability? YES/NO"
If YES -> Point to where (don't document it)
If NO -> Proceed with development
"""

import ast
import re
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple


class ResourceDiscoveryV2:
    """
    Lightweight discovery tool for binary decisions about existing capabilities.
    NOT a documentation tool - just answers: exists? where? how to import?
    """
    
    def __init__(self, root_path: str = "/home/opsvi/master_root"):
        self.root_path = Path(root_path)
        self.libs_path = self.root_path / "libs"
        
        # Pre-compute package index for fast lookups
        self._package_index = self._build_package_index()
    
    def _build_package_index(self) -> Dict[str, Dict]:
        """Build a simple index of packages for fast capability checks."""
        index = {}
        
        if not self.libs_path.exists():
            return index
            
        for package_dir in self.libs_path.iterdir():
            if package_dir.is_dir() and package_dir.name.startswith("opsvi-"):
                # Extract category from package name
                category = package_dir.name.replace("opsvi-", "")
                
                # Get basic info
                description = self._get_quick_description(package_dir)
                
                index[category] = {
                    "package_name": package_dir.name,
                    "path": str(package_dir),
                    "description": description,
                    "keywords": self._extract_keywords(package_dir.name, description)
                }
        
        return index
    
    def _get_quick_description(self, package_dir: Path) -> str:
        """Get one-line description from README or pyproject."""
        readme_path = package_dir / "README.md"
        if readme_path.exists():
            try:
                for line in readme_path.read_text().split("\n"):
                    if line.strip() and not line.startswith("#"):
                        return line.strip()[:100]
            except:
                pass
        return f"{package_dir.name} package"
    
    def _extract_keywords(self, name: str, description: str) -> List[str]:
        """Extract searchable keywords from name and description."""
        keywords = []
        
        # From package name
        name_parts = name.lower().replace("-", " ").replace("_", " ").split()
        keywords.extend(name_parts)
        
        # From description
        desc_words = re.findall(r'\w+', description.lower())
        keywords.extend([w for w in desc_words if len(w) > 3])
        
        return list(set(keywords))
    
    def check_capability(self, functionality: str) -> Dict[str, Any]:
        """
        Main entry point: Check if a capability exists.
        Returns a simple YES/NO with location if found.
        """
        
        # Parse the query
        query_words = re.findall(r'\w+', functionality.lower())
        query_words = [w for w in query_words if len(w) > 2]  # Skip short words
        
        # Fast check against package index
        best_match = None
        best_confidence = 0.0
        alternatives = 0
        
        for category, info in self._package_index.items():
            confidence = self._calculate_confidence(query_words, info)
            
            if confidence > best_confidence:
                best_confidence = confidence
                best_match = info
            
            if confidence > 0.3:  # Count as alternative if somewhat relevant
                alternatives += 1
        
        # Fast exit if high confidence match
        if best_confidence > 0.8:
            return self._format_found_response(best_match, best_confidence, alternatives - 1)
        
        # If medium confidence, do a targeted deep search in best match
        if best_confidence > 0.5 and best_match:
            enhanced_match = self._deep_scan_package(best_match, query_words)
            if enhanced_match:
                return enhanced_match
        
        # If low confidence, scan top 3 packages more carefully
        if best_confidence > 0.3:
            top_packages = self._get_top_packages(query_words, 3)
            for pkg_info in top_packages:
                enhanced_match = self._deep_scan_package(pkg_info, query_words)
                if enhanced_match and enhanced_match["confidence"] > 0.7:
                    return enhanced_match
        
        # Nothing found
        return self._format_not_found_response(functionality)
    
    def _calculate_confidence(self, query_words: List[str], package_info: Dict) -> float:
        """Calculate confidence score for a package match."""
        confidence = 0.0
        package_name = package_info.get("package_name", "").lower()
        keywords = package_info.get("keywords", [])
        description = package_info.get("description", "").lower()
        
        # Special case: common abbreviations and their expansions
        expansions = {
            "jwt": ["jwt", "json", "web", "token", "auth"],
            "api": ["api", "rest", "graphql", "http"],
            "db": ["database", "data", "store"],
            "auth": ["auth", "authentication", "authorization", "jwt", "token"],
            "redis": ["redis", "cache", "memory"],
        }
        
        for word in query_words:
            # Check for expanded matches
            word_variants = expansions.get(word, [word])
            
            for variant in word_variants:
                # Check package category (highest weight)
                if variant in package_name:
                    confidence += 0.5
                    break
                
                # Check keywords (medium weight)
                if any(variant in kw for kw in keywords):
                    confidence += 0.3
                    break
                
                # Check description (lower weight)
                if variant in description:
                    confidence += 0.1
        
        # Boost for exact category match
        category = package_info.get("package_name", "").replace("opsvi-", "")
        if any(word == category for word in query_words):
            confidence += 0.5
        
        return min(confidence, 1.0)  # Cap at 1.0
    
    def _deep_scan_package(self, package_info: Dict, query_words: List[str]) -> Optional[Dict]:
        """
        Do a targeted scan of a specific package for better confidence.
        Only looks at main module files, not everything.
        """
        package_path = Path(package_info["path"])
        module_path = package_path / package_info["package_name"].replace("-", "_")
        
        if not module_path.exists():
            return None
        
        # Check main __init__.py and top-level files only
        best_import = None
        confidence_boost = 0.0
        
        # Check __init__.py for exports
        init_file = module_path / "__init__.py"
        if init_file.exists():
            try:
                content = init_file.read_text()
                for word in query_words:
                    if word in content.lower():
                        confidence_boost += 0.1
                
                # Look for main classes/functions
                tree = ast.parse(content)
                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        if any(word in node.name.lower() for word in query_words):
                            best_import = f"from {package_info['package_name'].replace('-', '_')} import {node.name}"
                            confidence_boost += 0.3
                            break
            except:
                pass
        
        # Quick scan of main provider/client files
        for pattern in ["*provider*.py", "*client*.py", "*manager*.py", "*interface*.py"]:
            for py_file in module_path.glob(pattern):
                if py_file.name.startswith("_"):
                    continue
                    
                try:
                    # Just check filename for relevance
                    if any(word in py_file.stem.lower() for word in query_words):
                        if not best_import:
                            module_name = py_file.stem
                            best_import = f"from {package_info['package_name'].replace('-', '_')}.{module_name} import ..."
                        confidence_boost += 0.2
                except:
                    pass
        
        if confidence_boost > 0:
            original_confidence = self._calculate_confidence(query_words, package_info)
            total_confidence = min(original_confidence + confidence_boost, 1.0)
            
            return {
                "capability_exists": True,
                "confidence": round(total_confidence, 2),
                "primary_package": package_info["package_name"],
                "usage": best_import or f"import {package_info['package_name'].replace('-', '_')}",
                "location": package_info["path"],
                "description": package_info["description"],
                "recommendation": "Use existing package - see above import"
            }
        
        return None
    
    def _get_top_packages(self, query_words: List[str], limit: int = 3) -> List[Dict]:
        """Get top N packages by confidence for deeper scanning."""
        scored_packages = []
        
        for category, info in self._package_index.items():
            confidence = self._calculate_confidence(query_words, info)
            if confidence > 0:
                scored_packages.append((confidence, info))
        
        scored_packages.sort(key=lambda x: x[0], reverse=True)
        return [info for _, info in scored_packages[:limit]]
    
    def _format_found_response(self, match: Dict, confidence: float, alternatives: int) -> Dict[str, Any]:
        """Format response when capability is found."""
        return {
            "capability_exists": True,
            "confidence": round(confidence, 2),
            "primary_package": match["package_name"],
            "usage": f"import {match['package_name'].replace('-', '_')}",
            "location": match["path"],
            "description": match["description"],
            "alternatives": alternatives,
            "recommendation": f"Use existing {match['package_name']} package"
        }
    
    def _format_not_found_response(self, functionality: str) -> Dict[str, Any]:
        """Format response when capability is not found."""
        suggested_name = f"opsvi-{functionality.lower().split()[0]}"
        
        return {
            "capability_exists": False,
            "confidence": 0.0,
            "primary_package": None,
            "usage": None,
            "location": None,
            "description": None,
            "alternatives": 0,
            "recommendation": f"No existing capability found. Consider creating '{suggested_name}'"
        }
    
    def quick_check(self, package_name: str) -> Dict[str, Any]:
        """
        Direct package existence check - even faster than search.
        Use when you know the exact package name.
        """
        # Try without prefix
        category = package_name.replace("opsvi-", "")
        if category in self._package_index:
            info = self._package_index[category]
            return {
                "capability_exists": True,
                "confidence": 1.0,
                "primary_package": info["package_name"],
                "usage": f"import {info['package_name'].replace('-', '_')}",
                "location": info["path"],
                "description": info["description"],
                "alternatives": 0,
                "recommendation": "Package exists - use it"
            }
        
        # Not found
        return {
            "capability_exists": False,
            "confidence": 0.0,
            "primary_package": None,
            "usage": None,
            "location": None,
            "description": None,
            "alternatives": 0,
            "recommendation": f"Package '{package_name}' not found"
        }
    
    def list_categories(self) -> Dict[str, List[str]]:
        """
        Return just a list of available categories/packages.
        No details, just names for overview.
        """
        categories = {}
        
        # Group by common prefixes
        for category, info in self._package_index.items():
            # Extract high-level category
            if "llm" in category or "ai" in category:
                group = "ai_ml"
            elif "data" in category or "db" in category:
                group = "data"
            elif "auth" in category or "security" in category:
                group = "security"
            elif "api" in category or "http" in category:
                group = "networking"
            elif "mcp" in category or "tool" in category:
                group = "tools"
            else:
                group = "utilities"
            
            if group not in categories:
                categories[group] = []
            categories[group].append(info["package_name"])
        
        return {
            "categories": categories,
            "total_packages": len(self._package_index),
            "recommendation": "Use check_capability() to find specific functionality"
        }


# Compatibility wrapper for existing MCP interface
def resource_discovery_tool(action: str, **kwargs) -> Dict[str, Any]:
    """MCP tool interface for resource discovery."""
    
    discovery = ResourceDiscoveryV2()
    
    if action == "check_capability":
        return discovery.check_capability(kwargs.get("functionality", ""))
    elif action == "quick_check":
        return discovery.quick_check(kwargs.get("package_name", ""))
    elif action == "list_categories":
        return discovery.list_categories()
    else:
        return {
            "error": f"Unknown action: {action}",
            "available_actions": ["check_capability", "quick_check", "list_categories"]
        }


if __name__ == "__main__":
    # Test the new binary decision approach
    discovery = ResourceDiscoveryV2()
    
    # Test cases
    tests = [
        "JWT authentication",
        "database connection pooling",
        "Redis cache",
        "WebSocket support",
        "GraphQL API"
    ]
    
    for test in tests:
        result = discovery.check_capability(test)
        print(f"\n{test}:")
        print(f"  Exists: {result['capability_exists']}")
        print(f"  Confidence: {result['confidence']}")
        if result['capability_exists']:
            print(f"  Package: {result['primary_package']}")
            print(f"  Usage: {result['usage']}")
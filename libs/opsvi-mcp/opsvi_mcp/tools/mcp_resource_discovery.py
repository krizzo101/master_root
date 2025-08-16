#!/usr/bin/env python3
"""
MCP Tool for discovering existing resources in the libs/ directory.
Helps prevent reinventing the wheel by finding reusable components.
"""

import ast
import json
import re
from pathlib import Path
from typing import Any, Dict, List


class ResourceDiscoveryTool:
    """
    MCP tool for discovering existing resources in the monorepo.
    Searches libs/ for reusable packages and components.
    """

    # Default limits to prevent token overflow
    DEFAULT_MAX_PACKAGES = 5  # Reduced from 10
    DEFAULT_MAX_MODULES_PER_PACKAGE = 5  # Reduced from 20
    DEFAULT_MAX_UTILITIES = 10  # Reduced from 30
    DEFAULT_MAX_PATTERNS = 5  # Reduced from 10
    DEFAULT_MAX_PACKAGE_LIST = 10  # Reduced from 25
    
    # Threshold for suggesting more specific search
    TOO_MANY_RESULTS_THRESHOLD = 8  # Reduced from 15

    def __init__(self, root_path: str = "/home/opsvi/master_root"):
        self.root_path = Path(root_path)
        self.libs_path = self.root_path / "libs"

    def search_resources(
        self, 
        functionality: str, 
        search_depth: int = 3, 
        include_tests: bool = False,
        max_packages: int = None,
        max_modules_per_package: int = None
    ) -> Dict[str, Any]:
        """
        Search for existing resources related to specific functionality.

        Args:
            functionality: Description of needed functionality
            search_depth: How deep to search in directory structure
            include_tests: Whether to include test files in results
            max_packages: Maximum packages to return in detail
            max_modules_per_package: Maximum modules per package

        Returns:
            Dict containing found resources and their descriptions
        """
        results = {
            "search_term": functionality,
            "packages_found": [],
            "relevant_modules": [],
            "potential_utilities": [],
            "similar_patterns": [],
            "search_guidance": None,
        }

        # Convert search term to patterns
        search_patterns = self._generate_search_patterns(functionality)

        # Search libs/ directory
        if self.libs_path.exists():
            for package_dir in self.libs_path.iterdir():
                if package_dir.is_dir() and package_dir.name.startswith("opsvi-"):
                    package_info = self._analyze_package(
                        package_dir, search_patterns, search_depth, include_tests
                    )
                    if package_info["relevance_score"] > 0:
                        results["packages_found"].append(package_info)

        # Sort by relevance
        results["packages_found"].sort(key=lambda x: x["relevance_score"], reverse=True)
        
        # Check if too many results - suggest more specific search
        total_found = len(results["packages_found"])
        if total_found > self.TOO_MANY_RESULTS_THRESHOLD:
            # Provide guidance instead of just truncating
            top_categories = self._analyze_result_categories(results["packages_found"])
            results["search_guidance"] = {
                "status": "too_many_results",
                "total_found": total_found,
                "suggestion": f"Found {total_found} packages matching '{functionality}'. Please be more specific.",
                "refinement_suggestions": self._generate_refinement_suggestions(functionality, top_categories),
                "top_matches_summary": [
                    {"name": p["name"], "score": p["relevance_score"]} 
                    for p in results["packages_found"][:5]
                ]
            }
            # Return minimal results to avoid token overflow
            results["packages_found"] = results["packages_found"][:3]
            results["relevant_modules"] = []
            results["potential_utilities"] = []
            return results
        
        # Apply package limit for reasonable result sets
        max_pkg = max_packages or self.DEFAULT_MAX_PACKAGES
        results["packages_found"] = results["packages_found"][:max_pkg]

        # Extract specific findings with limits
        max_mods = max_modules_per_package or self.DEFAULT_MAX_MODULES_PER_PACKAGE
        for package in results["packages_found"]:
            # Limit modules per package
            package["relevant_modules"] = package.get("relevant_modules", [])[:max_mods]
            # Limit utilities per package
            package["utilities"] = package.get("utilities", [])[:self.DEFAULT_MAX_UTILITIES]
            
            results["relevant_modules"].extend(package.get("relevant_modules", []))
            results["potential_utilities"].extend(package.get("utilities", []))
            results["similar_patterns"].extend(package.get("patterns", []))
        
        # Apply overall limits to aggregated results
        results["relevant_modules"] = results["relevant_modules"][:max_mods * 2]  # Allow 2x for aggregate
        results["potential_utilities"] = results["potential_utilities"][:self.DEFAULT_MAX_UTILITIES]
        results["similar_patterns"] = results["similar_patterns"][:self.DEFAULT_MAX_PATTERNS]
        
        # Add success guidance if results are reasonable
        if 0 < total_found <= self.TOO_MANY_RESULTS_THRESHOLD:
            results["search_guidance"] = {
                "status": "success",
                "total_found": total_found,
                "recommendation": self._generate_recommendation(results["packages_found"])
            }

        return results

    def _generate_search_patterns(self, functionality: str) -> List[str]:
        """Generate search patterns from functionality description."""
        # Split into words and create patterns
        words = re.findall(r"\w+", functionality.lower())
        patterns = words.copy()

        # Add common variations
        for word in words:
            # Add underscored version
            if len(word) > 3:
                patterns.append(f"{word}_")
                patterns.append(f"_{word}")

            # Add common suffixes
            if word not in ["the", "a", "an", "for", "with", "to"]:
                patterns.extend(
                    [f"{word}er", f"{word}or", f"{word}ing", f"{word}ed", f"{word}s"]
                )

        return list(set(patterns))
    
    def _analyze_result_categories(self, packages: List[Dict]) -> Dict[str, int]:
        """Analyze categories of found packages to suggest refinements."""
        categories = {}
        for package in packages:
            # Extract category from package name
            name_parts = package["name"].split("-")
            if len(name_parts) > 1:
                category = name_parts[-1]  # Last part often indicates category
                categories[category] = categories.get(category, 0) + 1
        return categories
    
    def _generate_refinement_suggestions(self, original_query: str, categories: Dict[str, int]) -> List[str]:
        """Generate suggestions for more specific searches."""
        suggestions = []
        
        # Suggest adding technology/framework specifics
        if "database" in original_query.lower():
            suggestions.extend([
                f"{original_query} PostgreSQL",
                f"{original_query} MongoDB",
                f"{original_query} Redis"
            ])
        elif "auth" in original_query.lower():
            suggestions.extend([
                f"{original_query} JWT",
                f"{original_query} OAuth",
                f"{original_query} session"
            ])
        else:
            # Generic suggestions based on found categories
            top_categories = sorted(categories.items(), key=lambda x: x[1], reverse=True)[:3]
            for cat, _ in top_categories:
                suggestions.append(f"{original_query} {cat}")
        
        # Add pattern-specific suggestions
        suggestions.extend([
            f"{original_query} client",
            f"{original_query} provider",
            f"{original_query} interface"
        ])
        
        return suggestions[:5]  # Return top 5 suggestions
    
    def _generate_recommendation(self, packages: List[Dict]) -> str:
        """Generate recommendation based on search results."""
        if not packages:
            return "No existing packages found. Consider creating a new package."
        
        top_package = packages[0]
        if top_package["relevance_score"] > 10:
            return f"Strongly recommend using '{top_package['name']}' - high relevance match."
        elif top_package["relevance_score"] > 5:
            return f"Consider using '{top_package['name']}' or exploring top matches."
        else:
            return "Found some potential matches, but may need to create specialized solution."

    def _analyze_package(
        self,
        package_dir: Path,
        search_patterns: List[str],
        search_depth: int,
        include_tests: bool,
    ) -> Dict[str, Any]:
        """Analyze a package for relevance to search patterns."""
        package_info = {
            "name": package_dir.name,
            "path": str(package_dir),
            "description": "",
            "relevant_modules": [],
            "utilities": [],
            "patterns": [],
            "relevance_score": 0,
        }

        # Check README for description
        readme_path = package_dir / "README.md"
        if readme_path.exists():
            try:
                readme_content = readme_path.read_text()
                # Extract first paragraph as description
                lines = readme_content.split("\n")
                for line in lines:
                    if line.strip() and not line.startswith("#"):
                        package_info["description"] = line.strip()
                        break

                # Check readme for patterns
                readme_lower = readme_content.lower()
                for pattern in search_patterns:
                    if pattern in readme_lower:
                        package_info["relevance_score"] += 2
            except Exception:
                pass

        # Search Python files
        module_path = package_dir / package_dir.name.replace("-", "_")
        if module_path.exists():
            for py_file in module_path.rglob("*.py"):
                # Skip tests unless requested
                if not include_tests and "test" in py_file.name:
                    continue

                # Skip __pycache__
                if "__pycache__" in str(py_file):
                    continue

                # Limit search depth
                depth = len(py_file.relative_to(module_path).parts)
                if depth > search_depth:
                    continue

                # Analyze file
                file_info = self._analyze_python_file(py_file, search_patterns)
                if file_info["relevance_score"] > 0:
                    package_info["relevant_modules"].append(
                        {
                            "module": str(py_file.relative_to(package_dir)),
                            "score": file_info["relevance_score"],
                            "classes": file_info["classes"],
                            "functions": file_info["functions"],
                        }
                    )
                    package_info["relevance_score"] += file_info["relevance_score"]

                    # Add utilities and patterns
                    if file_info["classes"]:
                        package_info["utilities"].extend(file_info["classes"])
                    if file_info["functions"]:
                        package_info["utilities"].extend(file_info["functions"])

        return package_info

    def _analyze_python_file(
        self, py_file: Path, search_patterns: List[str]
    ) -> Dict[str, Any]:
        """Analyze a Python file for relevant content."""
        file_info = {"relevance_score": 0, "classes": [], "functions": []}

        try:
            content = py_file.read_text()
            content_lower = content.lower()

            # Check for pattern matches
            for pattern in search_patterns:
                if pattern in content_lower:
                    file_info["relevance_score"] += 1

            # Parse AST for structure
            try:
                tree = ast.parse(content)

                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        class_name = node.name
                        # Check if class name matches patterns
                        for pattern in search_patterns:
                            if pattern in class_name.lower():
                                file_info["relevance_score"] += 3
                                file_info["classes"].append(class_name)
                                break

                    elif isinstance(node, ast.FunctionDef):
                        func_name = node.name
                        # Check if function name matches patterns
                        for pattern in search_patterns:
                            if pattern in func_name.lower():
                                file_info["relevance_score"] += 2
                                file_info["functions"].append(func_name)
                                break
            except Exception:
                # If AST parsing fails, just use content matching
                pass

        except Exception:
            # File read error
            pass

        return file_info

    def list_packages(self, max_results: int = None, summary_only: bool = True) -> Dict[str, Any]:
        """List all available packages in libs/ directory.
        
        Args:
            max_results: Maximum number of packages to return (default: 25)
            summary_only: If True, only return name and description (default: True to prevent overflow)
        
        Returns:
            Dict with packages list and guidance
        """
        packages = []
        limit = max_results or self.DEFAULT_MAX_PACKAGE_LIST
        result = {
            "packages": [],
            "total_count": 0,
            "guidance": None
        }

        if self.libs_path.exists():
            for package_dir in self.libs_path.iterdir():
                if package_dir.is_dir() and not package_dir.name.startswith("."):
                    package_info = {
                        "name": package_dir.name,
                        "path": str(package_dir.relative_to(self.libs_path)),
                        "description": "",
                        "has_tests": False,
                        "modules": [],
                    }

                    # Try to get description from README
                    readme_path = package_dir / "README.md"
                    if readme_path.exists():
                        try:
                            content = readme_path.read_text()
                            lines = content.split("\n")
                            for line in lines:
                                if line.strip() and not line.startswith("#"):
                                    package_info["description"] = line.strip()[:100]
                                    break
                        except Exception:
                            pass

                    # Check for tests
                    test_dir = package_dir / "tests"
                    if test_dir.exists():
                        package_info["has_tests"] = True

                    # List Python modules (unless summary_only)
                    if not summary_only:
                        module_count = 0
                        for py_file in package_dir.rglob("*.py"):
                            if not any(p in str(py_file) for p in ["__pycache__", ".pyc"]):
                                module_path = py_file.relative_to(package_dir)
                                package_info["modules"].append(str(module_path))
                                module_count += 1
                                # Limit modules per package to prevent overflow
                                if module_count >= 5:  # Reduced from 10
                                    package_info["modules"].append(f"... and {sum(1 for _ in package_dir.rglob('*.py') if '__pycache__' not in str(_)) - 5} more")
                                    break
                    else:
                        # In summary mode, just count modules
                        module_count = sum(1 for _ in package_dir.rglob("*.py") 
                                         if "__pycache__" not in str(_))
                        package_info["module_count"] = module_count
                        del package_info["modules"]  # Remove modules list in summary mode

                    packages.append(package_info)
                    
                    # Check if we've hit the limit
                    if len(packages) >= limit:
                        break

        # Count total packages
        total_count = sum(1 for p in self.libs_path.iterdir() 
                         if p.is_dir() and not p.name.startswith("."))
        
        result["packages"] = packages
        result["total_count"] = total_count
        
        # Provide guidance based on results
        if total_count > limit:
            result["guidance"] = {
                "status": "truncated",
                "message": f"Showing {len(packages)} of {total_count} packages.",
                "suggestions": [
                    "Use search_resources() with specific functionality instead",
                    "Use check_package_exists() if you know the package name",
                    f"Increase max_results beyond {limit} to see more (may cause token overflow)"
                ]
            }
        else:
            result["guidance"] = {
                "status": "complete",
                "message": f"Showing all {total_count} packages."
            }

        return result

    def check_package_exists(self, package_name: str) -> Dict[str, Any]:
        """Check if a specific package exists and get its details."""
        package_path = self.libs_path / package_name

        if not package_path.exists():
            # Try with opsvi- prefix
            package_path = self.libs_path / f"opsvi-{package_name}"

        result = {
            "exists": package_path.exists() and package_path.is_dir(),
            "path": str(package_path) if package_path.exists() else None,
            "modules": [],
            "description": "",
            "dependencies": [],
        }

        if result["exists"]:
            # Get modules (limit to prevent overflow)
            module_count = 0
            for py_file in package_path.rglob("*.py"):
                if not any(p in str(py_file) for p in ["__pycache__", ".pyc"]):
                    result["modules"].append(str(py_file.relative_to(package_path)))
                    module_count += 1
                    if module_count >= 10:  # Reduced from 50 - much more conservative
                        total_modules = sum(1 for _ in package_path.rglob("*.py") 
                                          if "__pycache__" not in str(_))
                        result["modules"].append(f"... truncated ({total_modules} total modules)")
                        result["module_summary"] = {
                            "shown": 10,
                            "total": total_modules,
                            "message": "Use search_resources() with specific functionality to find relevant modules"
                        }
                        break

            # Get description from README
            readme_path = package_path / "README.md"
            if readme_path.exists():
                try:
                    content = readme_path.read_text()
                    lines = content.split("\n")
                    for line in lines:
                        if line.strip() and not line.startswith("#"):
                            result["description"] = line.strip()[:200]
                            break
                except Exception:
                    pass

            # Get dependencies from pyproject.toml
            pyproject_path = package_path / "pyproject.toml"
            if pyproject_path.exists():
                try:
                    content = pyproject_path.read_text()
                    # Simple extraction of dependencies
                    if "dependencies = [" in content:
                        deps_start = content.index("dependencies = [")
                        deps_end = content.index("]", deps_start)
                        deps_section = content[deps_start:deps_end]
                        for line in deps_section.split("\n")[1:]:
                            if '"' in line:
                                dep = line.split('"')[1]
                                result["dependencies"].append(dep)
                except Exception:
                    pass

        return result

    def find_similar_patterns(
        self, code_snippet: str, language: str = "python"
    ) -> List[Dict[str, Any]]:
        """Find existing code with similar functionality."""
        results = []

        # Extract key patterns from the snippet
        patterns = []
        if "def " in code_snippet:
            # Extract function names
            import re

            func_matches = re.findall(r"def\s+(\w+)", code_snippet)
            patterns.extend(func_matches)

        if "class " in code_snippet:
            # Extract class names
            import re

            class_matches = re.findall(r"class\s+(\w+)", code_snippet)
            patterns.extend(class_matches)

        # Search for similar patterns
        for py_file in self.libs_path.rglob("*.py"):
            if any(
                p in str(py_file) for p in ["__pycache__", ".pyc", "test_", "_test.py"]
            ):
                continue

            try:
                content = py_file.read_text()
                similarity_score = 0
                matched_patterns = []

                for pattern in patterns:
                    if pattern in content:
                        similarity_score += 0.3
                        matched_patterns.append(pattern)

                if similarity_score > 0:
                    result = {
                        "file_path": str(py_file.relative_to(self.root_path)),
                        "similarity_score": min(similarity_score, 1.0),
                        "matched_patterns": matched_patterns,
                        "suggested_import": self._generate_import_statement(py_file),
                    }
                    results.append(result)
            except Exception:
                continue

        # Sort by similarity score
        results.sort(key=lambda x: x["similarity_score"], reverse=True)
        return results[:10]  # Return top 10 matches

    def analyze_dependencies(self, package_name: str) -> Dict[str, Any]:
        """Analyze dependencies for a package."""
        package_path = self.libs_path / package_name

        if not package_path.exists():
            package_path = self.libs_path / f"opsvi-{package_name}"

        result = {
            "internal_imports": [],
            "external_dependencies": [],
            "python_version": None,
            "optional_dependencies": {},
        }

        if not package_path.exists():
            return result

        # Analyze Python files for imports
        internal_packages = set()
        external_packages = set()

        for py_file in package_path.rglob("*.py"):
            if any(p in str(py_file) for p in ["__pycache__", ".pyc"]):
                continue

            try:
                content = py_file.read_text()
                # Find imports
                import_lines = [
                    line
                    for line in content.split("\n")
                    if line.strip().startswith(("import ", "from "))
                ]

                for line in import_lines:
                    if "from libs." in line or "import libs." in line:
                        # Internal import
                        parts = line.split()
                        if "from" in parts:
                            idx = parts.index("from") + 1
                            if idx < len(parts):
                                module = (
                                    parts[idx].split(".")[1]
                                    if "." in parts[idx]
                                    else parts[idx]
                                )
                                internal_packages.add(module)
                    elif not line.startswith(("from .", "import .")):
                        # External import
                        parts = line.split()
                        if "import" in parts:
                            idx = parts.index("import") + 1
                            if idx < len(parts):
                                module = parts[idx].split(".")[0]
                                if module not in [
                                    "os",
                                    "sys",
                                    "json",
                                    "re",
                                    "pathlib",
                                    "typing",
                                ]:
                                    external_packages.add(module)
            except Exception:
                continue

        result["internal_imports"] = list(internal_packages)
        result["external_dependencies"] = list(external_packages)

        # Check pyproject.toml for declared dependencies
        pyproject_path = package_path / "pyproject.toml"
        if pyproject_path.exists():
            try:
                content = pyproject_path.read_text()

                # Extract Python version
                if 'python = "' in content:
                    py_match = re.search(r'python = "([^"]+)"', content)
                    if py_match:
                        result["python_version"] = py_match.group(1)

                # Extract optional dependencies
                if (
                    "[tool.poetry.extras]" in content
                    or "[project.optional-dependencies]" in content
                ):
                    # Simple extraction of optional deps
                    lines = content.split("\n")
                    current_extra = None
                    for line in lines:
                        if line.startswith("[") and "optional" in line.lower():
                            current_extra = "extras"
                        elif current_extra and "=" in line:
                            key = line.split("=")[0].strip()
                            result["optional_dependencies"][key] = []
            except Exception:
                pass

        return result

    def _generate_import_statement(self, file_path: Path) -> str:
        """Generate an import statement for a file."""
        try:
            relative_path = file_path.relative_to(self.libs_path)
            parts = list(relative_path.parts)

            # Remove .py extension
            if parts[-1].endswith(".py"):
                parts[-1] = parts[-1][:-3]

            # Convert to import statement
            if parts[-1] == "__init__":
                parts = parts[:-1]

            return f"from libs.{'.'.join(parts)} import ..."
        except Exception:
            return ""


# MCP Tool Functions
def mcp__resource_discovery__search_resources(
    functionality: str, search_depth: int = 3, include_tests: bool = False
) -> str:
    """
    Search for existing resources in libs/ related to specific functionality.

    Args:
        functionality: Description of the functionality you need
        search_depth: How deep to search in directory structure (default: 3)
        include_tests: Whether to include test files in results (default: False)

    Returns:
        JSON string with found resources
    """
    tool = ResourceDiscoveryTool()
    results = tool.search_resources(functionality, search_depth, include_tests)
    return json.dumps(results, indent=2)


def mcp__resource_discovery__list_packages() -> str:
    """
    List all available packages in the libs/ directory.

    Returns:
        JSON string with all packages and their descriptions
    """
    tool = ResourceDiscoveryTool()
    packages = tool.list_all_packages()
    return json.dumps(packages, indent=2)


# For testing
if __name__ == "__main__":
    # Test search
    print("Searching for 'mcp tools'...")
    results = mcp__resource_discovery__search_resources("mcp tools")
    print(results)

    print("\n" + "=" * 50 + "\n")

    # Test list
    print("Listing all packages...")
    packages = mcp__resource_discovery__list_packages()
    print(packages)

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

    def __init__(self, root_path: str = "/home/opsvi/master_root"):
        self.root_path = Path(root_path)
        self.libs_path = self.root_path / "libs"

    def search_resources(
        self, functionality: str, search_depth: int = 3, include_tests: bool = False
    ) -> Dict[str, Any]:
        """
        Search for existing resources related to specific functionality.

        Args:
            functionality: Description of needed functionality
            search_depth: How deep to search in directory structure
            include_tests: Whether to include test files in results

        Returns:
            Dict containing found resources and their descriptions
        """
        results = {
            "search_term": functionality,
            "packages_found": [],
            "relevant_modules": [],
            "potential_utilities": [],
            "similar_patterns": [],
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

        # Extract specific findings
        for package in results["packages_found"]:
            results["relevant_modules"].extend(package.get("relevant_modules", []))
            results["potential_utilities"].extend(package.get("utilities", []))
            results["similar_patterns"].extend(package.get("patterns", []))

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

    def list_all_packages(self) -> List[Dict[str, str]]:
        """List all available packages in libs/ directory."""
        packages = []

        if self.libs_path.exists():
            for package_dir in self.libs_path.iterdir():
                if package_dir.is_dir() and package_dir.name.startswith("opsvi-"):
                    package_info = {
                        "name": package_dir.name,
                        "path": str(package_dir),
                        "description": "",
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

                    packages.append(package_info)

        return packages


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

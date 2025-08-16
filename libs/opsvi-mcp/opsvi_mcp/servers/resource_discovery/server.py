#!/usr/bin/env python3
"""
MCP Server for Resource Discovery
Provides tools to discover existing packages and components in the libs/ directory.
"""

import sys
from pathlib import Path
from typing import Any, Dict, List

# Add the libs directory to the path
libs_path = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(libs_path))
root_path = libs_path.parent

from fastmcp import FastMCP  # noqa: E402

from opsvi_mcp.tools.mcp_resource_discovery import (  # noqa: E402
    ResourceDiscoveryTool,
)

# Initialize the MCP server
mcp = FastMCP("resource-discovery")

# Initialize the resource discovery tool
discovery_tool = ResourceDiscoveryTool(root_path=str(root_path))


@mcp.tool()
def search_resources(
    functionality: str, 
    search_depth: int = 2,  # Reduced default from 3
    include_tests: bool = False,
    max_packages: int = None
) -> Dict[str, Any]:
    """
    Search for existing resources related to specific functionality.
    
    IMPORTANT: Be specific with search terms to avoid token overflow.
    Generic terms like "database" will return too many results.

    Args:
        functionality: Description of needed functionality (be specific!)
        search_depth: How deep to search in directory structure (default: 2, max recommended: 3)
        include_tests: Whether to include test files in results (default: False)
        max_packages: Override max packages returned (default: 5)

    Returns:
        Dict containing:
        - packages_found: List of relevant packages (limited to prevent overflow)
        - search_guidance: Recommendations if too many/few results
        - relevant_modules: Top relevant modules (limited)
        - potential_utilities: Key utility functions found

    Examples:
        # Good - Specific searches:
        search_resources("neo4j graph client", search_depth=2)
        search_resources("JWT authentication provider", search_depth=2)
        search_resources("Redis cache interface", search_depth=1)
        
        # Bad - Too generic (will suggest refinements):
        search_resources("database")  # Too broad
        search_resources("auth")  # Too broad
    """
    return discovery_tool.search_resources(functionality, search_depth, include_tests, max_packages)


@mcp.tool()
def list_packages(
    max_results: int = None,
    summary_only: bool = True
) -> Any:
    """
    List available packages in the libs/ directory.
    
    WARNING: Full package list can exceed token limits!
    Use search_resources() or check_package_exists() for specific needs.

    Args:
        max_results: Maximum packages to return (default: 10)
        summary_only: If True, exclude module lists to save tokens (default: True)

    Returns:
        Dict containing:
        - packages: List of package info (limited to prevent overflow)
        - total_count: Total number of packages available
        - guidance: Suggestions for more specific queries

    Example:
        # Get summary of first 10 packages
        result = list_packages()
        
        # If you need specific functionality, use:
        search_resources("specific functionality")
    """
    return discovery_tool.list_packages(max_results, summary_only)


@mcp.tool()
def check_package_exists(package_name: str) -> Dict[str, Any]:
    """
    Check if a specific package exists and get its details.
    
    This is the PREFERRED method when you know the package name.
    Much more efficient than list_packages() or broad searches.

    Args:
        package_name: Name of the package to check (e.g., "opsvi-llm", "opsvi-agents")

    Returns:
        Dict containing:
        - exists: Boolean indicating if package exists
        - path: Full path to package if it exists
        - modules: List of modules (limited to 10 to save tokens)
        - module_summary: Summary if more than 10 modules exist
        - description: Package description if available
        - dependencies: List of dependencies if pyproject.toml exists

    Example:
        result = check_package_exists("opsvi-llm")
        if result["exists"]:
            print(f"Found at: {result['path']}")
            
        # Also works without "opsvi-" prefix:
        result = check_package_exists("llm")  # Will try "opsvi-llm"
    """
    return discovery_tool.check_package_exists(package_name)


@mcp.tool()
def find_similar_functionality(
    code_snippet: str, language: str = "python"
) -> List[Dict[str, Any]]:
    """
    Find existing code with similar functionality to a given snippet.

    Args:
        code_snippet: Code snippet to find similar implementations for
        language: Programming language (default: "python")

    Returns:
        List of similar code found with:
        - file_path: Path to file containing similar code
        - similarity_score: Score indicating how similar (0-1)
        - matched_patterns: What patterns matched
        - suggested_import: How to import and use this code

    Example:
        snippet = "def authenticate_user(username, password):"
        similar = find_similar_functionality(snippet)
    """
    return discovery_tool.find_similar_patterns(code_snippet, language)


@mcp.tool()
def get_package_dependencies(package_name: str) -> Dict[str, Any]:
    """
    Get dependencies and imports for a specific package.

    Args:
        package_name: Name of the package to analyze

    Returns:
        Dict containing:
        - internal_imports: Other libs/ packages this depends on
        - external_dependencies: Third-party packages required
        - python_version: Required Python version if specified
        - optional_dependencies: Optional/extra dependencies

    Example:
        deps = get_package_dependencies("opsvi-agents")
        print(f"Requires: {deps['external_dependencies']}")
    """
    return discovery_tool.analyze_dependencies(package_name)


if __name__ == "__main__":
    # Run the MCP server
    mcp.run()

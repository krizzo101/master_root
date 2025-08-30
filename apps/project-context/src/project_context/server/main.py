"""Project Context MCP Server - Main entry point."""

from pathlib import Path
from typing import Optional

from fastmcp import FastMCP
from pydantic import BaseModel, Field

from ..core.cache import CacheManager
from ..core.reader import ProjectIntelReader
from ..tools import register_all_tools

# Initialize FastMCP server
mcp = FastMCP(
    name="project-context",
    version="0.1.0",
    description="Semantic access to project intelligence data",
)

# Global instances
reader: Optional[ProjectIntelReader] = None
cache: Optional[CacheManager] = None


class ServerConfig(BaseModel):
    """Server configuration."""

    intel_dir: str = Field(
        default=".proj-intel", description="Path to project intelligence directory"
    )
    cache_enabled: bool = Field(default=True, description="Enable caching")
    cache_ttl: int = Field(default=300, description="Cache TTL in seconds")


@mcp.tool()
async def get_project_summary() -> dict:
    """Get overall project statistics and summary.

    Returns comprehensive project overview including file counts,
    code statistics, and key metrics.
    """
    if not reader:
        return {"error": "Server not initialized"}

    # Implementation will use reader to fetch summary
    return {
        "status": "Not yet implemented",
        "message": "This tool will provide project summary",
    }


def main():
    """Main entry point for the server."""
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="Project Context MCP Server")
    parser.add_argument(
        "--intel-dir",
        default=".proj-intel",
        help="Path to project intelligence directory",
    )
    parser.add_argument("--no-cache", action="store_true", help="Disable caching")

    args = parser.parse_args()

    # Initialize server components
    global reader, cache

    intel_path = Path(args.intel_dir)
    if not intel_path.exists():
        print(f"Error: Intelligence directory not found: {intel_path}")
        sys.exit(1)

    # Initialize reader
    from ..core.reader import ProjectIntelReader

    reader = ProjectIntelReader(str(intel_path))

    # Initialize cache if enabled
    if not args.no_cache:
        from ..core.cache import CacheManager

        cache = CacheManager()

    # Register all tools with the MCP server
    register_all_tools(mcp, reader, cache)

    # Run the server
    mcp.run()


if __name__ == "__main__":
    main()

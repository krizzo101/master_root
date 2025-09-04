"""Project Context MCP Server - Main entry point."""

import asyncio
import atexit
from datetime import datetime
from pathlib import Path
from typing import Optional

import structlog
from fastmcp import FastMCP
from pydantic import BaseModel, Field

from ..core.cache import CacheManager
from ..core.cache_watcher import CacheWatcher, project_invalidation_callback
from ..core.reader import ProjectIntelReader
from ..tools import register_all_tools

logger = structlog.get_logger(__name__)

# Initialize FastMCP server
mcp = FastMCP(name="project-context", version="0.1.0")

# Global instances
reader: Optional[ProjectIntelReader] = None
cache: Optional[CacheManager] = None
cache_watcher: Optional[CacheWatcher] = None


class ServerConfig(BaseModel):
    """Server configuration."""

    intel_dir: str = Field(
        default=".proj-intel", description="Path to project intelligence directory"
    )
    cache_enabled: bool = Field(default=True, description="Enable caching")
    cache_ttl: int = Field(default=300, description="Cache TTL in seconds")
    file_data_ttl: int = Field(default=60, description="File data cache TTL in seconds")
    project_stats_ttl: int = Field(
        default=300, description="Project stats cache TTL in seconds"
    )
    watch_enabled: bool = Field(
        default=True, description="Enable file watching for cache invalidation"
    )


# Tool registration is handled by register_all_tools() function


async def cleanup_on_exit():
    """Cleanup function to stop cache watcher on exit."""
    global cache_watcher
    if cache_watcher:
        await cache_watcher.stop()
        logger.info("Cache watcher stopped on exit")


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
    parser.add_argument("--no-watch", action="store_true", help="Disable file watching")
    parser.add_argument(
        "--file-ttl", type=int, default=60, help="File data cache TTL in seconds"
    )
    parser.add_argument(
        "--stats-ttl", type=int, default=300, help="Project stats cache TTL in seconds"
    )

    args = parser.parse_args()

    # Initialize server components
    global reader, cache, cache_watcher

    intel_path = Path(args.intel_dir)
    if not intel_path.exists():
        print(f"Error: Intelligence directory not found: {intel_path}")
        sys.exit(1)

    # Initialize reader
    from ..core.reader import ProjectIntelReader

    reader = ProjectIntelReader(str(intel_path))

    # Initialize cache if enabled
    if not args.no_cache:
        cache = CacheManager(
            file_data_ttl=args.file_ttl, project_stats_ttl=args.stats_ttl
        )
        logger.info(
            "Cache manager initialized",
            file_ttl=args.file_ttl,
            stats_ttl=args.stats_ttl,
        )

        # Initialize file watcher if enabled
        if not args.no_watch:
            cache_watcher = CacheWatcher(
                cache_manager=cache,
                watch_paths={str(Path.cwd()), str(intel_path)},
                invalidation_callback=project_invalidation_callback,
            )

            # Start the cache watcher in the background
            async def start_watcher():
                try:
                    await cache_watcher.start()
                    logger.info("Cache watcher started")
                except Exception as e:
                    logger.error("Failed to start cache watcher", error=str(e))

            # Register cleanup function
            atexit.register(lambda: asyncio.run(cleanup_on_exit()))

            # Start watcher
            asyncio.create_task(start_watcher())

    # Register all tools with the MCP server and enhanced database
    register_all_tools(mcp, reader, cache)

    # Run the server
    mcp.run()


if __name__ == "__main__":
    main()

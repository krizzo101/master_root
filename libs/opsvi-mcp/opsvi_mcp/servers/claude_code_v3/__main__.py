"""Claude Code V3 MCP Server - Entry Point"""

import logging
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from .config import config
from .server import server

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stderr)  # Log to stderr to avoid stdout conflicts
    ],
)

logger = logging.getLogger(__name__)


def main():
    """Main entry point"""
    logger.info("Starting Claude Code V3 MCP Server")
    logger.info(f"Max recursion depth: {config.recursion.max_depth}")
    logger.info(f"Multi-agent enabled: {config.decomposition.enable_decomposition}")

    # Run the FastMCP server
    server.run()


if __name__ == "__main__":
    main()

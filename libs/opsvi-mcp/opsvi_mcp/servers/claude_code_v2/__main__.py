"""
Claude Code V2 MCP Server - Module Entry Point

Run with: python -m opsvi_mcp.servers.claude_code_v2
"""

import asyncio
import os
import sys
import logging
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from .server import ClaudeCodeV2Server
from .config import ServerConfig


def setup_logging():
    """Setup logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stderr),  # Use stderr to avoid stdout JSON conflicts
            logging.FileHandler('/tmp/claude_code_v2_server.log')
        ]
    )


def check_environment():
    """Check and display configuration"""
    logger = logging.getLogger(__name__)
    logger.debug("Claude Code V2 MCP Server Configuration:")
    logger.debug(f"  Results Directory: {os.environ.get('CLAUDE_RESULTS_DIR', '/tmp/claude_results')}")
    logger.debug(f"  Max Concurrent L1: {os.environ.get('CLAUDE_MAX_CONCURRENT_L1', '10')}")
    logger.debug(f"  Max Recursion: {os.environ.get('CLAUDE_MAX_RECURSION', '3')}")
    logger.debug(f"  Default Timeout: {os.environ.get('CLAUDE_DEFAULT_TIMEOUT', '600')}s")
    
    if not os.environ.get("CLAUDE_CODE_TOKEN"):
        logger.warning("CLAUDE_CODE_TOKEN not set - Server will run but Claude API calls will fail")
    else:
        token = os.environ.get("CLAUDE_CODE_TOKEN")
        masked = token[:4] + "..." + token[-4:] if len(token) > 8 else "***"
        logger.debug(f"  Claude Token: {masked}")


def main():
    """Main entry point for MCP server"""
    setup_logging()
    check_environment()
    
    logger = logging.getLogger(__name__)
    logger.info("Starting Claude Code V2 MCP Server...")
    
    # Initialize configuration
    config = ServerConfig()
    
    # Create server
    server = ClaudeCodeV2Server(config)
    logger.info("Server initialized with fire-and-forget pattern")
    logger.info(f"Results directory: {config.default_results_dir}")
    logger.info(f"Max first-level agents: {config.max_concurrent_first_level}")
    logger.info("Server ready to accept connections")
    
    # Run the MCP server directly - it handles its own event loop
    server.mcp.run()


if __name__ == "__main__":
    main()
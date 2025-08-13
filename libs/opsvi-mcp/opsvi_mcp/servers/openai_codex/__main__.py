"""
OpenAI Codex MCP Server - Module Entry Point

Run with: python -m opsvi_mcp.servers.openai_codex
"""

import asyncio
import os
import sys
import logging
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from .server import OpenAICodexServer
from .config import CodexConfig


def setup_logging():
    """Setup logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('/tmp/openai_codex_server.log')
        ]
    )


def check_environment():
    """Check required environment variables"""
    if not os.environ.get("OPENAI_API_KEY"):
        print("ERROR: OPENAI_API_KEY environment variable is required")
        print("Please set it with: export OPENAI_API_KEY='your-api-key'")
        sys.exit(1)


async def main():
    """Main entry point"""
    setup_logging()
    check_environment()
    
    logger = logging.getLogger(__name__)
    logger.info("Starting OpenAI Codex MCP Server...")
    
    try:
        # Initialize configuration
        config = CodexConfig()
        
        # Create and run server
        server = OpenAICodexServer(config)
        logger.info(f"Server initialized with model: {config.model}")
        logger.info(f"Cache enabled: {config.enable_cache}")
        logger.info("Server ready to accept connections")
        
        await server.run()
        
    except KeyboardInterrupt:
        logger.info("Server shutdown requested")
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
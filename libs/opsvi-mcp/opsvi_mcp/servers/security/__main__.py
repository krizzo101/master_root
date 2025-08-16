"""Entry point for Security Analysis MCP Server"""

import asyncio
import logging
from .server import server

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Main entry point"""
    logger.info("Starting Security Analysis MCP Server")
    asyncio.run(server.run())


if __name__ == "__main__":
    main()

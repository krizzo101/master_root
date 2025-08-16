"""
Cursor Agent MCP Server - Module Entry Point

Run with: python -m opsvi_mcp.servers.cursor_agent
"""

import asyncio
import os
import sys
import logging
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from .server import CursorAgentServer
from .config import CursorConfig


def setup_logging():
    """Setup logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('/tmp/cursor_agent_server.log')
        ]
    )


def check_environment():
    """Check and display configuration"""
    print("Cursor Agent MCP Server Configuration:")
    print(f"  Cursor Executable: {os.environ.get('CURSOR_EXECUTABLE', 'cursor')}")
    print(f"  Workspace: {os.environ.get('CURSOR_WORKSPACE', os.getcwd())}")
    print(f"  Communication Method: {os.environ.get('CURSOR_COMM_METHOD', 'websocket')}")
    
    if os.environ.get('CURSOR_COMM_METHOD', 'websocket') == 'websocket':
        print(f"  WebSocket Host: {os.environ.get('CURSOR_WS_HOST', 'localhost')}")
        print(f"  WebSocket Port: {os.environ.get('CURSOR_WS_PORT', '7070')}")
    
    print()


async def main():
    """Main entry point"""
    setup_logging()
    check_environment()
    
    logger = logging.getLogger(__name__)
    logger.info("Starting Cursor Agent MCP Server...")
    
    try:
        # Initialize configuration
        config = CursorConfig()
        
        # Create and run server
        server = CursorAgentServer(config)
        logger.info(f"Server initialized with communication method: {config.communication_method}")
        logger.info(f"Default agents: {config.default_agents}")
        logger.info("Server ready to accept connections")
        
        # Note: Available agents can be listed via the list_available_agents tool
        logger.info("Use the list_available_agents tool to see all available agents")
        
        await server.run()
        
    except KeyboardInterrupt:
        logger.info("Server shutdown requested")
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
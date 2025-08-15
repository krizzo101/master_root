#!/usr/bin/env python3
"""Test script for Gemini MCP server"""

import asyncio
import os
import sys

# Add libs to path
sys.path.insert(0, '/home/opsvi/master_root/libs')

from opsvi_mcp.servers.gemini_agent.server import GeminiAgentServer
from opsvi_mcp.servers.gemini_agent.config import GeminiConfig

async def test_server():
    """Test the Gemini server"""
    # Set environment
    os.environ['GEMINI_API_KEY'] = 'AIzaSyDcABMDq_BnwtwYDW-xDYwpblaPaHxQFsY'
    os.environ['PYTHONPATH'] = '/home/opsvi/master_root/libs'
    
    # Create config
    config = GeminiConfig.from_env()
    config.validate()
    
    # Create server
    server = GeminiAgentServer(config)
    
    # Call the execute_gemini method directly
    result = await server.execute_gemini(
        task="Write a simple Python function that calculates the factorial of a number",
        mode="code",
        timeout=30,
        enable_file_ops=False,
        enable_shell=False
    )
    
    print("Result:", result)
    print("\nOutput:", result.get('output', '')[:500])

if __name__ == "__main__":
    asyncio.run(test_server())
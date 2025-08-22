#!/usr/bin/env python3
"""
Enhanced Knowledge MCP Server Wrapper

This is a thin wrapper that imports and runs the enhanced knowledge server
from apps/knowledge_system. This maintains the standard location for MCP
servers while keeping the core logic in apps.
"""

import os
import sys

# Add path for imports
sys.path.insert(0, "/home/opsvi/master_root")

# Import and run the server
from apps.knowledge_system.mcp_knowledge_server import main

if __name__ == "__main__":
    main()

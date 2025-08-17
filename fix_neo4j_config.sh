#!/bin/bash
# Auto-generated Neo4j configuration fix

echo "Fixing Neo4j configuration..."

# Update Python files
sed -i 's|bolt://localhost:7687|bolt://localhost:7687|g' /home/opsvi/master_root/apps/knowledge_system/knowledge_system.py
sed -i 's|bolt://localhost:7687|bolt://localhost:7687|g' /home/opsvi/master_root/libs/opsvi-mcp/opsvi_mcp/servers/knowledge/server.py

# Set environment variables
export NEO4J_URI="bolt://localhost:7687"
export NEO4J_ENCRYPTED="false"

echo "✅ Configuration updated!"
echo "Restart MCP servers with: claude mcp restart"

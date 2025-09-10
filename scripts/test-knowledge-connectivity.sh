#!/bin/bash
# Test Knowledge System Connectivity

echo "🔍 Testing Knowledge System Connectivity"
echo "========================================"
echo ""

# Test Neo4j
echo "1️⃣ Testing Neo4j Database..."
echo -n "   Bolt port (7687): "
if nc -zv localhost 7687 2>&1 | grep -q succeeded; then
    echo "✅ Open"
else
    echo "❌ Closed"
fi

echo -n "   HTTP port (7474): "
if nc -zv localhost 7474 2>&1 | grep -q succeeded; then
    echo "✅ Open"
else
    echo "❌ Closed"
fi

echo -n "   Cypher query: "
if docker-compose -f docker-compose.knowledge.yml exec neo4j cypher-shell -u neo4j -p password "RETURN 'Connected!' as status" 2>/dev/null | grep -q "Connected"; then
    echo "✅ Working"
else
    echo "❌ Failed"
fi

# Test Embedding Service
echo ""
echo "2️⃣ Testing Embedding Service..."
echo -n "   Port (8000): "
if nc -zv localhost 8000 2>&1 | grep -q succeeded; then
    echo "✅ Open"
else
    echo "❌ Closed"
fi

echo -n "   Health endpoint: "
if curl -s -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Responding"
else
    echo "❌ Not responding"
fi

echo -n "   Embedding generation: "
RESPONSE=$(curl -s -X POST http://localhost:8000/embed \
  -H "Content-Type: application/json" \
  -d '{"text": "test", "use_cache": false}' 2>/dev/null)

if echo "$RESPONSE" | grep -q "embedding"; then
    echo "✅ Working"
else
    echo "❌ Failed"
fi

# Test Python imports
echo ""
echo "3️⃣ Testing Python Environment..."
echo -n "   Neo4j driver: "
if python3 -c "import neo4j" 2>/dev/null; then
    echo "✅ Installed"
else
    echo "❌ Not installed"
fi

echo -n "   MCP package: "
if python3 -c "import mcp" 2>/dev/null; then
    echo "✅ Installed"
else
    echo "❌ Not installed (run: pip install mcp)"
fi

# Test MCP configuration
echo ""
echo "4️⃣ Testing MCP Configuration..."
echo -n "   Config file: "
if [ -f "/home/opsvi/master_root/.mcp.json" ]; then
    echo "✅ Exists"

    echo -n "   Knowledge server: "
    if jq -e '.mcpServers.knowledge' /home/opsvi/master_root/.mcp.json > /dev/null 2>&1; then
        echo "✅ Configured"
    else
        echo "❌ Not configured"
    fi

    echo -n "   DB server: "
    if jq -e '.mcpServers.db' /home/opsvi/master_root/.mcp.json > /dev/null 2>&1; then
        echo "✅ Configured"
    else
        echo "❌ Not configured"
    fi
else
    echo "❌ Not found"
fi

# Summary
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Summary:"
if nc -zv localhost 7687 2>&1 | grep -q succeeded && \
   nc -zv localhost 8000 2>&1 | grep -q succeeded && \
   [ -f "/home/opsvi/master_root/.mcp.json" ]; then
    echo "✅ All connectivity tests passed!"
else
    echo "⚠️  Some connectivity issues detected"
    echo "Run ./start-knowledge-system.sh to fix"
fi

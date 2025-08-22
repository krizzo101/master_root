# Neo4j Knowledge Tool Setup Instructions for WSL2

## Task: Install and Configure Neo4j for Knowledge Tool System

You need to set up a Neo4j instance in your WSL2 environment that will serve as the knowledge storage backend for the MCP knowledge tool system. This setup must be compatible with the knowledge tool helper library and MCP server configuration.

## Prerequisites Check
```bash
# Verify WSL2 environment
uname -a | grep -i microsoft
# Check available memory (need at least 2GB free)
free -h
# Check Java availability (Neo4j requires Java 17+)
java -version || echo "Java not installed"
```

## Step 1: Install Neo4j Community Edition

### Option A: Using APT (Recommended)
```bash
# Add Neo4j repository
wget -O - https://debian.neo4j.com/neotechnology.gpg.key | sudo apt-key add -
echo 'deb https://debian.neo4j.com stable latest' | sudo tee /etc/apt/sources.list.d/neo4j.list
sudo apt-get update

# Install Neo4j
sudo apt-get install neo4j -y

# Verify installation
neo4j version
```

### Option B: Manual Download
```bash
# Download Neo4j Community Edition
cd /tmp
wget https://dist.neo4j.com/neo4j-community-5.15.0-unix.tar.gz
tar -xzf neo4j-community-5.15.0-unix.tar.gz
sudo mv neo4j-community-5.15.0 /opt/neo4j
sudo ln -s /opt/neo4j/bin/neo4j /usr/local/bin/neo4j
```

## Step 2: Configure Neo4j

### Create Configuration File
```bash
# Backup original config
sudo cp /etc/neo4j/neo4j.conf /etc/neo4j/neo4j.conf.backup

# Apply knowledge tool configuration
sudo tee /etc/neo4j/neo4j.conf > /dev/null << 'EOF'
# Knowledge Tool Neo4j Configuration

# Network connector configuration
server.default_listen_address=0.0.0.0
server.bolt.enabled=true
server.bolt.listen_address=:7687
server.http.enabled=true
server.http.listen_address=:7474

# Database settings
initial.dbms.default_database=neo4j
dbms.security.auth_enabled=true

# Memory configuration (adjust based on available RAM)
server.memory.heap.initial_size=512m
server.memory.heap.max_size=1G
server.memory.pagecache.size=512m

# Query settings for knowledge tool
db.tx_log.rotation.retention_policy=1 days
dbms.cypher.min_replan_interval=10s
dbms.cypher.planner=cost

# Enable APOC procedures (required for schema export)
dbms.security.procedures.unrestricted=apoc.*
dbms.security.procedures.allowlist=apoc.*

# Logging
dbms.logs.query.enabled=true
dbms.logs.query.threshold=100ms
EOF
```

## Step 3: Install APOC Plugin (REQUIRED)

```bash
# Download APOC plugin matching Neo4j version
NEO4J_VERSION=$(neo4j version | grep -oP '\d+\.\d+\.\d+' | head -1)
APOC_VERSION="${NEO4J_VERSION}"

# Create plugins directory if it doesn't exist
sudo mkdir -p /var/lib/neo4j/plugins

# Download APOC
cd /var/lib/neo4j/plugins
sudo wget https://github.com/neo4j/apoc/releases/download/${APOC_VERSION}/apoc-${APOC_VERSION}-core.jar

# Set permissions
sudo chown neo4j:neo4j /var/lib/neo4j/plugins/apoc-*.jar
```

## Step 4: Initialize Database and Set Password

```bash
# Start Neo4j
sudo systemctl start neo4j

# Wait for startup
sleep 10

# Set initial password (MUST be 'password' for knowledge tool compatibility)
sudo neo4j-admin dbms set-initial-password password

# Restart to apply password
sudo systemctl restart neo4j

# Enable on boot
sudo systemctl enable neo4j
```

## Step 5: Create Knowledge Tool Schema

```bash
# Create schema initialization script
cat > /tmp/init_knowledge_schema.cypher << 'EOF'
// Knowledge Tool Schema Initialization

// Create constraints for unique IDs
CREATE CONSTRAINT knowledge_id_unique IF NOT EXISTS
FOR (k:Knowledge) REQUIRE k.knowledge_id IS UNIQUE;

// Create indexes for performance
CREATE INDEX knowledge_type_index IF NOT EXISTS
FOR (k:Knowledge) ON (k.knowledge_type);

CREATE INDEX knowledge_confidence_index IF NOT EXISTS
FOR (k:Knowledge) ON (k.confidence_score);

CREATE INDEX knowledge_timestamp_index IF NOT EXISTS
FOR (k:Knowledge) ON (k.created_at);

CREATE FULLTEXT INDEX knowledge_content_search IF NOT EXISTS
FOR (k:Knowledge) ON EACH [k.content];

// Create initial knowledge types
MERGE (t:KnowledgeType {name: 'ERROR_SOLUTION'})
MERGE (t:KnowledgeType {name: 'CODE_PATTERN'})
MERGE (t:KnowledgeType {name: 'WORKFLOW'})
MERGE (t:KnowledgeType {name: 'USER_PREFERENCE'})
MERGE (t:KnowledgeType {name: 'CONTEXT_PATTERN'})
MERGE (t:KnowledgeType {name: 'TOOL_USAGE'})

// Create relationship types structure
MERGE (r:RelationType {name: 'SIMILAR_TO'})
MERGE (r:RelationType {name: 'DERIVED_FROM'})
MERGE (r:RelationType {name: 'REQUIRES'})
MERGE (r:RelationType {name: 'CONTRADICTS'})
MERGE (r:RelationType {name: 'ENHANCES'})
MERGE (r:RelationType {name: 'RELATED_TO'});
EOF

# Apply schema
cypher-shell -u neo4j -p password < /tmp/init_knowledge_schema.cypher
```

## Step 6: Install Python Dependencies

```bash
# Install Neo4j Python driver
pip install neo4j py2neo

# Install MCP dependencies
pip install mcp

# Test connection
python3 << 'EOF'
from neo4j import GraphDatabase

uri = "bolt://localhost:7687"
driver = GraphDatabase.driver(uri, auth=("neo4j", "password"))

with driver.session() as session:
    result = session.run("MATCH (n) RETURN count(n) as count")
    print(f"Database connected. Node count: {result.single()['count']}")

    # Verify APOC is installed
    result = session.run("CALL apoc.help('export')")
    print("APOC installed successfully")

driver.close()
EOF
```

## Step 7: Configure Environment Variables

```bash
# Add to ~/.bashrc or ~/.zshrc
cat >> ~/.bashrc << 'EOF'

# Neo4j Knowledge Tool Configuration
export NEO4J_URI="bolt://localhost:7687"
export NEO4J_USER="neo4j"
export NEO4J_PASSWORD="password"
export KNOWLEDGE_DB_URI="bolt://localhost:7687"
export PYTHONPATH="${PYTHONPATH}:/home/$USER/master_root/libs"
EOF

# Reload shell
source ~/.bashrc
```

## Step 8: Test Knowledge Tool Integration

```bash
# Create test script
cat > /tmp/test_knowledge_tool.py << 'EOF'
#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.expanduser("~/master_root/libs"))

from knowledge_tool_helper import safe_knowledge_store, safe_knowledge_query

# Test storage
result = safe_knowledge_store(
    knowledge_type="TOOL_USAGE",
    content="Neo4j successfully configured for knowledge tool",
    tags=["neo4j", "setup", "test"],
    context={"environment": "WSL2", "version": "5.15.0"},
    confidence=0.95
)
print(f"Storage test: {result}")

# Test retrieval
results = safe_knowledge_query(
    query_type="search",
    query_text="Neo4j configured"
)
print(f"Retrieval test: Found {len(results)} results")
EOF

python3 /tmp/test_knowledge_tool.py
```

## Step 9: Configure MCP Server Connection

```bash
# Update .mcp.json for your project
cat > ~/.mcp.json << 'EOF'
{
  "mcpServers": {
    "knowledge": {
      "command": "python",
      "args": [
        "-m",
        "opsvi_mcp.servers.knowledge.server"
      ],
      "env": {
        "PYTHONPATH": "/home/$USER/master_root/libs",
        "NEO4J_URI": "bolt://localhost:7687",
        "NEO4J_USER": "neo4j",
        "NEO4J_PASSWORD": "password",
        "EMBEDDING_SERVICE_URL": "http://localhost:8000",
        "KNOWLEDGE_LOG_LEVEL": "INFO"
      }
    },
    "db": {
      "command": "uvx",
      "args": [
        "mcp-neo4j-cypher",
        "--db-url",
        "bolt://localhost:7687",
        "--user",
        "neo4j",
        "--password",
        "password"
      ]
    }
  }
}
EOF
```

## Step 10: Verify Complete Setup

```bash
# Run comprehensive verification
cat > /tmp/verify_setup.sh << 'EOF'
#!/bin/bash
set -e

echo "=== Neo4j Knowledge Tool Setup Verification ==="

# Check Neo4j service
if systemctl is-active --quiet neo4j; then
    echo "✓ Neo4j service running"
else
    echo "✗ Neo4j service not running"
    exit 1
fi

# Check port availability
if nc -zv localhost 7687 2>&1 | grep -q succeeded; then
    echo "✓ Bolt port 7687 accessible"
else
    echo "✗ Bolt port 7687 not accessible"
    exit 1
fi

# Check APOC installation
if cypher-shell -u neo4j -p password "CALL apoc.help('export') YIELD name RETURN count(name) as count" 2>/dev/null | grep -q count; then
    echo "✓ APOC plugin installed"
else
    echo "✗ APOC plugin not installed"
    exit 1
fi

# Check schema
CONSTRAINTS=$(cypher-shell -u neo4j -p password "SHOW CONSTRAINTS" 2>/dev/null | grep -c knowledge_id_unique || true)
if [ "$CONSTRAINTS" -gt 0 ]; then
    echo "✓ Knowledge schema initialized"
else
    echo "✗ Knowledge schema not initialized"
    exit 1
fi

# Check Python connectivity
if python3 -c "from neo4j import GraphDatabase; GraphDatabase.driver('bolt://localhost:7687', auth=('neo4j', 'password')).close()" 2>/dev/null; then
    echo "✓ Python driver connected"
else
    echo "✗ Python driver connection failed"
    exit 1
fi

echo ""
echo "=== Setup Complete! ==="
echo "Neo4j URL: bolt://localhost:7687"
echo "Username: neo4j"
echo "Password: password"
echo "Web UI: http://localhost:7474"
EOF

chmod +x /tmp/verify_setup.sh
/tmp/verify_setup.sh
```

## Troubleshooting

### If Neo4j won't start:
```bash
# Check logs
sudo journalctl -u neo4j -n 50

# Check Java version
java -version  # Must be 17+

# Check port conflicts
sudo lsof -i :7687
sudo lsof -i :7474
```

### If APOC won't load:
```bash
# Verify plugin location
ls -la /var/lib/neo4j/plugins/

# Check Neo4j logs for APOC errors
grep -i apoc /var/log/neo4j/neo4j.log
```

### If connection fails:
```bash
# Test with cypher-shell
cypher-shell -u neo4j -p password "RETURN 1"

# Check firewall
sudo ufw status

# Verify Neo4j config
grep -E "bolt|listen" /etc/neo4j/neo4j.conf
```

## Success Criteria
- [ ] Neo4j service running on port 7687
- [ ] APOC plugin installed and functional
- [ ] Knowledge schema created with constraints and indexes
- [ ] Python can connect and execute queries
- [ ] Knowledge tool helper can store and retrieve data
- [ ] MCP server configuration points to local Neo4j

## Notes
- Default credentials: neo4j/password (required for knowledge tool compatibility)
- Minimum 2GB RAM recommended for Neo4j
- APOC is MANDATORY for schema export functionality
- Bolt protocol on port 7687 is required for MCP integration
- Web UI available at http://localhost:7474 for manual inspection

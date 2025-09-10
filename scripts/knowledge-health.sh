#!/bin/bash
# Knowledge System Health Check

set -e

echo "🏥 Knowledge System Health Check"
echo "================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check Docker
echo "🐳 Docker Status:"
if docker info > /dev/null 2>&1; then
    echo -e "  ${GREEN}✓${NC} Docker is running"
else
    echo -e "  ${RED}✗${NC} Docker is not running"
    exit 1
fi

# Check Neo4j container
echo ""
echo "📊 Neo4j Database:"
if docker-compose -f docker-compose.knowledge.yml ps | grep -q "knowledge-neo4j.*Up"; then
    echo -e "  ${GREEN}✓${NC} Container is running"

    # Check Neo4j connectivity
    if docker-compose -f docker-compose.knowledge.yml exec neo4j cypher-shell -u neo4j -p password "RETURN 1" > /dev/null 2>&1; then
        echo -e "  ${GREEN}✓${NC} Database is responding"

        # Get node count
        NODE_COUNT=$(docker-compose -f docker-compose.knowledge.yml exec neo4j cypher-shell -u neo4j -p password "MATCH (n:Knowledge) RETURN count(n) as count" 2>/dev/null | grep -oE '[0-9]+' | tail -1)
        echo -e "  📈 Knowledge nodes: ${NODE_COUNT:-0}"

        # Get relationship count
        REL_COUNT=$(docker-compose -f docker-compose.knowledge.yml exec neo4j cypher-shell -u neo4j -p password "MATCH ()-[r]->() RETURN count(r) as count" 2>/dev/null | grep -oE '[0-9]+' | tail -1)
        echo -e "  🔗 Relationships: ${REL_COUNT:-0}"
    else
        echo -e "  ${RED}✗${NC} Database not responding"
    fi

    # Check port
    if nc -zv localhost 7687 2>/dev/null | grep -q succeeded; then
        echo -e "  ${GREEN}✓${NC} Bolt port 7687 is accessible"
    else
        echo -e "  ${YELLOW}⚠${NC} Bolt port 7687 not accessible"
    fi
else
    echo -e "  ${RED}✗${NC} Container is not running"
fi

# Check Embedding Service
echo ""
echo "🧠 Embedding Service:"
if docker-compose -f docker-compose.knowledge.yml ps | grep -q "knowledge-embedding.*Up"; then
    echo -e "  ${GREEN}✓${NC} Container is running"

    # Check API health
    if curl -s -f http://localhost:8000/health > /dev/null 2>&1; then
        echo -e "  ${GREEN}✓${NC} API is responding"

        # Get service info
        HEALTH=$(curl -s http://localhost:8000/health)
        if [ -n "$HEALTH" ]; then
            echo "  📊 Status: $(echo $HEALTH | jq -r '.status' 2>/dev/null || echo 'unknown')"
            echo "  🤖 Model: $(echo $HEALTH | jq -r '.model' 2>/dev/null || echo 'unknown')"
            echo "  📐 Dimension: $(echo $HEALTH | jq -r '.dimension' 2>/dev/null || echo 'unknown')"
        fi
    else
        echo -e "  ${RED}✗${NC} API not responding"
    fi
else
    echo -e "  ${RED}✗${NC} Container is not running"
fi

# Check disk space
echo ""
echo "💾 Disk Usage:"
DISK_USAGE=$(df -h /var/lib/docker 2>/dev/null | awk 'NR==2 {print $5}' | sed 's/%//')
if [ -n "$DISK_USAGE" ]; then
    if [ "$DISK_USAGE" -lt 80 ]; then
        echo -e "  ${GREEN}✓${NC} Docker storage: ${DISK_USAGE}% used"
    elif [ "$DISK_USAGE" -lt 90 ]; then
        echo -e "  ${YELLOW}⚠${NC} Docker storage: ${DISK_USAGE}% used (getting full)"
    else
        echo -e "  ${RED}✗${NC} Docker storage: ${DISK_USAGE}% used (critical)"
    fi
fi

# Check backups
echo ""
echo "💾 Backup Status:"
BACKUP_DIR="/home/opsvi/master_root/knowledge-backups"
if [ -d "$BACKUP_DIR" ]; then
    LATEST_BACKUP=$(ls -t "$BACKUP_DIR"/*.tar.gz 2>/dev/null | head -1)
    if [ -n "$LATEST_BACKUP" ]; then
        BACKUP_AGE=$(( ($(date +%s) - $(stat -c %Y "$LATEST_BACKUP")) / 3600 ))
        BACKUP_SIZE=$(du -h "$LATEST_BACKUP" | cut -f1)
        echo "  📦 Latest: $(basename "$LATEST_BACKUP")"
        echo "  ⏰ Age: ${BACKUP_AGE} hours ago"
        echo "  📊 Size: ${BACKUP_SIZE}"

        if [ "$BACKUP_AGE" -lt 24 ]; then
            echo -e "  ${GREEN}✓${NC} Backup is recent"
        else
            echo -e "  ${YELLOW}⚠${NC} Backup is ${BACKUP_AGE} hours old"
        fi
    else
        echo -e "  ${YELLOW}⚠${NC} No backups found"
    fi
fi

# Check MCP configuration
echo ""
echo "🔌 MCP Configuration:"
if [ -f "/home/opsvi/master_root/.mcp.json" ]; then
    echo -e "  ${GREEN}✓${NC} .mcp.json exists"

    # Check if knowledge server is configured
    if grep -q "knowledge" /home/opsvi/master_root/.mcp.json; then
        echo -e "  ${GREEN}✓${NC} Knowledge server configured"
    else
        echo -e "  ${RED}✗${NC} Knowledge server not configured"
    fi
else
    echo -e "  ${RED}✗${NC} .mcp.json not found"
fi

# Overall status
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
NEO4J_OK=false
EMBEDDING_OK=false

if docker-compose -f docker-compose.knowledge.yml ps | grep -q "knowledge-neo4j.*Up" && \
   docker-compose -f docker-compose.knowledge.yml exec neo4j cypher-shell -u neo4j -p password "RETURN 1" > /dev/null 2>&1; then
    NEO4J_OK=true
fi

if docker-compose -f docker-compose.knowledge.yml ps | grep -q "knowledge-embedding.*Up" && \
   curl -s -f http://localhost:8000/health > /dev/null 2>&1; then
    EMBEDDING_OK=true
fi

if [ "$NEO4J_OK" = true ] && [ "$EMBEDDING_OK" = true ]; then
    echo -e "${GREEN}✅ System Status: HEALTHY${NC}"
    echo "All services are running properly"
elif [ "$NEO4J_OK" = true ] || [ "$EMBEDDING_OK" = true ]; then
    echo -e "${YELLOW}⚠️  System Status: DEGRADED${NC}"
    echo "Some services need attention"
else
    echo -e "${RED}❌ System Status: DOWN${NC}"
    echo "Services are not running"
    echo ""
    echo "To start the system, run:"
    echo "  ./start-knowledge-system.sh"
fi

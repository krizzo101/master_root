#!/bin/bash
#
# Deploy Phase 1: Shadow Mode with KB Storage
#

echo "=== Enhanced Thinking Tool - Phase 1 Deployment ==="
echo ""

# Configuration
TRIAGE_PORT=${TRIAGE_PORT:-8101}
TRIAGE_MODE=${TRIAGE_MODE:-shadow}
PYTHONPATH="/home/opsvi/master_root:$PYTHONPATH"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to check if service is running
check_service() {
    if curl -s "http://localhost:$TRIAGE_PORT/health" > /dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# Step 1: Kill any existing triage service
echo -e "${YELLOW}[1/5] Stopping existing services...${NC}"
pkill -f "enhanced_triage_api.py" 2>/dev/null || true
pkill -f "triage_api.py" 2>/dev/null || true
sleep 2

# Step 2: Set up environment
echo -e "${YELLOW}[2/5] Setting up environment...${NC}"
export PYTHONPATH="/home/opsvi/master_root:$PYTHONPATH"
export TRIAGE_MODE="shadow"
export TRIAGE_SERVICE_URL="http://localhost:$TRIAGE_PORT"
export TRIAGE_ENABLED="true"

# Neo4j connection (if not already set)
export NEO4J_URI=${NEO4J_URI:-"bolt://localhost:7687"}
export NEO4J_USER=${NEO4J_USER:-"neo4j"}
export NEO4J_PASSWORD=${NEO4J_PASSWORD:-"password"}

echo "  Mode: $TRIAGE_MODE"
echo "  Port: $TRIAGE_PORT"
echo "  KB: $NEO4J_URI"

# Step 3: Start enhanced triage service
echo -e "${YELLOW}[3/5] Starting enhanced triage service...${NC}"
cd /home/opsvi/master_root/apps/thinking-supervisor/triage-service

# Start in background
nohup /home/opsvi/miniconda/bin/python enhanced_triage_api.py > triage.log 2>&1 &
TRIAGE_PID=$!

echo "  PID: $TRIAGE_PID"
echo "  Log: triage-service/triage.log"

# Wait for service to start
echo -e "${YELLOW}[4/5] Waiting for service to start...${NC}"
for i in {1..10}; do
    if check_service; then
        echo -e "${GREEN}  Service is running!${NC}"
        break
    fi
    echo "  Attempt $i/10..."
    sleep 2
done

if ! check_service; then
    echo -e "${RED}  Failed to start service!${NC}"
    echo "  Check logs: tail -f triage-service/triage.log"
    exit 1
fi

# Step 5: Run validation
echo -e "${YELLOW}[5/5] Running validation tests...${NC}"

# Test health endpoint
HEALTH=$(curl -s "http://localhost:$TRIAGE_PORT/health")
echo "  Health: $HEALTH"

# Test analysis endpoint
TEST_THOUGHT='{"thought": "You are absolutely right about that approach", "thought_number": 1, "session_id": "deploy_test", "context": {}, "history": []}'

RESULT=$(curl -s -X POST "http://localhost:$TRIAGE_PORT/analyze" \
    -H "Content-Type: application/json" \
    -d "$TEST_THOUGHT")

if echo "$RESULT" | grep -q "agreeability"; then
    echo -e "${GREEN}  Pattern detection: Working${NC}"
else
    echo -e "${RED}  Pattern detection: Failed${NC}"
fi

if echo "$RESULT" | grep -q "kb_stored"; then
    echo -e "${GREEN}  KB storage: Enabled${NC}"
else
    echo -e "${YELLOW}  KB storage: Check configuration${NC}"
fi

# Summary
echo ""
echo "=== Deployment Complete ==="
echo ""
echo "Service URL: http://localhost:$TRIAGE_PORT"
echo "Mode: $TRIAGE_MODE (shadow - non-invasive)"
echo ""
echo "To view logs:"
echo "  tail -f apps/thinking-supervisor/triage-service/triage.log"
echo ""
echo "To check metrics:"
echo "  curl http://localhost:$TRIAGE_PORT/health"
echo ""
echo "To stop service:"
echo "  kill $TRIAGE_PID"
echo ""
echo "Next steps:"
echo "1. Monitor shadow mode data collection"
echo "2. Query KB for stored patterns:"
echo "   mcp__knowledge__knowledge_query(query_type='by_type', knowledge_type='THINKING_PATTERN')"
echo "3. After sufficient data, move to advisory mode:"
echo "   export TRIAGE_MODE=advisory && ./deploy_phase1.sh"
echo ""

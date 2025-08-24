#!/bin/bash
# Deploy Intelligent Triage Service

set -e

echo "Deploying Intelligent Triage Service..."

# Set environment variables
export TRIAGE_MODE="${1:-shadow}"  # Default to shadow mode
export TRIAGE_PORT=8102
export PYTHONPATH="/home/opsvi/master_root/libs:/home/opsvi/master_root/apps"
export NEO4J_URI="bolt://localhost:7687"
export NEO4J_USER="neo4j"
export NEO4J_PASSWORD="password"

# Check for OpenAI API key
if [ -z "$OPENAI_API_KEY" ]; then
    echo "Warning: OPENAI_API_KEY not set. Triage will not be able to analyze thoughts."
    echo "Set with: export OPENAI_API_KEY='your-key'"
fi

# Install dependencies
echo "Installing dependencies..."
/home/opsvi/miniconda/bin/pip install fastapi uvicorn httpx fastmcp pydantic -q

# Kill any existing process on the port
echo "Checking for existing service..."
if lsof -Pi :$TRIAGE_PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "Stopping existing service on port $TRIAGE_PORT..."
    kill $(lsof -Pi :$TRIAGE_PORT -sTCP:LISTEN -t) 2>/dev/null || true
    sleep 2
fi

# Start the service
echo "Starting Intelligent Triage Service in $TRIAGE_MODE mode..."
cd /home/opsvi/master_root/apps/thinking-supervisor/triage-service

nohup /home/opsvi/miniconda/bin/python intelligent_triage.py > triage.log 2>&1 &
TRIAGE_PID=$!

echo "Intelligent Triage Service started with PID: $TRIAGE_PID"
echo "Logs: apps/thinking-supervisor/triage-service/triage.log"

# Wait for service to be ready
sleep 3

# Test health endpoint
echo "Testing service health..."
if curl -s http://localhost:$TRIAGE_PORT/health | grep -q "healthy"; then
    echo "✓ Service is healthy and running in $TRIAGE_MODE mode"
    echo ""
    echo "Service details:"
    curl -s http://localhost:$TRIAGE_PORT/health | /home/opsvi/miniconda/bin/python -m json.tool
else
    echo "✗ Service health check failed"
    exit 1
fi

echo ""
echo "Deployment complete!"
echo ""
echo "Key features of Intelligent Triage:"
echo "- Uses AI model (gpt-4o-mini) for analysis, not regex"
echo "- Loads KB instructions on every analysis"
echo "- Detects reflexive agreement before fact-checking"
echo "- Identifies complex topics needing consult suite"
echo "- Reminds about forgotten rules/instructions"
echo "- Stores patterns in KB via MCP"
echo ""
echo "To test manually:"
echo 'curl -X POST http://localhost:8102/analyze -H "Content-Type: application/json" -d @test_thought.json'

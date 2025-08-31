#!/bin/bash
#
# HECATON Run Script - Execute parallel Claude agents
#
# Usage:
#   ./run.sh [task] [num_agents]
#
# Examples:
#   ./run.sh "Build a REST API" 2
#   ./run.sh "Add tests for authentication" 3
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}==============================================================${NC}"
echo -e "${BLUE}                    HECATON PARALLEL EXECUTION                 ${NC}"
echo -e "${BLUE}==============================================================${NC}\n"

# Check for Claude Code tokens
TOKEN_COUNT=0
for i in {1..15}; do
    if [ ! -z "${!CLAUDE_CODE_TOKEN_$i}" ]; then
        TOKEN_COUNT=$((TOKEN_COUNT + 1))
    fi
done

if [ $TOKEN_COUNT -eq 0 ]; then
    echo -e "${RED}❌ Error: No CLAUDE_CODE_TOKEN_* environment variables found${NC}"
    echo -e "${YELLOW}Set your tokens like this:${NC}"
    echo "  export CLAUDE_CODE_TOKEN_1='your-token-1'"
    echo "  export CLAUDE_CODE_TOKEN_2='your-token-2'"
    echo ""
    echo "You need at least 2 tokens for parallel execution."
    exit 1
fi

echo -e "${GREEN}✅ Found $TOKEN_COUNT Claude Code tokens${NC}\n"

# Ensure ANTHROPIC_API_KEY is NOT set (as requested)
unset ANTHROPIC_API_KEY

# Get task and agent count
TASK="${1:-Create a simple Python calculator function with tests}"
NUM_AGENTS="${2:-2}"

echo -e "${YELLOW}Task:${NC} $TASK"
echo -e "${YELLOW}Agents:${NC} $NUM_AGENTS"
echo ""

# Check dependencies
if ! python3 -c "import langgraph" 2>/dev/null; then
    echo -e "${YELLOW}⚠️  LangGraph not installed. Installing...${NC}"
    pip install langgraph
fi

# Run HECATON
echo -e "${GREEN}🚀 Starting HECATON...${NC}\n"
cd "$(dirname "$0")"

python3 -m src.hecaton run "$TASK" --agents "$NUM_AGENTS" --mode send-api --verbose

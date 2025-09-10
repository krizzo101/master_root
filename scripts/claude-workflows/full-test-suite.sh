#!/bin/bash
# Full Test Suite Automation
# Runs complete testing pipeline with coverage and reporting

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

PROJECT_ROOT="/home/opsvi/master_root"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
REPORT_DIR="$PROJECT_ROOT/test-reports/$TIMESTAMP"

echo -e "${GREEN}=== Full Test Suite Automation ===${NC}"
echo "Timestamp: $TIMESTAMP"
echo ""

# Create report directory
mkdir -p "$REPORT_DIR"

# Function to run tests for a directory
run_tests() {
    local dir=$1
    local name=$2

    echo -e "${YELLOW}Testing $name...${NC}"

    if [ -d "$dir" ]; then
        # Run pytest with coverage
        pytest "$dir" \
            --cov="$dir" \
            --cov-report=html:"$REPORT_DIR/coverage-$name" \
            --cov-report=term-missing \
            --html="$REPORT_DIR/report-$name.html" \
            --self-contained-html \
            -v 2>&1 | tee "$REPORT_DIR/test-$name.log"

        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✓ $name tests passed${NC}"
        else
            echo -e "${RED}✗ $name tests failed${NC}"
            return 1
        fi
    else
        echo "Skipping $name (directory not found)"
    fi
}

# Run tests for each component
run_tests "$PROJECT_ROOT/apps/ACCF" "ACCF"
run_tests "$PROJECT_ROOT/apps/thinking-supervisor" "Thinking-Supervisor"
run_tests "$PROJECT_ROOT/libs/opsvi_mcp" "OPSVI-MCP"

# Type checking
echo -e "${YELLOW}Running type checking...${NC}"
mypy "$PROJECT_ROOT" --ignore-missing-imports --html-report "$REPORT_DIR/mypy" 2>&1 | tee "$REPORT_DIR/mypy.log"

# Linting
echo -e "${YELLOW}Running linting...${NC}"
ruff check "$PROJECT_ROOT" --output-format json > "$REPORT_DIR/ruff.json" 2>&1

# Security scanning
echo -e "${YELLOW}Running security scan...${NC}"
bandit -r "$PROJECT_ROOT" -f json -o "$REPORT_DIR/bandit.json" 2>/dev/null || true

# Generate summary
cat > "$REPORT_DIR/summary.md" << EOF
# Test Suite Summary
**Date**: $(date '+%Y-%m-%d %H:%M:%S')
**Project**: Master Root

## Results
- ACCF Tests: [View Report](report-ACCF.html)
- Thinking Supervisor Tests: [View Report](report-Thinking-Supervisor.html)
- OPSVI MCP Tests: [View Report](report-OPSVI-MCP.html)

## Coverage Reports
- [ACCF Coverage](coverage-ACCF/index.html)
- [Thinking Supervisor Coverage](coverage-Thinking-Supervisor/index.html)
- [OPSVI MCP Coverage](coverage-OPSVI-MCP/index.html)

## Code Quality
- [Type Checking Report](mypy/index.html)
- [Linting Report](ruff.json)
- [Security Report](bandit.json)
EOF

echo ""
echo -e "${GREEN}=== Test Suite Complete ===${NC}"
echo "Reports saved to: $REPORT_DIR"
echo "Open $REPORT_DIR/summary.md for full results"

#!/bin/bash
# SDLC Preflight Check - MANDATORY before any SDLC project
# This script MUST pass before proceeding with any development

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "====================================="
echo "SDLC PREFLIGHT CHECK - MANDATORY"
echo "====================================="

ERRORS=0
WARNINGS=0

# 1. CHECK: Not on main/master branch
BRANCH=$(git branch --show-current)
if [[ "$BRANCH" == "main" ]] || [[ "$BRANCH" == "master" ]]; then
    echo -e "${RED}✗ FAIL: On main branch. Create feature branch first!${NC}"
    echo "  Run: git checkout -b feature/<project-name>"
    ERRORS=$((ERRORS + 1))
else
    echo -e "${GREEN}✓ On feature branch: $BRANCH${NC}"
fi

# 2. CHECK: Project directory NOT in .gitignore
if [ $# -eq 0 ]; then
    echo -e "${YELLOW}⚠ Warning: No project path provided${NC}"
    echo "  Usage: $0 <project-path>"
    WARNINGS=$((WARNINGS + 1))
else
    PROJECT_PATH="$1"
    PROJECT_DIR=$(dirname "$PROJECT_PATH")

    # Check if apps/ or libs/ is gitignored
    if grep -q "^apps/$" .gitignore 2>/dev/null; then
        echo -e "${RED}✗ CRITICAL: apps/ directory is in .gitignore!${NC}"
        echo "  Your code will NEVER be committed!"
        echo "  Fix: Remove 'apps/' from .gitignore"
        ERRORS=$((ERRORS + 1))
    fi

    if grep -q "^libs/$" .gitignore 2>/dev/null; then
        echo -e "${RED}✗ CRITICAL: libs/ directory is in .gitignore!${NC}"
        echo "  Your code will NEVER be committed!"
        echo "  Fix: Remove 'libs/' from .gitignore"
        ERRORS=$((ERRORS + 1))
    fi

    # Check specific project path
    if echo "$PROJECT_PATH" | grep -q "^apps/" || echo "$PROJECT_PATH" | grep -q "^libs/"; then
        if git check-ignore "$PROJECT_PATH" 2>/dev/null; then
            echo -e "${RED}✗ CRITICAL: $PROJECT_PATH is gitignored!${NC}"
            ERRORS=$((ERRORS + 1))
        else
            echo -e "${GREEN}✓ Project path is tracked by git${NC}"
        fi
    fi
fi

# 3. CHECK: Agent profiles exist
PROFILES=("sdlc-discovery" "sdlc-design" "sdlc-planning" "sdlc-development" "sdlc-testing" "sdlc-deployment" "sdlc-production" "sdlc-postmortem")
MISSING_PROFILES=0

for profile in "${PROFILES[@]}"; do
    if [ ! -f ".claude/agents/${profile}.md" ]; then
        echo -e "${RED}✗ Missing agent profile: ${profile}.md${NC}"
        MISSING_PROFILES=$((MISSING_PROFILES + 1))
    fi
done

if [ $MISSING_PROFILES -eq 0 ]; then
    echo -e "${GREEN}✓ All agent profiles present${NC}"
else
    ERRORS=$((ERRORS + 1))
fi

# 4. CHECK: MCP tools available
echo -e "${YELLOW}ℹ Checking MCP tool availability...${NC}"
echo "  Required: knowledge, resource_discovery, web_search"
echo "  (Manual verification needed in Claude)"

# 5. CHECK: No uncommitted changes (clean start)
if [ -n "$(git status --porcelain)" ]; then
    echo -e "${YELLOW}⚠ Warning: Uncommitted changes exist${NC}"
    echo "  Consider: git add -A && git commit -m 'checkpoint'"
    WARNINGS=$((WARNINGS + 1))
else
    echo -e "${GREEN}✓ Working directory clean${NC}"
fi

# FINAL VERDICT
echo "====================================="
if [ $ERRORS -gt 0 ]; then
    echo -e "${RED}PREFLIGHT FAILED: $ERRORS critical issues found${NC}"
    echo -e "${RED}DO NOT PROCEED until all issues are fixed${NC}"
    exit 1
elif [ $WARNINGS -gt 0 ]; then
    echo -e "${YELLOW}PREFLIGHT PASSED with $WARNINGS warnings${NC}"
    echo "Review warnings before proceeding"
else
    echo -e "${GREEN}PREFLIGHT PASSED - Ready for SDLC${NC}"
fi

echo "====================================="
echo "NEXT STEPS:"
echo "1. Load discovery profile: Read('.claude/agents/sdlc-discovery.md')"
echo "2. Use knowledge_query to check for existing solutions"
echo "3. Use resource_discovery to check libs/"
echo "4. Create requirements document"
echo "====================================="

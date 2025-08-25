#!/bin/bash
# Automated Code Review Workflow
# Comprehensive code quality and security analysis

set -e

PROJECT_ROOT="/home/opsvi/master_root"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
REVIEW_DIR="$PROJECT_ROOT/code-reviews/$TIMESTAMP"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}=== Automated Code Review ===${NC}"
echo "Starting comprehensive review at $TIMESTAMP"
echo ""

mkdir -p "$REVIEW_DIR"

# Function to check Python files
review_python() {
    echo -e "${YELLOW}Reviewing Python code...${NC}"

    # Complexity analysis
    echo "Analyzing complexity..."
    radon cc "$PROJECT_ROOT" -s -j > "$REVIEW_DIR/complexity.json" 2>/dev/null || true

    # Maintainability index
    radon mi "$PROJECT_ROOT" -s > "$REVIEW_DIR/maintainability.txt" 2>/dev/null || true

    # Code duplication
    echo "Checking for duplicates..."
    pylint "$PROJECT_ROOT" --disable=all --enable=duplicate-code > "$REVIEW_DIR/duplicates.txt" 2>/dev/null || true

    # Style violations
    echo "Checking style..."
    flake8 "$PROJECT_ROOT" --output-file="$REVIEW_DIR/style.txt" 2>/dev/null || true

    # Type checking
    echo "Type checking..."
    mypy "$PROJECT_ROOT" --html-report "$REVIEW_DIR/types" 2>/dev/null || true
}

# Function to check JavaScript/TypeScript
review_javascript() {
    echo -e "${YELLOW}Reviewing JavaScript/TypeScript...${NC}"

    if command -v eslint &> /dev/null; then
        eslint "$PROJECT_ROOT" --format json -o "$REVIEW_DIR/eslint.json" 2>/dev/null || true
    fi
}

# Function to check security
review_security() {
    echo -e "${YELLOW}Security review...${NC}"

    # Python security
    bandit -r "$PROJECT_ROOT" -f json -o "$REVIEW_DIR/security-python.json" 2>/dev/null || true

    # Check for secrets
    echo "Scanning for secrets..."
    grep -r -E "(password|secret|token|key)\\s*=\\s*['\"][^'\"]+['\"]" "$PROJECT_ROOT" \
        --exclude-dir=.git \
        --exclude-dir=node_modules \
        --exclude-dir=__pycache__ > "$REVIEW_DIR/potential-secrets.txt" 2>/dev/null || true

    # Dependency vulnerabilities
    if [ -f "$PROJECT_ROOT/requirements.txt" ]; then
        pip-audit -r "$PROJECT_ROOT/requirements.txt" -f json -o "$REVIEW_DIR/dependencies.json" 2>/dev/null || true
    fi
}

# Function to analyze git history
review_git() {
    echo -e "${YELLOW}Git history analysis...${NC}"

    cd "$PROJECT_ROOT"

    # Recent changes
    git log --oneline -20 > "$REVIEW_DIR/recent-commits.txt"

    # File churn (most changed files)
    git log --format=format: --name-only | sort | uniq -c | sort -rg | head -20 > "$REVIEW_DIR/file-churn.txt"

    # Contributors
    git shortlog -sn > "$REVIEW_DIR/contributors.txt"

    # Uncommitted changes
    git status --porcelain > "$REVIEW_DIR/uncommitted.txt"
}

# Function to generate metrics
generate_metrics() {
    echo -e "${YELLOW}Generating metrics...${NC}"

    # Count lines of code
    echo "Lines of Code:" > "$REVIEW_DIR/metrics.txt"
    find "$PROJECT_ROOT" -type f -name "*.py" -exec wc -l {} + | tail -1 >> "$REVIEW_DIR/metrics.txt"
    find "$PROJECT_ROOT" -type f -name "*.js" -o -name "*.ts" -exec wc -l {} + | tail -1 >> "$REVIEW_DIR/metrics.txt"

    # Count files
    echo "" >> "$REVIEW_DIR/metrics.txt"
    echo "File counts:" >> "$REVIEW_DIR/metrics.txt"
    echo "Python files: $(find "$PROJECT_ROOT" -name "*.py" | wc -l)" >> "$REVIEW_DIR/metrics.txt"
    echo "JavaScript files: $(find "$PROJECT_ROOT" -name "*.js" | wc -l)" >> "$REVIEW_DIR/metrics.txt"
    echo "TypeScript files: $(find "$PROJECT_ROOT" -name "*.ts" | wc -l)" >> "$REVIEW_DIR/metrics.txt"
}

# Run all reviews
review_python
review_javascript
review_security
review_git
generate_metrics

# Generate summary report
cat > "$REVIEW_DIR/REVIEW_SUMMARY.md" << EOF
# Code Review Summary
**Date**: $(date '+%Y-%m-%d %H:%M:%S')
**Project**: Master Root

## Analysis Results

### Code Quality
- [Complexity Analysis](complexity.json)
- [Maintainability Index](maintainability.txt)
- [Code Duplication](duplicates.txt)
- [Style Violations](style.txt)
- [Type Checking](types/index.html)

### Security
- [Python Security Issues](security-python.json)
- [Potential Secrets](potential-secrets.txt)
- [Dependency Vulnerabilities](dependencies.json)

### Repository
- [Recent Commits](recent-commits.txt)
- [File Churn](file-churn.txt)
- [Contributors](contributors.txt)
- [Uncommitted Changes](uncommitted.txt)

### Metrics
$(cat "$REVIEW_DIR/metrics.txt")

## Recommendations
1. Review and fix security issues immediately
2. Address high complexity functions
3. Remove code duplications
4. Fix type errors
5. Clean up style violations

## Next Steps
- [ ] Fix critical security issues
- [ ] Refactor complex code
- [ ] Add missing type hints
- [ ] Update dependencies
- [ ] Document undocumented functions
EOF

echo ""
echo -e "${GREEN}=== Code Review Complete ===${NC}"
echo "Review saved to: $REVIEW_DIR"
echo "Summary: $REVIEW_DIR/REVIEW_SUMMARY.md"

# Open summary if possible
if command -v xdg-open &> /dev/null; then
    xdg-open "$REVIEW_DIR/REVIEW_SUMMARY.md" 2>/dev/null || true
fi

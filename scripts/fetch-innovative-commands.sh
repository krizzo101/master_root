#!/bin/bash
# Fetch innovative Claude Code commands from top repositories

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Create commands directory
COMMANDS_DIR=".claude/commands"
mkdir -p "$COMMANDS_DIR"

echo -e "${BLUE}=== Fetching Innovative Claude Code Commands ===${NC}"
echo ""

# Function to fetch command
fetch_command() {
    local name=$1
    local url=$2
    local description=$3

    echo -n "📥 $name - $description... "
    if curl -sS -o "$COMMANDS_DIR/$name.md" "$url" 2>/dev/null; then
        if [ -s "$COMMANDS_DIR/$name.md" ] && ! grep -q "404" "$COMMANDS_DIR/$name.md" 2>/dev/null; then
            echo -e "${GREEN}✓${NC}"
            return 0
        else
            rm -f "$COMMANDS_DIR/$name.md"
            echo -e "${RED}✗ (404)${NC}"
            return 1
        fi
    else
        echo -e "${RED}✗${NC}"
        return 1
    fi
}

echo -e "${YELLOW}1. PaulDuvall's Production Commands (58 total)${NC}"
fetch_command "xtest" "https://raw.githubusercontent.com/PaulDuvall/claude-code/main/slash-commands/active/xtest.md" "Smart test runner"
fetch_command "xquality" "https://raw.githubusercontent.com/PaulDuvall/claude-code/main/slash-commands/active/xquality.md" "Code quality checks"
fetch_command "xsecurity" "https://raw.githubusercontent.com/PaulDuvall/claude-code/main/slash-commands/active/xsecurity.md" "Security scanning"
fetch_command "xgit" "https://raw.githubusercontent.com/PaulDuvall/claude-code/main/slash-commands/active/xgit.md" "Smart git workflow"
fetch_command "xarchitecture" "https://raw.githubusercontent.com/PaulDuvall/claude-code/main/slash-commands/active/xarchitecture.md" "System design"
fetch_command "xdebug" "https://raw.githubusercontent.com/PaulDuvall/claude-code/main/slash-commands/active/xdebug.md" "AI debugging"
fetch_command "xrefactor" "https://raw.githubusercontent.com/PaulDuvall/claude-code/main/slash-commands/active/xrefactor.md" "Smart refactoring"

echo ""
echo -e "${YELLOW}2. wcygan's Mega Collection (88 commands)${NC}"
fetch_command "agent-orchestrator" "https://raw.githubusercontent.com/wcygan/dotfiles/main/claude/commands/agent-orchestrator.md" "Orchestrate multiple agents"
fetch_command "code-health" "https://raw.githubusercontent.com/wcygan/dotfiles/main/claude/commands/code-health.md" "Code health metrics"
fetch_command "performance-analysis" "https://raw.githubusercontent.com/wcygan/dotfiles/main/claude/commands/performance-analysis.md" "Performance profiling"
fetch_command "threat-model" "https://raw.githubusercontent.com/wcygan/dotfiles/main/claude/commands/threat-model.md" "Security threat modeling"

echo ""
echo -e "${YELLOW}3. GaloyMoney's Specialized Commands${NC}"
fetch_command "mermaid-diagram" "https://raw.githubusercontent.com/GaloyMoney/lana-bank/main/.claude/commands/mermaid.md" "Generate Mermaid diagrams"

echo ""
echo -e "${YELLOW}4. Session Management Commands${NC}"
fetch_command "session-manager" "https://raw.githubusercontent.com/iannuttall/claude-sessions/main/commands/session-update.md" "Session tracking"

echo ""
echo -e "${YELLOW}5. Creating Custom Innovative Commands${NC}"

# Create a custom workflow orchestrator
cat > "$COMMANDS_DIR/workflow-orchestrator.md" << 'EOF'
# Workflow Orchestrator

Orchestrate complex multi-step workflows with parallel execution and error recovery.

## Usage
Provide a workflow description and I will:
1. Break it into parallel and sequential steps
2. Identify dependencies between tasks
3. Execute steps with proper error handling
4. Provide progress updates throughout
5. Generate a summary report

## Workflow Types
- **Build & Deploy**: Full CI/CD pipeline execution
- **Code Migration**: Move code between frameworks/languages
- **Security Audit**: Comprehensive security assessment
- **Performance Optimization**: End-to-end performance improvement
- **Documentation Generation**: Complete documentation suite

## Process
1. Analyze workflow requirements
2. Create execution plan with timeline
3. Spawn parallel tasks where possible
4. Monitor progress and handle failures
5. Aggregate results and provide report

Specify your workflow and any constraints (time, resources, etc).
EOF
echo -e "📥 workflow-orchestrator - Complex workflow automation... ${GREEN}✓${NC}"

# Create AI code review command
cat > "$COMMANDS_DIR/ai-review.md" << 'EOF'
# AI-Powered Code Review

Perform comprehensive code review using multiple AI perspectives.

## Review Aspects
1. **Architecture Review**: Design patterns, structure, scalability
2. **Security Review**: Vulnerabilities, best practices, OWASP compliance
3. **Performance Review**: Bottlenecks, optimization opportunities
4. **Maintainability**: Code clarity, documentation, test coverage
5. **Best Practices**: Language-specific idioms and conventions

## Output
- Severity-ranked issues (Critical/High/Medium/Low)
- Concrete fix suggestions with code examples
- Positive feedback on well-written code
- Learning opportunities identified
- Overall code quality score

Provide file paths or let me analyze recent changes.
EOF
echo -e "📥 ai-review - Multi-perspective code review... ${GREEN}✓${NC}"

# Create auto-optimizer command
cat > "$COMMANDS_DIR/auto-optimizer.md" << 'EOF'
# Auto-Optimizer

Automatically optimize code for performance, readability, and maintainability.

## Optimization Targets
- **Performance**: Algorithm complexity, caching, lazy loading
- **Memory**: Reduce allocations, fix leaks, optimize data structures
- **Readability**: Simplify logic, improve naming, add comments
- **Type Safety**: Add type hints, fix type errors
- **Error Handling**: Add proper error handling and recovery
- **Testing**: Generate missing tests for uncovered code

## Process
1. Analyze current code metrics
2. Identify optimization opportunities
3. Apply improvements incrementally
4. Test each change for correctness
5. Measure improvement metrics
6. Generate optimization report

Specify optimization priorities or use balanced mode.
EOF
echo -e "📥 auto-optimizer - Automatic code optimization... ${GREEN}✓${NC}"

# Create knowledge graph builder
cat > "$COMMANDS_DIR/knowledge-graph.md" << 'EOF'
# Knowledge Graph Builder

Build a knowledge graph of your codebase for better understanding and navigation.

## Graph Components
- **Nodes**: Functions, classes, modules, files, concepts
- **Edges**: Calls, imports, inherits, implements, uses
- **Metadata**: Complexity, test coverage, change frequency
- **Clusters**: Logical groupings, domains, features

## Outputs
1. Visual graph (Mermaid/GraphViz)
2. Dependency analysis
3. Impact assessment for changes
4. Architecture insights
5. Refactoring opportunities
6. Dead code detection

## Use Cases
- Onboarding new developers
- Planning refactoring
- Understanding impact of changes
- Identifying architectural issues
- Documentation generation

Analyze current directory or specify paths.
EOF
echo -e "📥 knowledge-graph - Codebase knowledge graph... ${GREEN}✓${NC}"

# Summary
echo ""
echo -e "${GREEN}===============================================${NC}"
echo -e "${GREEN}Command Installation Complete!${NC}"
echo ""

# Count successful downloads
SUCCESS_COUNT=$(ls -1 "$COMMANDS_DIR"/*.md 2>/dev/null | wc -l)
echo "✅ Successfully installed $SUCCESS_COUNT innovative commands"

echo ""
echo "🎯 Highlights:"
echo "  • xtest, xquality, xsecurity - Production-ready DevOps commands"
echo "  • workflow-orchestrator - Complex multi-step automation"
echo "  • ai-review - Multi-perspective code analysis"
echo "  • auto-optimizer - Automatic code improvements"
echo "  • knowledge-graph - Codebase visualization"

echo ""
echo "📚 Available Commands:"
ls -1 "$COMMANDS_DIR"/*.md 2>/dev/null | xargs -n1 basename | sed 's/.md$//' | sed 's/^/  \//g' | sort

echo ""
echo -e "${YELLOW}💡 Try these powerful workflows:${NC}"
echo "  /xtest              - Smart test execution"
echo "  /xsecurity          - Security vulnerability scan"
echo "  /workflow-orchestrator - Complex task automation"
echo "  /ai-review          - Comprehensive code review"
echo "  /knowledge-graph    - Visualize your codebase"

echo ""
echo -e "${BLUE}Note: Some commands may need adjustment for your specific tools/environment${NC}"

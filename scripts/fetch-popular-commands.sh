#!/bin/bash
# Fetch popular Claude Code slash commands from various repositories

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Create commands directory
COMMANDS_DIR=".claude/commands"
mkdir -p "$COMMANDS_DIR"

echo -e "${GREEN}Fetching popular Claude Code commands...${NC}"

# Define commands to fetch with their sources
declare -A COMMANDS=(
    # Context and priming
    ["context-prime"]="https://raw.githubusercontent.com/elizaOS/elizaos.github.io/main/.claude/commands/context-prime.md"
    ["prime"]="https://raw.githubusercontent.com/yzyydev/AI-Engineering-Structure/main/.claude/commands/prime.md"

    # Documentation
    ["docs"]="https://raw.githubusercontent.com/slunsford/coffee-analytics/main/.claude/commands/docs.md"
    ["create-docs"]="https://raw.githubusercontent.com/jerseycheese/Narraitor/feature/issue-227-ai-suggestions/.claude/commands/create-docs.md"

    # Analysis and debugging
    ["five"]="https://raw.githubusercontent.com/TuckerTucker/tkr-agent-chat/main/.claude/commands/five.md"
    ["analyze-code"]="https://raw.githubusercontent.com/Hkgstax/VALUGATOR/main/.claude/commands/analyze-code.md"

    # Testing
    ["tdd"]="https://raw.githubusercontent.com/zscott/pane/main/.claude/commands/tdd.md"
    ["tdd-implement"]="https://raw.githubusercontent.com/jerseycheese/Narraitor/feature/issue-227-ai-suggestions/.claude/commands/tdd-implement.md"

    # Git and commits
    ["commit"]="https://raw.githubusercontent.com/evmts/tevm-monorepo/main/.claude/commands/commit.md"
    ["create-pr"]="https://raw.githubusercontent.com/toyamarinyon/giselle/main/.claude/commands/create-pr.md"
    ["fix-issue"]="https://raw.githubusercontent.com/metabase/metabase/master/.claude/commands/fix-issue.md"

    # Deployment
    ["deploy"]="https://raw.githubusercontent.com/cloudartisan/cloudartisan.github.io/main/.claude/commands/site/deploy.md"
    ["release"]="https://raw.githubusercontent.com/kelp/webdown/main/.claude/commands/release.md"

    # Project management
    ["todo"]="https://raw.githubusercontent.com/chrisleyva/todo-slash-command/main/todo.md"
    ["task-breakdown"]="https://raw.githubusercontent.com/Hkgstax/VALUGATOR/main/.claude/commands/task-breakdown.md"
)

# Track successes and failures
SUCCESS_COUNT=0
FAIL_COUNT=0
FAILED_COMMANDS=()

# Fetch each command
for cmd in "${!COMMANDS[@]}"; do
    url="${COMMANDS[$cmd]}"
    output_file="$COMMANDS_DIR/$cmd.md"

    echo -n "Fetching /$cmd... "

    if curl -sS -o "$output_file" "$url" 2>/dev/null; then
        # Check if we got a valid file (not 404 HTML)
        if grep -q "404" "$output_file" 2>/dev/null || [ ! -s "$output_file" ]; then
            echo -e "${RED}Failed (404)${NC}"
            rm -f "$output_file"
            FAILED_COMMANDS+=("$cmd")
            ((FAIL_COUNT++))
        else
            echo -e "${GREEN}Success${NC}"
            ((SUCCESS_COUNT++))
        fi
    else
        echo -e "${RED}Failed${NC}"
        FAILED_COMMANDS+=("$cmd")
        ((FAIL_COUNT++))
    fi
done

# Special handling for dump command (from gist)
echo -n "Fetching /dump... "
if curl -sS -o "$COMMANDS_DIR/dump.md" "https://gist.githubusercontent.com/fumito-ito/77c308e0382e06a9c16b22619f8a2f83/raw/dump.md" 2>/dev/null; then
    echo -e "${GREEN}Success${NC}"
    ((SUCCESS_COUNT++))
else
    echo -e "${RED}Failed${NC}"
    FAILED_COMMANDS+=("dump")
    ((FAIL_COUNT++))
fi

# Create mermaid command locally (it's often project-specific)
cat > "$COMMANDS_DIR/mermaid.md" << 'EOF'
# Generate Mermaid Diagram

Generate a Mermaid diagram based on the current context. Consider:

1. **For code structure**: Create a class diagram or flowchart
2. **For database**: Create an ERD (Entity Relationship Diagram)
3. **For processes**: Create a sequence or state diagram
4. **For architecture**: Create a C4 or component diagram

Output the diagram in a ```mermaid code block that can be rendered.

Include:
- Clear labels and relationships
- Proper Mermaid syntax
- Comments explaining complex parts
- A title and description

Focus on clarity and readability over completeness.
EOF
echo -e "Creating /mermaid... ${GREEN}Success${NC}"
((SUCCESS_COUNT++))

echo ""
echo -e "${GREEN}===============================================${NC}"
echo -e "${GREEN}Fetched $SUCCESS_COUNT commands successfully!${NC}"

if [ ${#FAILED_COMMANDS[@]} -gt 0 ]; then
    echo -e "${YELLOW}Failed to fetch ${#FAILED_COMMANDS[@]} commands:${NC}"
    for cmd in "${FAILED_COMMANDS[@]}"; do
        echo -e "  ${RED}- $cmd${NC}"
    done
fi

echo ""
echo "Commands are now available in $COMMANDS_DIR/"
echo ""
echo "Available commands:"
for file in "$COMMANDS_DIR"/*.md; do
    if [ -f "$file" ]; then
        basename "$file" .md | sed 's/^/  \//g'
    fi
done

echo ""
echo -e "${YELLOW}Note: Some commands may need adjustment for your project.${NC}"
echo -e "${YELLOW}Review each command before using it.${NC}"

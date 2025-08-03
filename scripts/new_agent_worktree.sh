#!/bin/bash
# OPSVI Git Worktree Helper
# Creates new worktrees for agent development
# Usage: ./scripts/new_agent_worktree.sh <agent_name> [base_branch]

set -euo pipefail

# Configuration
WORKSPACE_PATH="/home/opsvi/master_root"
WORKTREES_DIR="../_worktrees"
BASE_BRANCH="${2:-AUTOSAVE}"
AGENT_NAME="${1:-}"

# Validation
if [[ -z "$AGENT_NAME" ]]; then
    echo "ERROR: Agent name is required"
    echo "Usage: $0 <agent_name> [base_branch]"
    exit 1
fi

# Sanitize agent name (alphanumeric and hyphens only)
AGENT_NAME=$(echo "$AGENT_NAME" | sed 's/[^a-zA-Z0-9-]/-/g')

# Create worktree directory if it doesn't exist
mkdir -p "$WORKTREES_DIR"

# Worktree path
WORKTREE_PATH="$WORKTREES_DIR/$AGENT_NAME"

# Check if worktree already exists
if [[ -d "$WORKTREE_PATH" ]]; then
    echo "ERROR: Worktree already exists: $WORKTREE_PATH"
    echo "To remove: git worktree remove $WORKTREE_PATH"
    exit 1
fi

# Navigate to workspace
cd "$WORKSPACE_PATH"

# Verify we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo "ERROR: Not a git repository: $WORKSPACE_PATH"
    exit 1
fi

# Check if base branch exists
if ! git rev-parse --verify "$BASE_BRANCH" > /dev/null 2>&1; then
    echo "ERROR: Base branch does not exist: $BASE_BRANCH"
    echo "Available branches:"
    git branch -a
    exit 1
fi

# Create new branch for the worktree
NEW_BRANCH="agent/$AGENT_NAME"
if git rev-parse --verify "$NEW_BRANCH" > /dev/null 2>&1; then
    echo "WARNING: Branch $NEW_BRANCH already exists, using existing branch"
else
    echo "Creating new branch: $NEW_BRANCH from $BASE_BRANCH"
    git checkout "$BASE_BRANCH"
    git checkout -b "$NEW_BRANCH"
fi

# Create worktree
echo "Creating worktree: $WORKTREE_PATH"
git worktree add "$WORKTREE_PATH" "$NEW_BRANCH"

# Create .gitignore for worktree if it doesn't exist
if [[ ! -f "$WORKTREE_PATH/.gitignore" ]]; then
    cat > "$WORKTREE_PATH/.gitignore" << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# Virtual environments
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

# Logs
*.log
logs/

# Temporary files
*.tmp
*.temp
EOF
fi

# Create README for the worktree
cat > "$WORKTREE_PATH/README.md" << EOF
# Agent Worktree: $AGENT_NAME

This is a Git worktree for agent development.

## Quick Start

\`\`\`bash
cd $WORKTREE_PATH
# Your development work here
\`\`\`

## Git Workflow

1. Make changes in this worktree
2. Commit to the \`$NEW_BRANCH\` branch
3. Push to remote when ready
4. Create PR to merge into MAIN

## Cleanup

When done with this worktree:

\`\`\`bash
cd $WORKSPACE_PATH
git worktree remove $WORKTREE_PATH
git branch -d $NEW_BRANCH  # if no longer needed
\`\`\`

## Branch Info

- **Current Branch**: $NEW_BRANCH
- **Base Branch**: $BASE_BRANCH
- **Created**: $(date)
EOF

echo "✅ Worktree created successfully!"
echo "📁 Location: $WORKTREE_PATH"
echo "🌿 Branch: $NEW_BRANCH"
echo "📖 README: $WORKTREE_PATH/README.md"
echo ""
echo "To start working:"
echo "  cd $WORKTREE_PATH"
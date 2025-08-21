#!/bin/bash

# sync-claude-config.sh - Synchronize CLAUDE configuration across projects
# Usage: ./sync-claude-config.sh [target_path] [--dry-run] [--all]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SOURCE_DIR="${CLAUDE_SOURCE_DIR:-/home/opsvi/master_root}"
DEFAULT_PROJECTS=(
    "/home/opsvi/MetaGPT"
    "/home/opsvi/tool_research"
    "/home/opsvi/project-intelligence"
    "/home/opsvi/ARCANE_FOCUS"
)

# Files and directories to sync
SYNC_FILES=(
    "CLAUDE.md"
    ".mcp.json"
)
SYNC_DIRS=(
    ".claude"
    ".cursor"
)

# Parse arguments
DRY_RUN=false
SYNC_ALL=false
TARGET_PATH=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --all)
            SYNC_ALL=true
            shift
            ;;
        --help|-h)
            cat << EOF
Usage: $0 [target_path] [options]

Synchronize CLAUDE configuration files from master_root to other projects.

Arguments:
  target_path    Path to target project (optional if using --all)

Options:
  --all          Sync to all configured default projects
  --dry-run      Preview changes without applying them
  --help, -h     Show this help message

Environment:
  CLAUDE_SOURCE_DIR    Source directory (default: /home/opsvi/master_root)

Examples:
  $0 /home/opsvi/MyProject           # Sync to specific project
  $0 --all                            # Sync to all default projects
  $0 /path/to/project --dry-run      # Preview changes only

Files synchronized:
  - CLAUDE.md (main instructions)
  - .mcp.json (MCP server configuration)
  - .claude/ directory (agent profiles, commands, etc.)
  - .cursor/ directory (cursor rules and templates)
EOF
            exit 0
            ;;
        *)
            TARGET_PATH="$1"
            shift
            ;;
    esac
done

# Validation
if [ ! -d "$SOURCE_DIR" ]; then
    echo -e "${RED}Error: Source directory $SOURCE_DIR does not exist${NC}"
    exit 1
fi

# Function to sync files to a target
sync_to_target() {
    local target="$1"

    if [ ! -d "$target" ]; then
        echo -e "${YELLOW}Warning: Target directory $target does not exist${NC}"
        read -p "Create directory? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            if [ "$DRY_RUN" = true ]; then
                echo -e "${BLUE}[DRY-RUN] Would create: $target${NC}"
            else
                mkdir -p "$target"
                echo -e "${GREEN}Created: $target${NC}"
            fi
        else
            echo -e "${YELLOW}Skipping $target${NC}"
            return
        fi
    fi

    echo -e "${BLUE}Syncing to: $target${NC}"

    # Sync individual files
    for file in "${SYNC_FILES[@]}"; do
        source_file="$SOURCE_DIR/$file"
        target_file="$target/$file"

        if [ -f "$source_file" ]; then
            if [ "$DRY_RUN" = true ]; then
                if [ -f "$target_file" ]; then
                    if ! diff -q "$source_file" "$target_file" >/dev/null 2>&1; then
                        echo -e "  ${YELLOW}[DRY-RUN] Would update: $file${NC}"
                    else
                        echo -e "  ${GREEN}[DRY-RUN] Already current: $file${NC}"
                    fi
                else
                    echo -e "  ${BLUE}[DRY-RUN] Would copy: $file${NC}"
                fi
            else
                cp "$source_file" "$target_file"
                echo -e "  ${GREEN}✓ Synced: $file${NC}"
            fi
        else
            echo -e "  ${YELLOW}⚠ Source not found: $file${NC}"
        fi
    done

    # Sync directories
    for dir in "${SYNC_DIRS[@]}"; do
        source_dir="$SOURCE_DIR/$dir"
        target_dir="$target/$dir"

        if [ -d "$source_dir" ]; then
            if [ "$DRY_RUN" = true ]; then
                echo -e "  ${BLUE}[DRY-RUN] Would sync directory: $dir/${NC}"
                # Show what would be copied
                if [ ! -d "$target_dir" ]; then
                    echo -e "    ${YELLOW}Would create directory and copy all contents${NC}"
                else
                    # Check for differences
                    diff_count=$(diff -qr "$source_dir" "$target_dir" 2>/dev/null | wc -l)
                    if [ "$diff_count" -gt 0 ]; then
                        echo -e "    ${YELLOW}Would update $diff_count files${NC}"
                    else
                        echo -e "    ${GREEN}Already synchronized${NC}"
                    fi
                fi
            else
                # Ensure target directory exists
                mkdir -p "$target_dir"
                # Use rsync for efficient copying (fallback to cp -r if rsync not available)
                if command -v rsync &> /dev/null; then
                    rsync -a --delete "$source_dir/" "$target_dir/"
                else
                    cp -r "$source_dir"/* "$target_dir/" 2>/dev/null || true
                fi
                echo -e "  ${GREEN}✓ Synced: $dir/${NC}"
            fi
        else
            echo -e "  ${YELLOW}⚠ Source directory not found: $dir${NC}"
        fi
    done

    # Check if project is a git repository and offer to commit
    if [ -d "$target/.git" ] && [ "$DRY_RUN" = false ]; then
        cd "$target"
        if git diff --quiet 2>/dev/null; then
            echo -e "  ${GREEN}No changes to commit${NC}"
        else
            echo -e "  ${YELLOW}Changes detected in git repository${NC}"
            read -p "  Commit changes? (y/n) " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                git add -A
                git commit -m "sync: update CLAUDE configuration from master_root

- Updated CLAUDE.md with latest instructions
- Synced .claude/ agent profiles and commands
- Updated .mcp.json configuration
- Synced .cursor/ rules and templates"
                echo -e "  ${GREEN}✓ Changes committed${NC}"
            fi
        fi
        cd - >/dev/null
    fi

    echo
}

# Main execution
echo -e "${BLUE}═══════════════════════════════════════════════════${NC}"
echo -e "${BLUE}    CLAUDE Configuration Synchronization Tool${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════${NC}"
echo -e "Source: ${GREEN}$SOURCE_DIR${NC}"
echo

if [ "$DRY_RUN" = true ]; then
    echo -e "${YELLOW}Running in DRY-RUN mode - no changes will be made${NC}"
    echo
fi

# Determine targets
if [ "$SYNC_ALL" = true ]; then
    echo -e "${BLUE}Syncing to all default projects...${NC}"
    echo
    for project in "${DEFAULT_PROJECTS[@]}"; do
        sync_to_target "$project"
    done
elif [ -n "$TARGET_PATH" ]; then
    sync_to_target "$TARGET_PATH"
else
    echo -e "${RED}Error: No target specified${NC}"
    echo "Use --all to sync to default projects or specify a target path"
    echo "Run with --help for usage information"
    exit 1
fi

# Summary
if [ "$DRY_RUN" = false ]; then
    echo -e "${GREEN}═══════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}    Synchronization Complete!${NC}"
    echo -e "${GREEN}═══════════════════════════════════════════════════${NC}"

    # Provide quick verification command
    echo
    echo "To verify synchronization, run:"
    echo -e "${BLUE}  grep -c 'EFFICIENCY & BATCHING' */CLAUDE.md 2>/dev/null${NC}"
else
    echo -e "${YELLOW}═══════════════════════════════════════════════════${NC}"
    echo -e "${YELLOW}    Dry-run complete - no changes made${NC}"
    echo -e "${YELLOW}═══════════════════════════════════════════════════${NC}"
    echo
    echo "Remove --dry-run flag to apply changes"
fi

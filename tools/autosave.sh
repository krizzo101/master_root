#!/bin/bash
# OPSVI Autosave Script
# Commits changes to AUTOSAVE branch every 10 minutes
# Usage: ./tools/autosave.sh [workspace_path]

set -euo pipefail

# Configuration
WORKSPACE_PATH="${1:-/home/opsvi/master_root}"
LOG_DIR="$HOME/.opsvi_logs"
LOG_FILE="$LOG_DIR/autosave.log"
BRANCH="AUTOSAVE"
MAX_COMMITS=100  # Keep last 100 commits on AUTOSAVE

# Ensure log directory exists
mkdir -p "$LOG_DIR"

# Logging function
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

# Error handling
cleanup() {
    log "Autosave script terminated"
    exit 1
}

trap cleanup ERR

# Main autosave logic
main() {
    log "Starting autosave for workspace: $WORKSPACE_PATH"

    if [[ ! -d "$WORKSPACE_PATH" ]]; then
        log "ERROR: Workspace path does not exist: $WORKSPACE_PATH"
        exit 1
    fi

    cd "$WORKSPACE_PATH"

    # Check if we're in a git repository
    if ! git rev-parse --git-dir > /dev/null 2>&1; then
        log "ERROR: Not a git repository: $WORKSPACE_PATH"
        exit 1
    fi

    # Check for changes
    if git diff-index --quiet HEAD --; then
        log "No changes detected, skipping commit"
        return 0
    fi

    # Get current branch
    current_branch=$(git branch --show-current)

    # Switch to AUTOSAVE branch if not already there
    if [[ "$current_branch" != "$BRANCH" ]]; then
        log "Switching from $current_branch to $BRANCH"
        git checkout "$BRANCH" || {
            log "ERROR: Failed to checkout $BRANCH branch"
            exit 1
        }
    fi

    # Add all changes
    git add -A

    # Check if there are staged changes
    if git diff --cached --quiet; then
        log "No staged changes, skipping commit"
        return 0
    fi

    # Create commit with timestamp
    timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    commit_msg="autosave: $timestamp"

    if git commit -m "$commit_msg"; then
        log "Successfully committed changes: $commit_msg"

        # Clean up old commits (keep last MAX_COMMITS)
        commit_count=$(git rev-list --count HEAD)
        if [[ $commit_count -gt $MAX_COMMITS ]]; then
            commits_to_remove=$((commit_count - MAX_COMMITS))
            log "Removing $commits_to_remove old commits to maintain history limit"
            git reset --soft HEAD~$commits_to_remove
        fi
    else
        log "ERROR: Failed to commit changes"
        exit 1
    fi

    log "Autosave completed successfully"
}

# Run main function
main "$@"
#!/bin/bash
# OPSVI Snapshot Script
# Creates tagged snapshots every 12 hours
# Usage: ./tools/snapshot.sh [workspace_path]

set -euo pipefail

# Configuration
WORKSPACE_PATH="${1:-/home/opsvi/master_root}"
LOG_DIR="$HOME/.opsvi_logs"
LOG_FILE="$LOG_DIR/snapshot.log"
BRANCH="MAIN"
SNAPSHOT_PREFIX="snapshot"

# Ensure log directory exists
mkdir -p "$LOG_DIR"

# Logging function
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

# Error handling
cleanup() {
    log "Snapshot script terminated"
    exit 1
}

trap cleanup ERR

# Main snapshot logic
main() {
    log "Starting snapshot for workspace: $WORKSPACE_PATH"

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

    # Get current branch
    current_branch=$(git branch --show-current)

    # Switch to MAIN branch if not already there
    if [[ "$current_branch" != "$BRANCH" ]]; then
        log "Switching from $current_branch to $BRANCH"
        git checkout "$BRANCH" || {
            log "ERROR: Failed to checkout $BRANCH branch"
            exit 1
        }
    fi

    # Pull latest changes
    log "Pulling latest changes from remote"
    git pull origin "$BRANCH" || {
        log "WARNING: Failed to pull from remote, continuing with local state"
    }

    # Create snapshot tag
    timestamp=$(date '+%Y%m%d_%H%M%S')
    snapshot_tag="${SNAPSHOT_PREFIX}_${timestamp}"

    # Check if tag already exists
    if git rev-parse "$snapshot_tag" >/dev/null 2>&1; then
        log "WARNING: Tag $snapshot_tag already exists, skipping"
        return 0
    fi

    # Create and push tag
    if git tag "$snapshot_tag"; then
        log "Successfully created snapshot tag: $snapshot_tag"

        # Push tag to remote
        if git push origin "$snapshot_tag"; then
            log "Successfully pushed snapshot tag to remote"
        else
            log "WARNING: Failed to push snapshot tag to remote"
        fi

        # Clean up old snapshots (keep last 30)
        log "Cleaning up old snapshots"
        snapshot_tags=$(git tag --list "${SNAPSHOT_PREFIX}_*" --sort=-version:refname)
        count=0
        for tag in $snapshot_tags; do
            count=$((count + 1))
            if [[ $count -gt 30 ]]; then
                log "Removing old snapshot tag: $tag"
                git tag -d "$tag"
                git push origin ":refs/tags/$tag" || true
            fi
        done
    else
        log "ERROR: Failed to create snapshot tag"
        exit 1
    fi

    log "Snapshot completed successfully"
}

# Run main function
main "$@"
#!/bin/bash
# Hook that runs BEFORE any /compact command
# This will auto-export the session before compaction

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
PROJECT_NAME=$(basename "$(pwd)")
EXPORT_DIR="$HOME/.claude/session-exports/pre-compact"

# Create export directory
mkdir -p "$EXPORT_DIR"

# Export path
EXPORT_PATH="$EXPORT_DIR/${PROJECT_NAME}_${TIMESTAMP}.jsonl"

# Get the current session ID if available
SESSION_ID="${CLAUDE_SESSION_ID:-unknown}"

# Log the export
echo "🔄 Pre-compact hook: Auto-exporting session to $EXPORT_PATH" >&2

# Use Claude's internal export mechanism if available
# Otherwise, manually copy the current session
if [ -d "$HOME/.claude/projects" ]; then
    # Find the most recent session file
    LATEST_SESSION=$(find "$HOME/.claude/projects" -name "*.jsonl" -type f -printf '%T@ %p\n' 2>/dev/null | sort -rn | head -1 | cut -d' ' -f2-)

    if [ -n "$LATEST_SESSION" ]; then
        cp "$LATEST_SESSION" "$EXPORT_PATH"
        echo "✅ Session exported: $(du -h "$EXPORT_PATH" | cut -f1)" >&2
    else
        echo "⚠️  No session file found to export" >&2
    fi
else
    echo "⚠️  Claude projects directory not found" >&2
fi

# Allow the compact to proceed
exit 0

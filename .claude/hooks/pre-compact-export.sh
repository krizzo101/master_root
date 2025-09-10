#!/bin/bash
# Pre-compact hook to automatically export full session before compaction
# This hook runs before /compact command executes

# Configuration
EXPORT_DIR="${HOME}/master_root/.claude/session-exports"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
PROJECT_NAME=$(basename "$(pwd)")

# Create export directory if it doesn't exist
mkdir -p "$EXPORT_DIR"

# Read the input JSON from stdin (Claude Code passes hook data as JSON)
INPUT=$(cat)

# Extract session info if needed (optional)
# SESSION_ID=$(echo "$INPUT" | jq -r '.sessionId // "unknown"')

# Export filename with timestamp
EXPORT_FILE="$EXPORT_DIR/${PROJECT_NAME}_session_${TIMESTAMP}.txt"

# Use Claude Code's /export command to save full session
# Note: We need to trigger export from within the session
# The hook can't directly run /export, but we can save the current context

# Save the input context (includes current conversation)
echo "=== PRE-COMPACT SESSION EXPORT ===" > "$EXPORT_FILE"
echo "Timestamp: $(date)" >> "$EXPORT_FILE"
echo "Project: $PROJECT_NAME" >> "$EXPORT_FILE"
echo "Working Directory: $(pwd)" >> "$EXPORT_FILE"
echo "===================================" >> "$EXPORT_FILE"
echo "" >> "$EXPORT_FILE"

# If we have access to the session data, save it
if [ -n "$INPUT" ]; then
    echo "$INPUT" | jq -r '.conversation // empty' >> "$EXPORT_FILE" 2>/dev/null || echo "$INPUT" >> "$EXPORT_FILE"
fi

# Log the export
echo "[$(date)] Session exported to: $EXPORT_FILE" >> "$EXPORT_DIR/export.log"

# Return success to allow compact to proceed
echo "{\"decision\": \"allow\", \"message\": \"Session exported to $EXPORT_FILE\"}"
exit 0

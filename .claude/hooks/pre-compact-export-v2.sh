#!/bin/bash
# Enhanced Pre-compact hook that triggers /export before compaction
# This version works with the transcript path if available

# Configuration
EXPORT_DIR="${HOME}/master_root/.claude/session-exports"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
PROJECT_NAME=$(basename "$(pwd)")

# Create export directory if it doesn't exist
mkdir -p "$EXPORT_DIR"

# Export filename with timestamp
EXPORT_FILE="$EXPORT_DIR/${PROJECT_NAME}_pre_compact_${TIMESTAMP}.txt"

# Read the input JSON from stdin
INPUT=$(cat)

# Try to get transcript path from environment or input
TRANSCRIPT_PATH="${TRANSCRIPT_PATH:-}"
if [ -z "$TRANSCRIPT_PATH" ] && command -v jq >/dev/null 2>&1; then
    TRANSCRIPT_PATH=$(echo "$INPUT" | jq -r '.transcriptPath // empty' 2>/dev/null)
fi

# Create header
{
    echo "=== PRE-COMPACT SESSION EXPORT ==="
    echo "Timestamp: $(date)"
    echo "Project: $PROJECT_NAME"
    echo "Working Directory: $(pwd)"
    echo "===================================="
    echo ""
} > "$EXPORT_FILE"

# If we have a transcript path, copy it
if [ -n "$TRANSCRIPT_PATH" ] && [ -f "$TRANSCRIPT_PATH" ]; then
    echo "=== TRANSCRIPT ===" >> "$EXPORT_FILE"
    cat "$TRANSCRIPT_PATH" >> "$EXPORT_FILE"
    echo "[$(date)] Session transcript exported from: $TRANSCRIPT_PATH" >> "$EXPORT_DIR/export.log"
else
    # Otherwise save the input context
    echo "=== CONTEXT DATA ===" >> "$EXPORT_FILE"
    echo "$INPUT" >> "$EXPORT_FILE"
    echo "[$(date)] Session context exported (no transcript available)" >> "$EXPORT_DIR/export.log"
fi

# Log the export
echo "[$(date)] Pre-compact export saved to: $EXPORT_FILE" >> "$EXPORT_DIR/export.log"

# Create a symlink to the latest export
ln -sf "$EXPORT_FILE" "$EXPORT_DIR/latest_pre_compact.txt"

# Return success with message
echo "{\"decision\": \"allow\", \"message\": \"Session exported to $EXPORT_FILE before compaction\"}"
exit 0

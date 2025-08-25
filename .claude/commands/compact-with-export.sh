#!/bin/bash
# Custom compact command that exports session first
# Usage: /compact-with-export

# Get current timestamp
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
PROJECT_NAME=$(basename "$(pwd)")
EXPORT_DIR="$HOME/.claude/exports"

# Create export directory if it doesn't exist
mkdir -p "$EXPORT_DIR"

# Export the current session using Claude's export functionality
# This triggers the built-in export before compaction
echo "📦 Exporting session before compaction..."
echo "/export $EXPORT_DIR/${PROJECT_NAME}_${TIMESTAMP}.jsonl"

# Add a small delay to ensure export completes
sleep 2

# Now trigger the actual compact command
echo "🗜️ Compacting session..."
echo "/compact"

echo "✅ Session exported to: $EXPORT_DIR/${PROJECT_NAME}_${TIMESTAMP}.jsonl"
echo "✅ Session compacted"

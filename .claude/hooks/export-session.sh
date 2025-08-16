#!/bin/bash
# Session Export Hook for Claude Code
# Automatically exports sessions on completion

TRANSCRIPT_PATH="$1"
EVENT_TYPE="$2"  # SessionStart, SessionStop, etc.

# Configuration
EXPORT_DIR="/home/opsvi/master_root/.sdlc-sessions"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Create export directory if it doesn't exist
mkdir -p "$EXPORT_DIR"

# Log the event
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Hook triggered: $EVENT_TYPE" >> "$EXPORT_DIR/hook.log"

# Export based on event type
case "$EVENT_TYPE" in
    "SessionStop"|"SessionComplete")
        if [ -f "$TRANSCRIPT_PATH" ]; then
            # Copy the transcript
            EXPORT_FILE="$EXPORT_DIR/session_${TIMESTAMP}.json"
            cp "$TRANSCRIPT_PATH" "$EXPORT_FILE"

            # Add metadata
            METADATA_FILE="$EXPORT_DIR/session_${TIMESTAMP}_metadata.json"
            cat > "$METADATA_FILE" << EOF
{
    "event": "$EVENT_TYPE",
    "timestamp": "$(date -Iseconds)",
    "transcript_path": "$TRANSCRIPT_PATH",
    "export_file": "$EXPORT_FILE",
    "environment": {
        "user": "$USER",
        "pwd": "$PWD",
        "claude_version": "$(claude --version 2>/dev/null || echo 'unknown')"
    }
}
EOF

            echo "[$(date '+%Y-%m-%d %H:%M:%S')] Session exported to: $EXPORT_FILE" >> "$EXPORT_DIR/hook.log"
        else
            echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: Transcript not found at $TRANSCRIPT_PATH" >> "$EXPORT_DIR/hook.log"
        fi
        ;;

    "SessionStart")
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] Session started, transcript at: $TRANSCRIPT_PATH" >> "$EXPORT_DIR/hook.log"
        ;;

    *)
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] Unknown event: $EVENT_TYPE" >> "$EXPORT_DIR/hook.log"
        ;;
esac

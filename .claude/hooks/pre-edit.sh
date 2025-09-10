#!/bin/bash
# Pre-edit hook - Runs before any file edit

FILE_PATH="$1"
OLD_CONTENT="$2"
NEW_CONTENT="$3"

# Create backup
if [ -f "$FILE_PATH" ]; then
    BACKUP_DIR="/home/opsvi/master_root/.claude/backups/$(date +%Y%m%d)"
    mkdir -p "$BACKUP_DIR"
    cp "$FILE_PATH" "$BACKUP_DIR/$(basename $FILE_PATH).$(date +%H%M%S).bak"
    echo "✅ Backup created: $BACKUP_DIR/$(basename $FILE_PATH).$(date +%H%M%S).bak"
fi

# Check for potential issues
if echo "$NEW_CONTENT" | grep -q "PRIVATE KEY\|SECRET\|PASSWORD\|TOKEN"; then
    echo "⚠️  WARNING: Potential secret detected in edit!"
    echo "Please review carefully before committing."
fi

# Validate Python syntax if .py file
if [[ "$FILE_PATH" == *.py ]]; then
    echo "$NEW_CONTENT" | python -m py_compile - 2>/dev/null
    if [ $? -ne 0 ]; then
        echo "❌ Python syntax error detected!"
        exit 1
    fi
fi

exit 0

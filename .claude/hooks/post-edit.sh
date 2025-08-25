#!/bin/bash
# Post-edit hook - Runs after any file edit

FILE_PATH="$1"

# Auto-format Python files
if [[ "$FILE_PATH" == *.py ]]; then
    echo "🎨 Auto-formatting Python file..."
    black "$FILE_PATH" 2>/dev/null || true
    ruff check --fix "$FILE_PATH" 2>/dev/null || true
fi

# Auto-format TypeScript/JavaScript
if [[ "$FILE_PATH" == *.ts ]] || [[ "$FILE_PATH" == *.js ]]; then
    echo "🎨 Auto-formatting TypeScript/JavaScript..."
    npx prettier --write "$FILE_PATH" 2>/dev/null || true
fi

# Update documentation if needed
if [[ "$FILE_PATH" == *.py ]]; then
    echo "📚 Checking documentation..."
    # Could generate docs here
fi

# Log the change
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Modified: $FILE_PATH" >> /home/opsvi/master_root/.claude/activity.log

exit 0

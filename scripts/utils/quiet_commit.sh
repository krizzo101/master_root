#!/bin/bash
# Truly quiet git commit - redirects ALL output

# Check if commit message was provided
if [ $# -eq 0 ]; then
    echo "Usage: ./quiet_commit.sh \"commit message\""
    exit 1
fi

# Stage all changes
git add -A 2>/dev/null

# Run commit with pre-commit hooks, capturing all output
OUTPUT_FILE="/tmp/commit_output_$$.log"
ERROR_FILE="/tmp/commit_error_$$.log"

# Set environment to suppress as much as possible
export PRE_COMMIT_QUIET=1
export PYTHONWARNINGS="ignore"
export TERM=dumb

# Run commit, redirecting all output
if git commit -m "$1" > "$OUTPUT_FILE" 2> "$ERROR_FILE"; then
    echo "✅ Committed successfully"
    exit 0
else
    # Check if it failed due to pre-commit hooks
    if grep -q "hook" "$ERROR_FILE" 2>/dev/null || grep -q "hook" "$OUTPUT_FILE" 2>/dev/null; then
        # Pre-commit made changes, retry
        git add -A 2>/dev/null
        if git commit -m "$1" > "$OUTPUT_FILE" 2> "$ERROR_FILE"; then
            echo "✅ Committed after pre-commit fixes"
            exit 0
        else
            echo "❌ Commit failed after retry. Check /tmp/commit_error_$$.log"
            exit 1
        fi
    else
        echo "❌ Commit failed. Check /tmp/commit_error_$$.log"
        exit 1
    fi
fi

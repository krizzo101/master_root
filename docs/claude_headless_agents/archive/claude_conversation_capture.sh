#!/bin/bash

# Claude Conversation Capture Script
# Captures full conversation including tool calls from debug output

capture_conversation() {
    local prompt="$1"
    local temp_file=$(mktemp)

    # Run Claude with debug and capture all output
    claude -p -d "$prompt" 2>&1 | tee "$temp_file"

    echo ""
    echo "=== CONVERSATION SUMMARY ==="
    echo ""

    # Extract tool calls
    echo "Tool Calls Made:"
    grep -E "DEBUG.*Tool:" "$temp_file" | sed 's/.*Tool: /  - /'

    # Extract results
    echo ""
    echo "Final Result:"
    tail -n 5 "$temp_file" | grep -v DEBUG | grep -v ERROR

    rm "$temp_file"
}

# Usage
if [ $# -eq 0 ]; then
    echo "Usage: $0 \"Your prompt\""
    exit 1
fi

capture_conversation "$1"

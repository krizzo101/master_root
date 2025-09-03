#!/bin/bash

# Claude Token Automation Script
# This script automates the claude setup-token process

echo "Claude Token Setup Automation"
echo "=============================="

# Method 1: Using expect (if available)
if command -v expect &> /dev/null; then
    echo "Using expect for automation..."

    expect -c '
    spawn claude setup-token
    set timeout 120

    # Wait for browser to open and user to authorize
    expect {
        "*CLAUDE_CODE_TOKEN*" {
            set token $expect_out(buffer)
            # Extract just the token value
            regexp {CLAUDE_CODE_TOKEN[=:[:space:]]+([a-zA-Z0-9_-]+)} $token match extracted_token
            puts "\nToken captured: $extracted_token"

            # Save to file
            set fp [open "$env(HOME)/.claude_token" w]
            puts $fp "export CLAUDE_CODE_TOKEN=$extracted_token"
            close $fp
        }
        timeout {
            puts "Timeout waiting for token"
            exit 1
        }
    }
    '

    if [ $? -eq 0 ]; then
        echo "Token saved to ~/.claude_token"
        echo "Run: source ~/.claude_token"
        exit 0
    fi
fi

# Method 2: Using background process with output capture
echo "Starting claude setup-token in background..."

# Create a temporary file for output
TMPFILE=$(mktemp)

# Run claude setup-token and capture output
claude setup-token 2>&1 | tee "$TMPFILE" &
CLAUDE_PID=$!

echo "Process started (PID: $CLAUDE_PID)"
echo "Please complete the authorization in your browser..."

# Monitor the output file for token
TIMEOUT=120
ELAPSED=0

while [ $ELAPSED -lt $TIMEOUT ]; do
    if grep -q "CLAUDE_CODE_TOKEN" "$TMPFILE"; then
        TOKEN=$(grep -oP 'CLAUDE_CODE_TOKEN[=:\s]+\K[a-zA-Z0-9_-]+' "$TMPFILE" | head -1)

        if [ -n "$TOKEN" ]; then
            echo -e "\n✓ Token captured successfully!"

            # Save token
            echo "export CLAUDE_CODE_TOKEN=$TOKEN" > ~/.claude_token
            echo "CLAUDE_CODE_TOKEN=$TOKEN" >> .env

            echo "Token saved to:"
            echo "  - ~/.claude_token (source this file)"
            echo "  - .env (for local projects)"

            echo -e "\nTo use: source ~/.claude_token"

            # Clean up
            rm -f "$TMPFILE"
            kill $CLAUDE_PID 2>/dev/null

            exit 0
        fi
    fi

    sleep 2
    ELAPSED=$((ELAPSED + 2))
    echo -n "."
done

echo -e "\n✗ Timeout: Could not capture token"
echo "Please run 'claude setup-token' manually"

# Clean up
rm -f "$TMPFILE"
kill $CLAUDE_PID 2>/dev/null

exit 1

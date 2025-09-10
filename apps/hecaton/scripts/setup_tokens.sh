#!/bin/bash
# Setup tokens for Phase 0 testing
# Uses existing CLAUDE_CODE_TOKEN for both slots

if [ -z "$CLAUDE_CODE_TOKEN" ]; then
    echo "ERROR: CLAUDE_CODE_TOKEN not found in environment"
    echo "Please set CLAUDE_CODE_TOKEN before running Hecaton"
    exit 1
fi

# For Phase 0, we'll use the same token twice
export CLAUDE_CODE_TOKEN_0="$CLAUDE_CODE_TOKEN"
export CLAUDE_CODE_TOKEN_1="$CLAUDE_CODE_TOKEN"

echo "✓ Tokens configured for Phase 0 (2 agents)"
echo "  CLAUDE_CODE_TOKEN_0: ***REDACTED***"
echo "  CLAUDE_CODE_TOKEN_1: ***REDACTED***"

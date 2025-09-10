#!/bin/bash

# CRITICAL: Clear ANTHROPIC_API_KEY and ensure CLAUDE_CODE_TOKEN is set
unset ANTHROPIC_API_KEY
export CLAUDE_CODE_TOKEN="${CLAUDE_CODE_TOKEN}"

echo "=== Environment Setup ==="
echo "CLAUDE_CODE_TOKEN: ${CLAUDE_CODE_TOKEN:0:20}..."
echo "ANTHROPIC_API_KEY: ${ANTHROPIC_API_KEY:-NOT_SET (good!)}"

# Verify token is accessible to Python
python3 -c "import os; print(f'Python sees CLAUDE_CODE_TOKEN: {os.getenv(\"CLAUDE_CODE_TOKEN\", \"NOT_SET\")[:20]}...')"
python3 -c "import os; print(f'Python sees ANTHROPIC_API_KEY: {os.getenv(\"ANTHROPIC_API_KEY\", \"NOT_SET\")}')"

# Navigate to HECATON
cd /home/opsvi/master_root/apps/hecaton

echo -e "\n=== Testing HECATON with correct environment ==="
python -m hecaton run "Add a comment to the main function" --agents 1 --merge-back --dry-run --verbose 2>&1 | head -30

echo -e "\n=== Check for any patches created ==="
find . -name "*.patch" -type f 2>/dev/null | head -5

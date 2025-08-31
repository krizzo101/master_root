#!/bin/bash
# Environment setup for testing prompt_opt.py hook

echo "=== Environment Details ==="
echo "Working Directory: $(pwd)"
echo "Python Version: $(python3 --version)"
echo "Hook Location: .claude/hooks/prompt_opt.py"
echo "Hook Config: .claude/settings.json"
echo

# Check hook file exists
if [ -f ".claude/hooks/prompt_opt.py" ]; then
    echo "✓ Hook file exists"
    echo "  Permissions: $(ls -l .claude/hooks/prompt_opt.py | awk '{print $1}')"
    echo "  Size: $(wc -l < .claude/hooks/prompt_opt.py) lines"
else
    echo "✗ Hook file not found!"
    exit 1
fi

# Check configuration
if [ -f ".claude/settings.json" ]; then
    echo "✓ Settings file exists"
    echo "  Hook configured for: $(grep -A2 'UserPromptSubmit' .claude/settings.json | head -3)"
else
    echo "⚠ Settings file not found (hook may not be registered)"
fi

# Check dependencies
echo
echo "=== Checking Dependencies ==="
python3 -c "import json, os, re, select, sys, textwrap; print('✓ Standard libraries available')"
python3 -c "from openai import OpenAI; print('✓ OpenAI library available')" 2>/dev/null || echo "⚠ OpenAI library not available (may affect functionality)"

# Check environment variables
echo
echo "=== Environment Variables ==="
echo "OPENAI_API_KEY: $([ -n "$OPENAI_API_KEY" ] && echo '✓ Set' || echo '✗ Not set')"
echo "DEBUG: $([ -n "$DEBUG" ] && echo "Set to '$DEBUG'" || echo 'Not set (debug output disabled)')"
echo "PROMPT_OPT_MODEL: $([ -n "$PROMPT_OPT_MODEL" ] && echo "$PROMPT_OPT_MODEL" || echo 'Not set (using default: gpt-5-mini)')"
echo "PROMPT_OPT_MAX_TOK: $([ -n "$PROMPT_OPT_MAX_TOK" ] && echo "$PROMPT_OPT_MAX_TOK" || echo 'Not set (using default: 4000)')"

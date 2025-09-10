#!/usr/bin/env python3
"""Minimal prompt optimizer hook that actually works"""
import json
import sys

try:
    # Read JSON from stdin
    inp = json.load(sys.stdin)
    prompt = inp.get("prompt", "")

    # For now, just pass through with suppressed output
    # This proves the hook is working
    print(json.dumps({"suppressOutput": True}))
    sys.exit(0)

except Exception as e:
    # Return error but don't block
    print(f"Prompt optimizer error: {e}", file=sys.stderr)
    sys.exit(1)  # Non-blocking error

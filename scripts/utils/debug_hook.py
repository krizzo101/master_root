#!/usr/bin/env python3
import json
import os
import sys
import traceback

try:
    inp = json.load(sys.stdin)

    # Import after reading input to ensure we don't block
    from openai import OpenAI

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    # Try simplified call
    resp = client.responses.create(
        model="gpt-5-mini",
        input="Optimize: " + inp.get("prompt", "test"),
        max_output_tokens=100,
    )

    result = {
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": f"[PROMPT_OPTIMIZER]\n{inp.get('prompt', 'test')}\n[END_PROMPT_OPTIMIZER]",
        }
    }

    print(json.dumps(result))

except Exception as e:
    # Print actual error for debugging
    print(f"ACTUAL ERROR: {e}", file=sys.stderr)
    traceback.print_exc(file=sys.stderr)
    print(json.dumps({"suppressOutput": True}))

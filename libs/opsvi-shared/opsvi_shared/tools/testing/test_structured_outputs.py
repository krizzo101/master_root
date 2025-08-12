"""
Test Structured Outputs Implementation
Debug the new OpenAI structured outputs approach
"""

import os
import sys

sys.path.append("development/agent_hub")
os.environ["OPENAI_API_KEY"] = (
    os.popen(
        'grep -o \'"OPENAI_API_KEY": "[^"]*"\' .cursor/mcp.json | cut -d\'"\'  -f4'
    )
    .read()
    .strip()
)
try:
    from app import _call, load_schema
    from openai_helper import chat_structured

    simple_schema = {
        "name": "test_response",
        "description": "A simple test response",
        "parameters": {
            "type": "object",
            "properties": {
                "message": {"type": "string", "description": "A simple message"},
                "status": {"type": "string", "description": "Status of the operation"},
            },
            "required": ["message", "status"],
            "additionalProperties": False,
        },
    }
    response = chat_structured(
        model="gpt-4o-mini",
        system="You are a helpful assistant. Always respond with the requested JSON structure.",
        user="Say hello with status 'success'",
        schema=simple_schema,
    )
    try:
        patch_schema = load_schema("patch_schema")
        response2 = chat_structured(
            model="gpt-4o-mini",
            system="You are a development assistant. Generate code changes as requested.",
            user="Create a simple health check endpoint for a FastAPI app",
            schema=patch_schema,
        )
    except Exception:
        pass
    else:
        pass
    finally:
        pass
    result = _call(
        model="gpt-4o-mini",
        sys="You are a helpful assistant.",
        user="Respond with a simple JSON object containing a greeting",
        schema=simple_schema,
    )
except Exception:
    import traceback

    traceback.print_exc()
else:
    pass
finally:
    pass

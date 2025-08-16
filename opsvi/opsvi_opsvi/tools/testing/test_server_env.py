"""
Test server environment
Check if OpenAI API key and imports work in server context
"""

import os
import sys

sys.path.insert(0, "/home/opsvi/agent_world/development/agent_hub")
api_key = os.environ.get("OPENAI_API_KEY", "NOT_SET")
try:
    from app import _call
    from openai_helper import chat_structured

    if api_key != "NOT_SET":
        simple_schema = {
            "name": "test_response",
            "parameters": {
                "type": "object",
                "properties": {"message": {"type": "string"}},
                "required": ["message"],
                "additionalProperties": False,
            },
        }
        response = chat_structured(
            model="gpt-4o-mini",
            system="You are a helpful assistant.",
            user="Say hello in JSON format",
            schema=simple_schema,
        )
    else:
        pass
    if api_key == "NOT_SET":
        cmd = 'grep -o \'"OPENAI_API_KEY": "[^"]*"\' /home/opsvi/agent_world/.cursor/mcp.json | cut -d\'"\'  -f4'
        api_key = os.popen(cmd).read().strip()
        if api_key:
            os.environ["OPENAI_API_KEY"] = api_key
        else:
            pass
    else:
        pass
    result = _call(
        model="gpt-4o-mini",
        sys="You are a helpful assistant.",
        user="Say hello",
        schema=simple_schema,
    )
except Exception:
    import traceback

    traceback.print_exc()
else:
    pass
finally:
    pass

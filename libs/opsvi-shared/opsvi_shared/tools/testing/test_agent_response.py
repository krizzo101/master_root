"""
Agent Response Debug Test
Test the _call function directly to debug parsing issues
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
    from app import _call
    from profiles.dev_agent import DevAgent

    dev_agent = DevAgent("test_hash")
    schema = dev_agent.get_schema()
    result = _call(
        model="gpt-4o-mini",
        sys=dev_agent.get_prompt(),
        user="Add a simple health check endpoint that returns server status",
        schema=schema,
    )
    full_result = dev_agent.generate_feature(
        spec="Add a simple health check endpoint that returns server status",
        repo_state_hash="test123",
    )
except Exception:
    import traceback

    traceback.print_exc()
else:
    pass
finally:
    pass

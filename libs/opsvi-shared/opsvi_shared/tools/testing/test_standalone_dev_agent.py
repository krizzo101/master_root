"""
Standalone Dev Agent Test
Exact replication of dev_generate_feature to isolate the issue
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


async def dev_generate_feature_replica(spec: str, repo_state_hash: str):
    """Exact replica of the dev_generate_feature function"""
    from app import _call, load_profile, load_schema

    sys_prompt = load_profile("dev_agent")
    rule_text = ""
    user = f"Implement the following feature in our codebase.\nSPEC: {spec}\nREPO_HASH: {repo_state_hash}\nRelevant rules:\n{rule_text[:4000]}"
    schema = load_schema("patch_schema")
    bundle = _call("gpt-4o-mini", sys_prompt, user, schema)
    return bundle


import asyncio


async def main():
    try:
        result = await dev_generate_feature_replica(
            spec="Add a simple health check endpoint that returns server status",
            repo_state_hash="standalone_test_001",
        )
        if isinstance(result, dict):
            if "error" in result:
                if "debug_info" in result:
                    pass
                else:
                    pass
            else:
                pass
                pass
                pass
                pass
                pass
                if "patch_diff" in result:
                    pass
                else:
                    pass
        else:
            pass
    except Exception:
        import traceback

        traceback.print_exc()
    else:
        pass
    finally:
        pass


if __name__ == "__main__":
    asyncio.run(main())
else:
    pass

import asyncio
import os
import re
import subprocess
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.types import TextContent

MCP_SERVER_CMD = ["python3", "src/applications/workflow_mcp/mcp_workflow_server.py"]


def extract_workflow_name(success_str: str) -> str:
    # Extract workflow_name from 'SUCCESS: Workflow registered: workflow_83921 (version ...)' pattern
    match = re.search(r"registered: (\w+)_?(\d+)?", success_str)
    if match:
        return match.group(1) + ("_" + match.group(2) if match.group(2) else "")
    return ""


async def call_tool(session, tool_name: str, arguments: dict[str, Any]) -> Any:
    result = await session.call_tool(tool_name, arguments)
    if result.content:
        return [
            c.text if isinstance(c, TextContent) else str(c) for c in result.content
        ]
    return []


async def main():
    """
    Batch test for workflow_mcp MCP server tools (generate, list, run, delete).
    Spawns the server as a subprocess and connects via stdio.
    """
    with subprocess.Popen(
        MCP_SERVER_CMD, stdin=subprocess.PIPE, stdout=subprocess.PIPE
    ) as proc:
        server_params = StdioServerParameters(
            command=MCP_SERVER_CMD[0],
            args=MCP_SERVER_CMD[1:],
            env=os.environ.copy(),
        )
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                # 1. Generate workflow
                prompt = "Test workflow prompt for MCP tool batch test"
                print("\n[1] generate_workflow...")
                gen_result = await call_tool(
                    session, "generate_workflow", {"prompt": prompt}
                )
                print("Result:", gen_result)
                assert any(
                    "SUCCESS" in r for r in gen_result
                ), "generate_workflow failed"
                workflow_name = extract_workflow_name(gen_result[0])
                assert workflow_name, "No workflow_name extracted from result"
                # 2. List workflows
                print("\n[2] list_workflows...")
                list_result = await call_tool(session, "list_workflows", {})
                print("Result:", list_result)
                assert any(
                    workflow_name in r for r in list_result
                ), "Workflow not found in list"
                # 3. Run workflow
                print("\n[3] run_workflow...")
                run_result = await call_tool(
                    session, "run_workflow", {"workflow_id": workflow_name}
                )
                print("Result:", run_result)
                assert any("SUCCESS" in r for r in run_result), "run_workflow failed"
                # 4. Delete workflow
                print("\n[4] delete_workflow...")
                del_result = await call_tool(
                    session, "delete_workflow", {"workflow_id": workflow_name}
                )
                print("Result:", del_result)
                assert any("SUCCESS" in r for r in del_result), "delete_workflow failed"
                print("\nAll MCP tool tests passed.")


if __name__ == "__main__":
    asyncio.run(main())

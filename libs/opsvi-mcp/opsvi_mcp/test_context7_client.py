import asyncio

from src.shared.mcp.context7_mcp_client import Context7MCPClient


async def main():
    try:
        client = Context7MCPClient(
            mcp_config_path="/home/opsvi/agent_world/.cursor/mcp.json", debug=True
        )
        libs = await client.resolve_library_id("pydantic")
        print(f"Resolved libraries: {libs}")
    except Exception as e:
        import traceback

        print(f"Exception: {e}")
        print(traceback.format_exc())


if __name__ == "__main__":
    asyncio.run(main())

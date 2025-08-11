"""Quick test of collaboration integration with single agent"""

import asyncio

from src.shared.live_collaboration_integration import LiveCollaborationBridge


async def test_single_agent():
    bridge = LiveCollaborationBridge()
    result = await bridge.execute_collaboration_workflow(
        "Check vector health for research documents collection"
    )


if __name__ == "__main__":
    asyncio.run(test_single_agent())
else:
    pass

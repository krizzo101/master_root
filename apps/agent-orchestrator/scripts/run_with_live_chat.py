#!/usr/bin/env python3
"""
Run Orchestrator with Live Group Chat Integration
"""
import asyncio
import json
from pathlib import Path

from src.generic_orchestrator import AgentTask, GenericOrchestrator
from src.live_orchestrator_chat import add_live_chat_to_orchestrator


def create_test_tasks():
    """Create test tasks for group chat demo"""
    return [
        AgentTask(
            task_id="test_research_1",
            task_type="research-genius",
            prompt="Research the latest AI orchestration frameworks for 2025",
        ),
        AgentTask(
            task_id="test_analysis_1",
            task_type="solution-architect",
            prompt="Analyze system architecture patterns",
            dependencies=["test_research_1"],
        ),
    ]


async def run_orchestrator_with_chat():
    """Run orchestrator with live group chat"""

    output_dir = Path("./outputs/live_chat_test")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Create orchestrator with multi-provider support
    orchestrator = GenericOrchestrator(
        output_dir=output_dir,
        max_parallel=5,
        master_mcp_registry_path=Path("../../.mcp.json"),
    )

    # Add live chat integration
    live_chat = add_live_chat_to_orchestrator(orchestrator)

    # Start web interface on different port (8765 is dashboard)
    live_chat.start_web_interface(8766)

    print("🚀 Orchestrator with Live Chat Started!")
    print("💬 Group chat web interface: http://localhost:8766")
    print("📊 Multi-provider support active")
    print("🎯 Type commands: 'status', 'agents', 'tasks'")
    print("=" * 60)

    # Run orchestrator with test tasks
    try:
        results = await orchestrator.run(task_generator=create_test_tasks)
        print("✅ Orchestration completed with live chat!")
        return results

    except KeyboardInterrupt:
        print("\n🛑 Shutting down live chat...")
        live_chat.shutdown()
        return None


if __name__ == "__main__":
    print("🎉 Starting Badass AI Orchestrator with Live Group Chat!")
    asyncio.run(run_orchestrator_with_chat())

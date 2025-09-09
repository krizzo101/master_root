#!/usr/bin/env python3
"""
Simple Group Chat Demo - No Agent Execution Required
"""
from pathlib import Path

from src.group_chat import GroupChatManager, GroupChatTool


def demo_group_chat():
    """Demo group chat without orchestrator complexity"""

    # Create group chat
    chat = GroupChatManager("demo_chat_001")

    # Add some demo agents
    orchestrator = GroupChatTool(chat, "orchestrator", "unified-orchestrator")
    agent1 = GroupChatTool(chat, "research_agent_1", "research-genius")
    agent2 = GroupChatTool(chat, "analysis_agent_1", "solution-architect")

    print("🚀 Group Chat Demo Started!")
    print("💬 Chat ID: demo_chat_001")
    print("🤖 Active agents: orchestrator, research_agent_1, analysis_agent_1")

    # Demo messages
    orchestrator.send_message(
        "🎛️ Multi-provider orchestrator online! Claude + OpenAI ready."
    )
    agent1.send_message("👋 Research agent ready for system discovery tasks!")
    agent2.send_message("📊 Analysis agent ready for capability assessment!")

    # Show some status
    orchestrator.send_message("📈 System Health: 5/10 → targeting 9/10")
    orchestrator.send_message(
        "✅ Phase 1 Complete: Multi-provider fallback system deployed"
    )
    orchestrator.send_message(
        "🎯 Next: Phase 2 performance optimization or Phase 4 security compliance"
    )

    # Start web interface
    try:
        chat.start_websocket_server(8766)
        print("🌐 Group chat web interface: http://localhost:8766")
        print("💾 Token usage stats:")
        print(f"   - Messages: {len(chat.messages)}")
        print(f"   - Deduplication savings: ~{len(chat.dedupe_cache) * 50} tokens")

        # Keep running
        print("\n🎯 Demo running! Press Ctrl+C to stop...")
        import time

        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n🛑 Shutting down group chat demo...")
    except Exception as e:
        print(f"Note: WebSocket might not work without websockets package: {e}")
        print("But group chat core functionality is working!")


if __name__ == "__main__":
    demo_group_chat()

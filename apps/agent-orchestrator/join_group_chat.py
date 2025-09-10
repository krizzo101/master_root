#!/usr/bin/env python3
"""
Join Group Chat Tool - For other Claude Code agents to join coordination
"""
import sys
import time
from pathlib import Path

from src.group_chat import GroupChatManager, GroupChatTool


def join_chat(agent_name="claude_agent", agent_type="general-assistant"):
    """Join the group chat coordination"""

    # Connect to existing chat
    chat = GroupChatManager("demo_chat_001")
    agent = GroupChatTool(chat, agent_name, agent_type)

    print(f"🚀 {agent_name} joined group chat!")
    print("💬 Chat ID: demo_chat_001")
    print("🌐 Web interface: http://localhost:8766")

    # Send join message
    agent.send_message(f"👋 {agent_name} ready for coordination!")

    # Interactive mode
    print("\n🎯 Type messages (or 'exit' to quit):")
    try:
        while True:
            try:
                user_input = input(f"{agent_name}> ")
                if user_input.lower() == "exit":
                    break
                if user_input.strip():
                    agent.send_message(user_input)
            except EOFError:
                print("\n📝 Non-interactive mode - sending test message")
                agent.send_message(f"🤖 {agent_name} connected via CLI")
                break

    except KeyboardInterrupt:
        pass

    # Say goodbye
    agent.send_message(f"👋 {agent_name} leaving coordination")
    print(f"\n🛑 {agent_name} left group chat")

    return agent


if __name__ == "__main__":
    import sys

    agent_name = sys.argv[1] if len(sys.argv) > 1 else "claude_agent"
    join_chat(agent_name)

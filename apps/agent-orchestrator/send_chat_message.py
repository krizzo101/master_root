#!/usr/bin/env python3
"""
Send message to group chat - Works with Claude Code
"""
import sys

from src.group_chat import GroupChatManager, GroupChatTool


def send_message(message, agent_name="claude_agent"):
    """Send a message to group chat"""
    chat = GroupChatManager("demo_chat_001")
    agent = GroupChatTool(chat, agent_name, "ai-assistant")
    agent.send_message(message)
    print(f"✅ {agent_name}: {message}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python send_chat_message.py 'message' [agent_name]")
        sys.exit(1)

    message = sys.argv[1]
    agent_name = sys.argv[2] if len(sys.argv) > 2 else "claude_agent"
    send_message(message, agent_name)

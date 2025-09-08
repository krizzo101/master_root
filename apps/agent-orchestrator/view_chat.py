#!/usr/bin/env python3
"""
View Group Chat Messages
"""
from src.group_chat import GroupChatManager


def view_chat():
    chat = GroupChatManager("demo_chat_001")

    print(f"💬 Chat: {chat.chat_id}")
    print(f"📊 Total messages: {len(chat.messages)}")
    print(f"🤖 Active agents: {len(chat.agents)}")
    print("=" * 60)

    # Show recent messages
    recent = chat.messages[-10:] if len(chat.messages) > 10 else chat.messages

    for msg in recent:
        timestamp = f"{msg.timestamp:.0f}"[-6:]  # Last 6 digits
        print(f"[{timestamp}] {msg.agent_id}: {msg.content}")

    print("=" * 60)
    print("🔄 Run: python view_chat.py to refresh")


if __name__ == "__main__":
    view_chat()

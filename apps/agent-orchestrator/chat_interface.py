#!/usr/bin/env python3
"""
Combined Group Chat Interface - Send and View in one window
"""
import os
import threading
import time

from src.group_chat import GroupChatManager, GroupChatTool


class ChatInterface:
    def __init__(self, agent_name="user"):
        self.agent_name = agent_name
        self.chat = GroupChatManager("demo_chat_001")
        self.agent = GroupChatTool(self.chat, agent_name, "human-user")
        self.last_shown = 0
        self.running = True

    def show_new_messages(self):
        """Show only new messages since last check"""
        # Create fresh chat manager to get latest messages
        fresh_chat = GroupChatManager("demo_chat_001")
        if len(fresh_chat.messages) > self.last_shown:
            new_messages = fresh_chat.messages[self.last_shown :]
            for msg in new_messages:
                timestamp = f"{msg.timestamp:.0f}"[-6:]
                print(f"\n[{timestamp}] {msg.agent_id}: {msg.content}")
            self.last_shown = len(fresh_chat.messages)
            print(f"{self.agent_name}> ", end="", flush=True)  # Restore prompt

    def monitor_messages(self):
        """Background thread to show new messages"""
        while self.running:
            try:
                self.show_new_messages()
                time.sleep(2)  # Check every 2 seconds
            except:
                break

    def run(self):
        """Main chat interface"""
        print(f"💬 Group Chat - {self.agent_name}")
        print("📊 Type messages, see responses in real-time")
        print("=" * 50)

        # Show existing messages
        self.show_new_messages()

        # Start background monitor
        monitor_thread = threading.Thread(target=self.monitor_messages, daemon=True)
        monitor_thread.start()

        # Interactive loop
        try:
            while True:
                user_input = input(f"{self.agent_name}> ")
                if user_input.lower() in ["exit", "quit"]:
                    break
                if user_input.strip():
                    self.agent.send_message(user_input)
                    time.sleep(0.5)  # Brief pause to see your own message

        except (KeyboardInterrupt, EOFError):
            pass

        self.running = False
        print(f"\n👋 {self.agent_name} left chat")


if __name__ == "__main__":
    import sys

    agent_name = sys.argv[1] if len(sys.argv) > 1 else "user"

    interface = ChatInterface(agent_name)
    interface.run()

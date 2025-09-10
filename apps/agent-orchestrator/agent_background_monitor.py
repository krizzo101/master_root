#!/usr/bin/env python3
"""
Keep Claude Code agents "alive" in background - respond when mentioned
"""
import subprocess
import time

from src.group_chat import GroupChatManager


class AgentMonitor:
    def __init__(self):
        self.chat = GroupChatManager("demo_chat_001")
        self.last_checked = len(self.chat.messages)
        self.active_agents = {
            "agent_2": "/path/to/agent2/claude/session",
            "agent_3": "/path/to/agent3/claude/session",
        }

    def monitor_and_respond(self):
        """Monitor chat and trigger agent responses"""
        while True:
            # Check for new messages
            fresh_chat = GroupChatManager("demo_chat_001")
            new_messages = fresh_chat.messages[self.last_checked :]

            for msg in new_messages:
                # Check if any agent is mentioned
                for agent_name in self.active_agents:
                    if (
                        agent_name in msg.content.lower()
                        or "@" + agent_name in msg.content
                    ):
                        # Trigger that agent to respond
                        self._trigger_agent(agent_name, msg)

            self.last_checked = len(fresh_chat.messages)
            time.sleep(3)  # Check every 3 seconds

    def _trigger_agent(self, agent_name, message):
        """Trigger a Claude Code agent to respond to message"""
        # This would call the agent's Claude Code session
        # For now, just simulate a response
        response = f"🤖 {agent_name} responding to: '{message.content[:30]}...'"
        subprocess.run(["python", "send_chat_message.py", response, agent_name])


if __name__ == "__main__":
    monitor = AgentMonitor()
    monitor.monitor_and_respond()

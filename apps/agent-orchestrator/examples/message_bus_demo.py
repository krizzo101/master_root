#!/usr/bin/env python3
"""
Message Bus Demo - Interactive demonstration of agent collaboration features

This script demonstrates key features of the message bus system:
- Agent connections and heartbeats
- Point-to-point messaging
- Broadcast messaging
- Topic-based subscriptions
- Group-based messaging
- Error handling and reconnection

Usage:
    python examples/message_bus_demo.py
"""

import asyncio
import json
import logging
import sys
import time
from pathlib import Path
from typing import Any, Dict

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.message_bus.simple_client import SimpleMessageClient

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DemoAgent:
    """Demo agent that showcases message bus features"""

    def __init__(self, agent_id: str, capabilities: list = None):
        self.agent_id = agent_id
        self.capabilities = capabilities or ["demo", "test"]

        # Create message client
        self.client = SimpleMessageClient(
            agent_id=agent_id,
            capabilities=self.capabilities,
            auto_reconnect=True,
        )

        # Message counters
        self.messages_sent = 0
        self.messages_received = 0

        # Setup message handlers
        self.client.register_direct_handler(self.handle_direct_message)
        self.client.register_broadcast_handler(self.handle_broadcast_message)

        logger.info(
            f"DemoAgent {agent_id} created with capabilities: {self.capabilities}"
        )

    async def connect(self) -> bool:
        """Connect to message bus"""
        print(f"🔌 {self.agent_id}: Connecting to message bus...")
        success = await self.client.connect()
        if success:
            print(f"✅ {self.agent_id}: Connected successfully!")
        else:
            print(f"❌ {self.agent_id}: Connection failed!")
        return success

    async def disconnect(self):
        """Disconnect from message bus"""
        print(f"🔌 {self.agent_id}: Disconnecting...")
        await self.client.disconnect()
        print(f"✅ {self.agent_id}: Disconnected")

    def handle_direct_message(self, sender_id: str, data: Dict[str, Any]):
        """Handle direct messages"""
        self.messages_received += 1
        message_type = data.get("type", "unknown")
        content = data.get("content", "")

        print(f"📨 {self.agent_id}: Direct message from {sender_id}")
        print(f"   Type: {message_type}")
        print(f"   Content: {content}")

        # Auto-respond to certain message types
        if message_type == "ping":
            asyncio.create_task(self.send_pong(sender_id))
        elif message_type == "request_status":
            asyncio.create_task(self.send_status(sender_id))

    def handle_broadcast_message(self, sender_id: str, data: Dict[str, Any]):
        """Handle broadcast messages"""
        if sender_id == self.agent_id:
            return  # Ignore our own broadcasts

        self.messages_received += 1
        message_type = data.get("type", "unknown")
        content = data.get("content", "")

        print(f"📢 {self.agent_id}: Broadcast from {sender_id}")
        print(f"   Type: {message_type}")
        print(f"   Content: {content}")

    def handle_topic_message(self, data: Dict[str, Any]):
        """Handle topic messages"""
        self.messages_received += 1
        topic = data.get("topic", "unknown")
        content = data.get("content", "")

        print(f"🏷️  {self.agent_id}: Topic message on '{topic}'")
        print(f"   Content: {content}")

    def handle_group_message(self, data: Dict[str, Any]):
        """Handle group messages"""
        self.messages_received += 1
        group = data.get("group", "unknown")
        content = data.get("content", "")

        print(f"👥 {self.agent_id}: Group message in '{group}'")
        print(f"   Content: {content}")

    async def send_ping(self, target_agent: str):
        """Send ping message to specific agent"""
        data = {
            "type": "ping",
            "content": f"Ping from {self.agent_id}",
            "timestamp": time.time(),
        }

        response = await self.client.send_to_agent(target_agent, data)
        if response.success:
            self.messages_sent += 1
            print(f"🏓 {self.agent_id}: Sent ping to {target_agent}")
        else:
            print(f"❌ {self.agent_id}: Failed to send ping - {response.error}")

    async def send_pong(self, target_agent: str):
        """Send pong response"""
        data = {
            "type": "pong",
            "content": f"Pong from {self.agent_id}",
            "timestamp": time.time(),
        }

        response = await self.client.send_to_agent(target_agent, data)
        if response.success:
            self.messages_sent += 1
            print(f"🏓 {self.agent_id}: Sent pong to {target_agent}")

    async def send_status(self, target_agent: str):
        """Send status information"""
        data = {
            "type": "status_response",
            "content": f"Status from {self.agent_id}",
            "stats": {
                "messages_sent": self.messages_sent,
                "messages_received": self.messages_received,
                "capabilities": self.capabilities,
                "connected": self.client.is_connected,
            },
        }

        response = await self.client.send_to_agent(target_agent, data)
        if response.success:
            self.messages_sent += 1
            print(f"📊 {self.agent_id}: Sent status to {target_agent}")

    async def broadcast_announcement(self, announcement: str):
        """Broadcast announcement to all agents"""
        data = {
            "type": "announcement",
            "content": announcement,
            "timestamp": time.time(),
            "from": self.agent_id,
        }

        response = await self.client.broadcast(data)
        if response.success:
            self.messages_sent += 1
            print(f"📢 {self.agent_id}: Broadcasted announcement")
        else:
            print(f"❌ {self.agent_id}: Failed to broadcast - {response.error}")

    async def publish_to_topic(self, topic: str, message: str):
        """Publish message to topic"""
        data = {
            "type": "topic_message",
            "topic": topic,
            "content": message,
            "timestamp": time.time(),
        }

        response = await self.client.send_to_topic(topic, data)
        if response.success:
            self.messages_sent += 1
            print(f"🏷️  {self.agent_id}: Published to topic '{topic}'")
        else:
            print(f"❌ {self.agent_id}: Failed to publish to topic - {response.error}")

    async def subscribe_to_topic(self, topic: str):
        """Subscribe to a topic"""
        success = await self.client.subscribe_topic(topic, self.handle_topic_message)
        if success:
            print(f"🏷️  {self.agent_id}: Subscribed to topic '{topic}'")
        else:
            print(f"❌ {self.agent_id}: Failed to subscribe to topic '{topic}'")

    async def join_group(self, group_id: str):
        """Join a message group"""
        success = await self.client.join_group(group_id, self.handle_group_message)
        if success:
            print(f"👥 {self.agent_id}: Joined group '{group_id}'")
        else:
            print(f"❌ {self.agent_id}: Failed to join group '{group_id}'")

    def get_stats(self) -> Dict[str, Any]:
        """Get agent statistics"""
        return {
            "agent_id": self.agent_id,
            "capabilities": self.capabilities,
            "messages_sent": self.messages_sent,
            "messages_received": self.messages_received,
            "connected": self.client.is_connected,
        }


async def demo_point_to_point_messaging(agents: list):
    """Demonstrate point-to-point messaging"""
    print("\n" + "=" * 50)
    print("🎯 DEMO: Point-to-Point Messaging")
    print("=" * 50)

    if len(agents) < 2:
        print("Need at least 2 agents for this demo")
        return

    # Agent 1 sends ping to Agent 2
    await agents[0].send_ping(agents[1].agent_id)
    await asyncio.sleep(1)

    # Agent 2 requests status from Agent 1
    data = {"type": "request_status", "content": "Please send your status"}
    response = await agents[1].client.send_to_agent(agents[0].agent_id, data)
    if response.success:
        print(f"📊 {agents[1].agent_id}: Requested status from {agents[0].agent_id}")

    await asyncio.sleep(2)


async def demo_broadcast_messaging(agents: list):
    """Demonstrate broadcast messaging"""
    print("\n" + "=" * 50)
    print("📢 DEMO: Broadcast Messaging")
    print("=" * 50)

    if not agents:
        print("No agents available for broadcast demo")
        return

    # First agent broadcasts announcement
    await agents[0].broadcast_announcement("Hello everyone! This is a broadcast demo!")
    await asyncio.sleep(2)

    # Another agent broadcasts
    if len(agents) > 1:
        await agents[1].broadcast_announcement("Broadcasting from agent 2!")
        await asyncio.sleep(2)


async def demo_topic_messaging(agents: list):
    """Demonstrate topic-based messaging"""
    print("\n" + "=" * 50)
    print("🏷️  DEMO: Topic-Based Messaging")
    print("=" * 50)

    if len(agents) < 2:
        print("Need at least 2 agents for topic demo")
        return

    # Subscribe agents to different topics
    await agents[0].subscribe_to_topic("alerts")
    await agents[1].subscribe_to_topic("alerts")

    if len(agents) > 2:
        await agents[2].subscribe_to_topic("notifications")

    await asyncio.sleep(1)

    # Publish to topics
    await agents[0].publish_to_topic("alerts", "High priority alert!")
    await asyncio.sleep(1)

    if len(agents) > 2:
        await agents[1].publish_to_topic(
            "notifications", "General notification message"
        )
        await asyncio.sleep(1)


async def demo_group_messaging(agents: list):
    """Demonstrate group-based messaging"""
    print("\n" + "=" * 50)
    print("👥 DEMO: Group Messaging")
    print("=" * 50)

    if len(agents) < 3:
        print("Need at least 3 agents for group demo")
        return

    # Create groups
    await agents[0].join_group("team_alpha")
    await agents[1].join_group("team_alpha")
    if len(agents) > 2:
        await agents[2].join_group("team_beta")

    await asyncio.sleep(1)

    # Send group messages
    data = {
        "type": "group_message",
        "group": "team_alpha",
        "content": "Team Alpha meeting in 5 minutes",
    }
    response = await agents[0].client.send_to_group("team_alpha", data)
    if response.success:
        print(f"👥 {agents[0].agent_id}: Sent message to team_alpha")

    await asyncio.sleep(2)


async def demo_performance_test(agents: list):
    """Demonstrate system performance"""
    print("\n" + "=" * 50)
    print("⚡ DEMO: Performance Test")
    print("=" * 50)

    if len(agents) < 2:
        print("Need at least 2 agents for performance demo")
        return

    # Rapid message exchange
    start_time = time.time()
    message_count = 20

    print(f"Sending {message_count} messages rapidly...")

    for i in range(message_count):
        sender = agents[i % len(agents)]
        receiver = agents[(i + 1) % len(agents)]

        data = {
            "type": "performance_test",
            "content": f"Performance test message {i}",
            "sequence": i,
        }

        response = await sender.client.send_to_agent(receiver.agent_id, data)
        if response.success:
            sender.messages_sent += 1

        # Small delay to prevent overwhelming
        await asyncio.sleep(0.01)

    duration = time.time() - start_time
    messages_per_second = message_count / duration

    print(f"✅ Sent {message_count} messages in {duration:.2f}s")
    print(f"🚀 Throughput: {messages_per_second:.1f} messages/second")

    await asyncio.sleep(2)


async def print_final_stats(agents: list):
    """Print final statistics"""
    print("\n" + "=" * 50)
    print("📊 FINAL STATISTICS")
    print("=" * 50)

    total_sent = sum(agent.messages_sent for agent in agents)
    total_received = sum(agent.messages_received for agent in agents)

    print(f"Total messages sent: {total_sent}")
    print(f"Total messages received: {total_received}")
    print()

    for agent in agents:
        stats = agent.get_stats()
        print(f"{agent.agent_id}:")
        print(f"  Sent: {stats['messages_sent']}")
        print(f"  Received: {stats['messages_received']}")
        print(f"  Connected: {stats['connected']}")


async def main():
    """Main demo function"""
    print("🚀 MESSAGE BUS DEMO STARTING")
    print("=" * 60)
    print("This demo will showcase key features of the message bus:")
    print("- Point-to-point messaging")
    print("- Broadcast messaging")
    print("- Topic subscriptions")
    print("- Group messaging")
    print("- Performance testing")
    print()

    # Create demo agents
    agent_configs = [
        ("agent_alpha", ["demo", "leader", "ping"]),
        ("agent_beta", ["demo", "worker", "pong"]),
        ("agent_gamma", ["demo", "monitor", "stats"]),
    ]

    agents = []

    try:
        # Create and connect agents
        print("👥 Creating demo agents...")
        for agent_id, capabilities in agent_configs:
            agent = DemoAgent(agent_id, capabilities)
            success = await agent.connect()
            if success:
                agents.append(agent)
            else:
                print(f"❌ Failed to connect {agent_id}")

        if not agents:
            print("❌ No agents connected. Is the message bus server running?")
            print("   Start it with: python message_bus_server.py")
            return

        print(f"✅ Connected {len(agents)} agents")
        await asyncio.sleep(2)

        # Run demos
        await demo_point_to_point_messaging(agents)
        await demo_broadcast_messaging(agents)
        await demo_topic_messaging(agents)
        await demo_group_messaging(agents)
        await demo_performance_test(agents)

        # Print final statistics
        await print_final_stats(agents)

        print("\n🎉 Demo completed successfully!")

    except KeyboardInterrupt:
        print("\n⏹️  Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        logger.exception("Demo error")
    finally:
        # Cleanup
        print("\n🧹 Cleaning up...")
        for agent in agents:
            try:
                await agent.disconnect()
            except Exception as e:
                logger.warning(f"Error disconnecting {agent.agent_id}: {e}")

        print("✅ Cleanup complete")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Demo shutdown complete!")
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        sys.exit(1)

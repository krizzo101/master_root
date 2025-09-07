#!/usr/bin/env python3
"""
Agent Collaboration Example - Real-world usage of the message bus for agent coordination

This example demonstrates how agents can use the message bus for collaborative tasks:
- Task delegation and work distribution
- Progress updates and status reporting
- Resource sharing and coordination
- Error handling and fallback mechanisms

Usage:
    python examples/agent_collaboration_example.py
"""

import asyncio
import logging
import random
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.message_bus.simple_client import SimpleMessageClient

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class Task:
    """Represents a task that can be delegated between agents"""

    task_id: str
    task_type: str
    data: Dict[str, Any]
    priority: str = "normal"
    timeout_seconds: int = 60
    created_at: float = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "task_type": self.task_type,
            "data": self.data,
            "priority": self.priority,
            "timeout_seconds": self.timeout_seconds,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Task":
        return cls(
            task_id=data["task_id"],
            task_type=data["task_type"],
            data=data["data"],
            priority=data.get("priority", "normal"),
            timeout_seconds=data.get("timeout_seconds", 60),
            created_at=data.get("created_at", time.time()),
        )


class CollaborativeAgent:
    """Base class for collaborative agents using the message bus"""

    def __init__(self, agent_id: str, agent_type: str, capabilities: List[str]):
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.capabilities = capabilities

        # Message bus client
        self.client = SimpleMessageClient(
            agent_id=agent_id,
            capabilities=capabilities,
            auto_reconnect=True,
        )

        # Agent state
        self.active_tasks: Dict[str, Task] = {}
        self.completed_tasks: List[str] = []
        self.available_for_work = True
        self.load_factor = 0.0  # 0.0 = idle, 1.0 = fully loaded

        # Register message handlers
        self.client.register_direct_handler(self.handle_direct_message)
        self.client.register_broadcast_handler(self.handle_broadcast_message)

        # Subscribe to relevant topics
        asyncio.create_task(self._setup_subscriptions())

        logger.info(f"CollaborativeAgent {agent_id} ({agent_type}) created")

    async def connect(self) -> bool:
        """Connect to the message bus"""
        success = await self.client.connect()
        if success:
            # Join the general collaboration group
            await self.client.join_group("collaboration", self.handle_group_message)

            # Subscribe to task-related topics
            await self.client.subscribe_topic("tasks", self.handle_task_topic)
            await self.client.subscribe_topic(
                "status_updates", self.handle_status_topic
            )

            # Announce availability
            await self.announce_availability()

        return success

    async def disconnect(self):
        """Disconnect from the message bus"""
        await self.client.disconnect()

    async def _setup_subscriptions(self):
        """Setup topic subscriptions based on capabilities"""
        await asyncio.sleep(1)  # Wait for connection

        # Subscribe to capability-specific topics
        for capability in self.capabilities:
            topic_name = f"tasks_{capability}"
            await self.client.subscribe_topic(topic_name, self.handle_capability_task)

    def handle_direct_message(self, sender_id: str, data: Dict[str, Any]):
        """Handle direct messages from other agents"""
        message_type = data.get("type", "unknown")

        if message_type == "task_request":
            asyncio.create_task(self._handle_task_request(sender_id, data))
        elif message_type == "task_response":
            asyncio.create_task(self._handle_task_response(sender_id, data))
        elif message_type == "status_request":
            asyncio.create_task(self._handle_status_request(sender_id))
        elif message_type == "resource_request":
            asyncio.create_task(self._handle_resource_request(sender_id, data))
        else:
            logger.info(
                f"{self.agent_id}: Received direct message from {sender_id}: {message_type}"
            )

    def handle_broadcast_message(self, sender_id: str, data: Dict[str, Any]):
        """Handle broadcast messages"""
        message_type = data.get("type", "unknown")

        if message_type == "emergency_stop":
            asyncio.create_task(self._handle_emergency_stop(sender_id, data))
        elif message_type == "system_announcement":
            logger.info(f"{self.agent_id}: System announcement: {data.get('content')}")
        else:
            logger.debug(f"{self.agent_id}: Broadcast from {sender_id}: {message_type}")

    def handle_group_message(self, data: Dict[str, Any]):
        """Handle group messages in the collaboration group"""
        message_type = data.get("type", "unknown")
        sender_id = data.get("sender_id", "unknown")

        if message_type == "coordination_request":
            asyncio.create_task(self._handle_coordination_request(sender_id, data))
        elif message_type == "resource_sharing":
            asyncio.create_task(self._handle_resource_sharing(sender_id, data))
        else:
            logger.debug(f"{self.agent_id}: Group message: {message_type}")

    def handle_task_topic(self, data: Dict[str, Any]):
        """Handle messages on the tasks topic"""
        message_type = data.get("type", "unknown")

        if message_type == "task_available" and self.can_accept_task(data):
            asyncio.create_task(self._consider_task_acceptance(data))

    def handle_capability_task(self, data: Dict[str, Any]):
        """Handle messages for capability-specific tasks"""
        if self.can_accept_task(data):
            asyncio.create_task(self._consider_task_acceptance(data))

    def handle_status_topic(self, data: Dict[str, Any]):
        """Handle status update messages"""
        message_type = data.get("type", "unknown")
        sender_id = data.get("sender_id", "unknown")

        if message_type == "agent_status_update":
            logger.debug(f"{self.agent_id}: Status update from {sender_id}")

    async def announce_availability(self):
        """Announce agent availability to the collaboration network"""
        announcement = {
            "type": "agent_available",
            "agent_id": self.agent_id,
            "agent_type": self.agent_type,
            "capabilities": self.capabilities,
            "load_factor": self.load_factor,
            "available_for_work": self.available_for_work,
            "timestamp": time.time(),
        }

        await self.client.send_to_topic("status_updates", announcement)
        logger.info(f"{self.agent_id}: Announced availability")

    async def delegate_task(
        self, task: Task, target_agent: Optional[str] = None
    ) -> bool:
        """Delegate a task to another agent or broadcast for pickup"""
        task_data = {
            "type": "task_request",
            "task": task.to_dict(),
            "requester_id": self.agent_id,
            "timestamp": time.time(),
        }

        if target_agent:
            # Direct delegation
            response = await self.client.send_to_agent(target_agent, task_data)
            if response.success:
                logger.info(
                    f"{self.agent_id}: Delegated task {task.task_id} to {target_agent}"
                )
                return True
        else:
            # Broadcast for any capable agent to pick up
            response = await self.client.send_to_topic("tasks", task_data)
            if response.success:
                logger.info(
                    f"{self.agent_id}: Broadcast task {task.task_id} for pickup"
                )
                return True

        return False

    async def report_progress(self, task_id: str, progress: float, status: str):
        """Report task progress to interested parties"""
        progress_data = {
            "type": "progress_update",
            "task_id": task_id,
            "agent_id": self.agent_id,
            "progress": progress,
            "status": status,
            "timestamp": time.time(),
        }

        await self.client.send_to_topic("status_updates", progress_data)
        logger.info(
            f"{self.agent_id}: Reported progress for task {task_id}: {progress:.1%} ({status})"
        )

    async def complete_task(self, task: Task, result: Dict[str, Any]):
        """Mark a task as completed and report results"""
        # Remove from active tasks
        if task.task_id in self.active_tasks:
            del self.active_tasks[task.task_id]

        self.completed_tasks.append(task.task_id)
        self._update_load_factor()

        # Report completion
        completion_data = {
            "type": "task_completed",
            "task_id": task.task_id,
            "agent_id": self.agent_id,
            "result": result,
            "completion_time": time.time(),
        }

        await self.client.send_to_topic("status_updates", completion_data)
        logger.info(f"{self.agent_id}: Completed task {task.task_id}")

    def can_accept_task(self, task_data: Dict[str, Any]) -> bool:
        """Check if agent can accept a task based on capabilities and load"""
        if not self.available_for_work:
            return False

        task = Task.from_dict(task_data.get("task", {}))

        # Check if we have required capabilities
        required_caps = task.data.get("required_capabilities", [])
        if required_caps and not any(cap in self.capabilities for cap in required_caps):
            return False

        # Check load factor
        if self.load_factor >= 0.8:  # 80% capacity limit
            return False

        return True

    def _update_load_factor(self):
        """Update load factor based on active tasks"""
        max_concurrent_tasks = 3  # Configurable limit
        self.load_factor = len(self.active_tasks) / max_concurrent_tasks

    async def _handle_task_request(self, sender_id: str, data: Dict[str, Any]):
        """Handle incoming task requests"""
        task_data = data.get("task", {})
        task = Task.from_dict(task_data)

        if self.can_accept_task(data):
            # Accept the task
            self.active_tasks[task.task_id] = task
            self._update_load_factor()

            # Send acceptance response
            response_data = {
                "type": "task_response",
                "task_id": task.task_id,
                "status": "accepted",
                "agent_id": self.agent_id,
                "estimated_completion": time.time() + task.timeout_seconds / 2,
            }

            await self.client.send_to_agent(sender_id, response_data)
            logger.info(
                f"{self.agent_id}: Accepted task {task.task_id} from {sender_id}"
            )

            # Start processing the task
            asyncio.create_task(self._process_task(task))
        else:
            # Reject the task
            response_data = {
                "type": "task_response",
                "task_id": task.task_id,
                "status": "rejected",
                "agent_id": self.agent_id,
                "reason": "Cannot accept task (overloaded or missing capabilities)",
            }

            await self.client.send_to_agent(sender_id, response_data)
            logger.info(
                f"{self.agent_id}: Rejected task {task.task_id} from {sender_id}"
            )

    async def _handle_task_response(self, sender_id: str, data: Dict[str, Any]):
        """Handle task responses from other agents"""
        task_id = data.get("task_id")
        status = data.get("status")

        logger.info(f"{self.agent_id}: Task {task_id} {status} by {sender_id}")

    async def _handle_status_request(self, sender_id: str):
        """Handle status requests from other agents"""
        status_data = {
            "type": "status_response",
            "agent_id": self.agent_id,
            "agent_type": self.agent_type,
            "capabilities": self.capabilities,
            "active_tasks": len(self.active_tasks),
            "completed_tasks": len(self.completed_tasks),
            "load_factor": self.load_factor,
            "available_for_work": self.available_for_work,
            "timestamp": time.time(),
        }

        await self.client.send_to_agent(sender_id, status_data)

    async def _consider_task_acceptance(self, data: Dict[str, Any]):
        """Consider accepting a publicly available task"""
        if random.random() < 0.3:  # 30% chance to show interest
            task_data = data.get("task", {})
            task = Task.from_dict(task_data)
            requester_id = data.get("requester_id")

            if requester_id and self.can_accept_task(data):
                # Send interest in the task
                interest_data = {
                    "type": "task_interest",
                    "task_id": task.task_id,
                    "agent_id": self.agent_id,
                    "capabilities": self.capabilities,
                    "load_factor": self.load_factor,
                    "timestamp": time.time(),
                }

                await self.client.send_to_agent(requester_id, interest_data)
                logger.info(
                    f"{self.agent_id}: Expressed interest in task {task.task_id}"
                )

    async def _process_task(self, task: Task):
        """Process a task (simulate work)"""
        logger.info(f"{self.agent_id}: Starting task {task.task_id} ({task.task_type})")

        # Simulate task processing with progress updates
        total_steps = random.randint(3, 8)
        for step in range(total_steps):
            await asyncio.sleep(random.uniform(1, 3))  # Simulate work

            progress = (step + 1) / total_steps
            await self.report_progress(
                task.task_id, progress, f"Step {step + 1}/{total_steps}"
            )

        # Generate mock result
        result = {
            "success": True,
            "output": f"Processed {task.task_type} task with data: {task.data}",
            "processing_time": time.time() - task.created_at,
            "steps_completed": total_steps,
        }

        await self.complete_task(task, result)

    async def _handle_emergency_stop(self, sender_id: str, data: Dict[str, Any]):
        """Handle emergency stop requests"""
        reason = data.get("reason", "Unknown")
        logger.warning(
            f"{self.agent_id}: Emergency stop requested by {sender_id}: {reason}"
        )

        # Stop accepting new work
        self.available_for_work = False

        # Cancel active tasks (simplified)
        for task_id in list(self.active_tasks.keys()):
            logger.warning(
                f"{self.agent_id}: Cancelling task {task_id} due to emergency stop"
            )
            del self.active_tasks[task_id]

        self._update_load_factor()

    async def _handle_coordination_request(self, sender_id: str, data: Dict[str, Any]):
        """Handle coordination requests from other agents"""
        coord_type = data.get("coordination_type", "unknown")
        logger.info(
            f"{self.agent_id}: Coordination request from {sender_id}: {coord_type}"
        )

    async def _handle_resource_request(self, sender_id: str, data: Dict[str, Any]):
        """Handle resource sharing requests"""
        resource_type = data.get("resource_type", "unknown")
        logger.info(
            f"{self.agent_id}: Resource request from {sender_id}: {resource_type}"
        )

    async def _handle_resource_sharing(self, sender_id: str, data: Dict[str, Any]):
        """Handle resource sharing announcements"""
        resource_type = data.get("resource_type", "unknown")
        logger.info(f"{self.agent_id}: Resource shared by {sender_id}: {resource_type}")


class ManagerAgent(CollaborativeAgent):
    """Agent that specializes in task management and coordination"""

    def __init__(self):
        super().__init__(
            agent_id="manager_agent",
            agent_type="manager",
            capabilities=["coordination", "planning", "monitoring"],
        )
        self.managed_tasks: Dict[str, Dict] = {}

    async def create_and_delegate_tasks(self):
        """Create sample tasks and delegate them"""
        task_types = [
            ("data_processing", {"dataset": "customer_data.csv", "operation": "clean"}),
            ("analysis", {"data": [1, 2, 3, 4, 5], "type": "statistical"}),
            (
                "report_generation",
                {"template": "quarterly_report", "data_source": "analytics_db"},
            ),
            (
                "validation",
                {
                    "rules": ["check_duplicates", "validate_format"],
                    "target": "processed_data",
                },
            ),
        ]

        for i, (task_type, task_data) in enumerate(task_types):
            task = Task(
                task_id=f"task_{i+1}",
                task_type=task_type,
                data=task_data,
                priority="normal" if i < 2 else "high",
            )

            self.managed_tasks[task.task_id] = {
                "task": task,
                "status": "delegated",
                "assigned_agent": None,
                "created_at": time.time(),
            }

            success = await self.delegate_task(task)
            if success:
                logger.info(f"Manager: Delegated {task_type} task")

            await asyncio.sleep(1)


class WorkerAgent(CollaborativeAgent):
    """Agent that specializes in processing specific types of tasks"""

    def __init__(self, agent_id: str, specialization: str):
        capabilities = ["processing", specialization]
        super().__init__(
            agent_id=agent_id,
            agent_type="worker",
            capabilities=capabilities,
        )
        self.specialization = specialization


async def run_collaboration_demo():
    """Run the agent collaboration demonstration"""
    print("🤖 AGENT COLLABORATION DEMO")
    print("=" * 50)

    # Create agents
    manager = ManagerAgent()
    workers = [
        WorkerAgent("data_worker", "data_processing"),
        WorkerAgent("analysis_worker", "analysis"),
        WorkerAgent("report_worker", "report_generation"),
    ]

    all_agents = [manager] + workers

    try:
        # Connect all agents
        print("🔌 Connecting agents to message bus...")
        for agent in all_agents:
            success = await agent.connect()
            if success:
                print(f"✅ {agent.agent_id} connected")
            else:
                print(f"❌ {agent.agent_id} failed to connect")

        # Wait for connections to settle
        await asyncio.sleep(2)

        # Manager delegates tasks
        print("\n📋 Manager creating and delegating tasks...")
        await manager.create_and_delegate_tasks()

        # Let the collaboration run for a while
        print("\n⚡ Agents collaborating...")
        await asyncio.sleep(30)

        # Request status from all agents
        print("\n📊 Requesting final status from all agents...")
        for agent in all_agents:
            stats = {
                "agent_id": agent.agent_id,
                "active_tasks": len(agent.active_tasks),
                "completed_tasks": len(agent.completed_tasks),
                "load_factor": agent.load_factor,
            }
            print(f"  {agent.agent_id}: {stats}")

        print("\n✅ Collaboration demo completed successfully!")

    except KeyboardInterrupt:
        print("\n⏹️  Demo interrupted by user")
    except Exception as e:
        logger.exception("Demo failed")
        print(f"\n❌ Demo failed: {e}")
    finally:
        # Cleanup
        print("\n🧹 Disconnecting agents...")
        for agent in all_agents:
            try:
                await agent.disconnect()
                print(f"✅ {agent.agent_id} disconnected")
            except Exception as e:
                print(f"❌ Error disconnecting {agent.agent_id}: {e}")


if __name__ == "__main__":
    try:
        asyncio.run(run_collaboration_demo())
    except KeyboardInterrupt:
        print("\n👋 Collaboration demo shutdown complete!")
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        sys.exit(1)

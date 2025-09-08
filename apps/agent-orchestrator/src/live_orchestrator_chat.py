"""
Live Orchestrator Chat Integration
Orchestrator agents join group chat for real-time coordination
"""
import json
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from .group_chat import GroupChatManager, GroupChatTool


class LiveOrchestratorChat:
    """Integrates orchestrator with group chat for real-time updates"""

    def __init__(self, orchestrator, chat_manager: GroupChatManager = None):
        self.orchestrator = orchestrator
        self.chat_manager = chat_manager or GroupChatManager("orchestrator_live")

        # Register orchestrator as special agent
        self.orchestrator_tool = GroupChatTool(
            chat_manager=self.chat_manager,
            agent_id="orchestrator",
            agent_type="unified-orchestrator",
        )

        # Track live agents
        self.live_agents: Dict[str, GroupChatTool] = {}

        # Start monitoring thread
        self.monitoring = True
        self.monitor_thread = threading.Thread(
            target=self._monitor_orchestrator, daemon=True
        )
        self.monitor_thread.start()

        print("🚀 Live orchestrator chat started!")
        print(f"💬 Chat ID: {self.chat_manager.chat_id}")

        # Send startup message
        task_count = getattr(self.orchestrator, "tasks", [])
        self.orchestrator_tool.send_message(
            f"🎛️ Orchestrator online! Ready to coordinate {len(task_count)} agents."
        )

    def _monitor_orchestrator(self):
        """Monitor orchestrator state and send live updates"""
        last_task_states = {}
        last_metrics = {}

        while self.monitoring:
            try:
                # Check for task state changes
                current_states = {}
                if hasattr(self.orchestrator, "tasks"):
                    for task in self.orchestrator.tasks:
                        current_states[task.task_id] = getattr(
                            task, "status", "unknown"
                        )

                # Report state changes
                for task_id, current_state in current_states.items():
                    last_state = last_task_states.get(task_id)
                    if last_state != current_state:
                        if current_state == "running":
                            self.orchestrator_tool.send_message(
                                f"🚀 Starting {task_id} ({getattr(self._get_task(task_id), 'task_type', 'unknown')})"
                            )
                        elif current_state == "completed":
                            duration = self._get_task_duration(task_id)
                            self.orchestrator_tool.send_message(
                                f"✅ {task_id} completed in {duration:.1f}s"
                            )
                        elif current_state == "failed":
                            self.orchestrator_tool.send_message(
                                f"❌ {task_id} failed - investigating..."
                            )

                last_task_states = current_states

                # Report metrics periodically
                if hasattr(self.orchestrator, "metrics"):
                    current_metrics = getattr(self.orchestrator, "metrics", {})
                    if current_metrics != last_metrics:
                        self._report_metrics_update(current_metrics)
                        last_metrics = current_metrics.copy()

                time.sleep(5)  # Check every 5 seconds

            except Exception as e:
                print(f"Error in orchestrator monitoring: {e}")
                time.sleep(10)

    def _get_task(self, task_id: str):
        """Get task object by ID"""
        if hasattr(self.orchestrator, "tasks"):
            for task in self.orchestrator.tasks:
                if getattr(task, "task_id", None) == task_id:
                    return task
        return None

    def _get_task_duration(self, task_id: str) -> float:
        """Get task execution duration"""
        task = self._get_task(task_id)
        if task and hasattr(task, "start_time") and hasattr(task, "end_time"):
            return task.end_time - task.start_time
        return 0.0

    def _report_metrics_update(self, metrics: Dict):
        """Report metrics changes to chat"""
        if "completed" in metrics and "total" in metrics and metrics["total"] > 0:
            progress = metrics["completed"] / metrics["total"] * 100
            self.orchestrator_tool.send_message(
                f"📊 Progress: {progress:.1f}% ({metrics['completed']}/{metrics['total']} tasks)"
            )

        if "failed" in metrics and metrics["failed"] > 0:
            self.orchestrator_tool.send_message(
                f"⚠️ {metrics['failed']} tasks failed - may need attention"
            )

    def register_live_agent(self, agent_id: str, agent_type: str, agent_instance=None):
        """Register agent for live chat participation"""
        agent_tool = GroupChatTool(
            chat_manager=self.chat_manager, agent_id=agent_id, agent_type=agent_type
        )

        self.live_agents[agent_id] = agent_tool

        # Send agent introduction
        agent_tool.send_message(f"👋 {agent_id} ({agent_type}) ready for coordination!")

        # If we have the actual agent instance, we can send progress updates
        if agent_instance:
            self._setup_agent_monitoring(agent_id, agent_instance, agent_tool)

        return agent_tool

    def _setup_agent_monitoring(
        self, agent_id: str, agent_instance, agent_tool: GroupChatTool
    ):
        """Setup monitoring for individual agent"""

        def monitor_agent():
            last_status = None
            while self.monitoring and agent_id in self.live_agents:
                try:
                    # Check agent status (this would depend on agent implementation)
                    current_status = getattr(agent_instance, "status", "working")

                    if current_status != last_status:
                        if current_status == "thinking":
                            agent_tool.send_message("🤔 Analyzing task...")
                        elif current_status == "researching":
                            agent_tool.send_message("🔍 Gathering information...")
                        elif current_status == "writing":
                            agent_tool.send_message("✍️ Generating output...")

                    last_status = current_status
                    time.sleep(10)  # Check every 10 seconds

                except Exception:
                    break

        monitor_thread = threading.Thread(target=monitor_agent, daemon=True)
        monitor_thread.start()

    def handle_human_message(self, content: str) -> str:
        """Handle message from human user to orchestrator"""
        # Add human message to chat
        human_tool = GroupChatTool(
            chat_manager=self.chat_manager, agent_id="human", agent_type="user"
        )
        human_tool.send_message(content)

        # Process command if it looks like one
        response = self._process_orchestrator_command(content)

        if response:
            self.orchestrator_tool.send_message(response)
            return response

        return "Message received - orchestrator continuing work..."

    def _process_orchestrator_command(self, content: str) -> Optional[str]:
        """Process commands directed at orchestrator"""
        content_lower = content.lower().strip()

        if "status" in content_lower or "progress" in content_lower:
            return self._get_orchestrator_status()
        elif "pause" in content_lower:
            return self._pause_orchestrator()
        elif "resume" in content_lower:
            return self._resume_orchestrator()
        elif "agents" in content_lower:
            return self._list_active_agents()
        elif "tasks" in content_lower:
            return self._list_task_status()
        elif content_lower.startswith("priority"):
            return self._handle_priority_change(content)

        return None

    def _get_orchestrator_status(self) -> str:
        """Get current orchestrator status"""
        if hasattr(self.orchestrator, "metrics"):
            metrics = self.orchestrator.metrics
            total = metrics.get("total", 0)
            completed = metrics.get("completed", 0)
            failed = metrics.get("failed", 0)
            running = metrics.get("running", 0)

            return (
                f"📊 Orchestrator Status:\n"
                f"  ✅ Completed: {completed}/{total}\n"
                f"  🚀 Running: {running}\n"
                f"  ❌ Failed: {failed}\n"
                f"  💬 Live agents: {len(self.live_agents)}"
            )

        return "📊 Orchestrator active - metrics unavailable"

    def _list_active_agents(self) -> str:
        """List all active agents in chat"""
        agents = list(self.chat_manager.agents.keys())
        if not agents:
            return "No active agents in chat"

        agent_list = []
        for agent_id in agents:
            agent = self.chat_manager.agents[agent_id]
            status = "🟢" if time.time() - agent.last_seen < 60 else "🟡"
            agent_list.append(f"  {status} {agent_id} ({agent.agent_type})")

        return "🤖 Active agents:\n" + "\n".join(agent_list)

    def _list_task_status(self) -> str:
        """List current task status"""
        if not hasattr(self.orchestrator, "tasks"):
            return "No task information available"

        status_summary = {}
        for task in self.orchestrator.tasks:
            status = getattr(task, "status", "unknown")
            status_summary[status] = status_summary.get(status, 0) + 1

        summary_lines = [
            f"  {status}: {count}" for status, count in status_summary.items()
        ]
        return "📋 Task Status:\n" + "\n".join(summary_lines)

    def _pause_orchestrator(self) -> str:
        """Pause orchestrator execution"""
        # This would depend on orchestrator implementation
        return "⏸️ Orchestrator paused (feature in development)"

    def _resume_orchestrator(self) -> str:
        """Resume orchestrator execution"""
        return "▶️ Orchestrator resumed (feature in development)"

    def _handle_priority_change(self, content: str) -> str:
        """Handle priority change requests"""
        return "🔧 Priority changes not yet implemented"

    def get_chat_context_for_agent(self, agent_id: str) -> Dict:
        """Get chat context optimized for specific agent"""
        return self.chat_manager.get_context_for_agent(agent_id)

    def start_web_interface(self, port: int = 8765):
        """Start web interface for group chat"""
        self.chat_manager.start_websocket_server(port)
        print(f"🌐 Group chat web interface: http://localhost:{port}")

    def shutdown(self):
        """Shutdown live chat monitoring"""
        self.monitoring = False
        self.orchestrator_tool.send_message("🛑 Orchestrator chat shutting down...")


# Integration with existing orchestrator
def add_live_chat_to_orchestrator(orchestrator, chat_id: str = None):
    """Add live chat capabilities to existing orchestrator"""
    live_chat = LiveOrchestratorChat(
        orchestrator, GroupChatManager(chat_id) if chat_id else None
    )

    # Hook into orchestrator events if possible
    if hasattr(orchestrator, "on_task_start"):
        original_on_task_start = orchestrator.on_task_start

        def enhanced_on_task_start(task):
            live_chat.orchestrator_tool.send_message(
                f"🚀 Starting {task.task_id} ({getattr(task, 'task_type', 'unknown')})"
            )
            if original_on_task_start:
                return original_on_task_start(task)

        orchestrator.on_task_start = enhanced_on_task_start

    if hasattr(orchestrator, "on_task_complete"):
        original_on_task_complete = orchestrator.on_task_complete

        def enhanced_on_task_complete(task, result):
            duration = getattr(task, "duration", 0)
            live_chat.orchestrator_tool.send_message(
                f"✅ {task.task_id} completed in {duration:.1f}s"
            )
            if original_on_task_complete:
                return original_on_task_complete(task, result)

        orchestrator.on_task_complete = enhanced_on_task_complete

    return live_chat

"""
Main HECATON Orchestrator
Coordinates parallel agent execution using Send API
"""

import asyncio
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..agents import AgentRegistry
from ..agents.specialized import CodeAgent, ResearchAgent, TestAgent

# Import Phase 2 components
from ..messaging.message_broker import Message, MessageBroker
from ..monitoring.performance_monitor import PerformanceMonitor

logger = logging.getLogger(__name__)


@dataclass
class HecatonConfig:
    """Configuration for HECATON orchestrator"""

    max_parallel_agents: int = 15
    token_pool_size: int = 15
    worktree_base: Path = Path("/home/opsvi/hecaton_worktrees")
    enable_monitoring: bool = True
    enable_checkpointing: bool = True


class HecatonOrchestrator:
    """
    Main orchestrator for HECATON multi-agent system.
    Phase 0: Minimal implementation for 2-agent parallel execution.
    """

    def __init__(self, config: Optional[HecatonConfig] = None):
        self.config = config or HecatonConfig()

        # Initialize Phase 2 components
        self.message_broker = MessageBroker()
        self.registry = AgentRegistry()
        self.performance_monitor = PerformanceMonitor()

        # These will be properly initialized in later phases
        self.send_api = None  # SendAPIOrchestrator()
        self.token_pool = None  # TokenPool(size=self.config.token_pool_size)
        self.worktree_manager = None  # WorktreeManager(base_path=self.config.worktree_base)

        # Register specialized agent types
        self._register_agent_types()

        logger.info(
            "HECATON initialized with Phase 2 components",
            max_agents=self.config.max_parallel_agents,
            tokens=self.config.token_pool_size,
            monitoring=self.config.enable_monitoring,
        )

    async def execute_parallel(self, tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Execute tasks in parallel using Send API.

        Args:
            tasks: List of task definitions

        Returns:
            Execution results from all agents
        """
        logger.info(f"Starting parallel execution of {len(tasks)} tasks")

        # Phase 0: Simple parallel execution
        # This will be enhanced in Phase 1 with the agents themselves

        results = await self.send_api.execute(tasks)

        logger.info("Parallel execution completed", task_count=len(tasks))
        return results

    async def bootstrap_phase_1(self):
        """
        Use the 2-agent system to build 5-agent capability.
        This method will be called once Phase 0 is working.
        """
        logger.info("Starting Phase 1 bootstrap sequence")

        tasks = [
            {"id": "expand_tokens", "prompt": "Expand token pool to support 5 tokens"},
            {"id": "enhance_orchestrator", "prompt": "Add error handling and retry logic"},
        ]

        results = await self.execute_parallel(tasks)
        logger.info("Phase 1 bootstrap completed")
        return results

    def _register_agent_types(self):
        """Register all specialized agent types with the registry."""
        self.registry.register_agent_type("code", CodeAgent)
        self.registry.register_agent_type("research", ResearchAgent)
        self.registry.register_agent_type("test", TestAgent)
        logger.info("Registered specialized agent types: code, research, test")

    def register_specialized_agents(self) -> Dict[str, Any]:
        """Create and register specialized agents for Phase 2.

        Returns:
            Dictionary of created agent IDs by type
        """
        agents_created = {}

        # Create code agents
        code_agents = []
        for i in range(2):
            agent = self.registry.create_agent("code", f"CodeAgent_{i+1}")
            code_agents.append(agent.id)
        agents_created["code"] = code_agents

        # Create research agents
        research_agents = []
        for i in range(2):
            agent = self.registry.create_agent("research", f"ResearchAgent_{i+1}")
            research_agents.append(agent.id)
        agents_created["research"] = research_agents

        # Create test agent
        test_agent = self.registry.create_agent("test", "TestAgent_1")
        agents_created["test"] = [test_agent.id]

        logger.info(
            "Specialized agents registered",
            code_agents=len(code_agents),
            research_agents=len(research_agents),
            test_agents=1,
        )

        return agents_created

    async def start_message_broker(self):
        """Start the message broker for inter-agent communication."""
        await self.message_broker.start()
        logger.info("Message broker started")

    async def stop_message_broker(self):
        """Stop the message broker."""
        await self.message_broker.stop()
        logger.info("Message broker stopped")

    async def broadcast_message(self, topic: str, payload: Any, sender: str = "orchestrator"):
        """Broadcast a message to all agents subscribed to a topic.

        Args:
            topic: Topic to broadcast on
            payload: Message payload
            sender: Sender identifier
        """
        message = Message(sender=sender, topic=topic, payload=payload)
        await self.message_broker.publish(topic, message)
        logger.debug(f"Broadcast message to topic '{topic}'")

    async def execute_with_monitoring(self, tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Execute tasks with performance monitoring.

        Args:
            tasks: List of task definitions

        Returns:
            Execution results with performance metrics
        """
        results = {}

        if self.config.enable_monitoring:
            # Track each task
            for task in tasks:
                task_id = task.get("id", f"task_{len(results)}")
                self.performance_monitor.start_tracking(task_id)

        try:
            # Execute tasks (simulated for Phase 2)
            for task in tasks:
                task_id = task.get("id", f"task_{len(results)}")

                # Get appropriate agent based on task type
                task_type = task.get("type", "general")
                agents = self.registry.get_agents_by_type(task_type)

                if agents:
                    agent = agents[0]  # Use first available agent
                    result = agent.execute(task)
                else:
                    result = {"status": "no_agent_available", "task_id": task_id}

                results[task_id] = result

                if self.config.enable_monitoring:
                    self.performance_monitor.end_tracking(
                        task_id, success=result.get("status") == "success"
                    )

        except Exception as e:
            logger.error(f"Error during task execution: {e}")

        # Add performance metrics to results
        if self.config.enable_monitoring:
            results["_metrics"] = self.performance_monitor.calculate_statistics()

        return results

    def get_agent_status(self) -> Dict[str, Any]:
        """Get status of all registered agents.

        Returns:
            Dictionary with agent status information
        """
        return {
            "registered_agents": self.registry.list_agents(),
            "agent_types": {
                "code": len(self.registry.get_agents_by_type("code")),
                "research": len(self.registry.get_agents_by_type("research")),
                "test": len(self.registry.get_agents_by_type("test")),
            },
            "message_broker_running": self.message_broker._running
            if self.message_broker
            else False,
            "performance_metrics": self.performance_monitor.calculate_statistics()
            if self.config.enable_monitoring
            else None,
        }

    def export_metrics(self, filepath: Optional[str] = None) -> str:
        """Export performance metrics.

        Args:
            filepath: Optional path to save metrics

        Returns:
            JSON string of metrics
        """
        if not self.config.enable_monitoring:
            return '{"error": "Monitoring is disabled"}'

        return self.performance_monitor.export_metrics(filepath)

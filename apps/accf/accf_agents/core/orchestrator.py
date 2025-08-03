"""
Agent orchestrator for managing workflow execution.

This module provides the main orchestration logic for the ACCF Research Agent system,
handling task distribution, agent coordination, and workflow management.
"""

import asyncio
import time
from typing import Dict, List, Optional, Any
from .settings import Settings
from ..agents.base import Task, Result, BaseAgent
import logging


class AgentOrchestrator:
    """Main orchestrator for agent workflow execution."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.logger = logging.getLogger("orchestrator")
        self.agents: Dict[str, BaseAgent] = {}
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize the orchestrator and all agents."""
        if self._initialized:
            return

        self.logger.info("Initializing AgentOrchestrator")

        # Discover and initialize agents
        await self._discover_agents()
        await self._initialize_agents()

        self._initialized = True
        self.logger.info(f"Orchestrator initialized with {len(self.agents)} agents")

    async def _discover_agents(self) -> None:
        """Discover available agents from the accf_agents.agents module."""
        try:
            # Import the agents module to discover available agents
            from ..agents import (
                ConsultAgent,
                KnowledgeAgent,
            )

            # Register the core agents (focusing on consult and knowledge as requested)
            agent_classes = [
                ("consult", ConsultAgent),
                ("knowledge", KnowledgeAgent),
            ]

            for agent_name, agent_class in agent_classes:
                try:
                    agent = agent_class(agent_name, self.settings)
                    self.agents[agent_name] = agent
                    self.logger.info(f"Registered agent: {agent_name}")
                except Exception as e:
                    self.logger.error(f"Failed to register agent {agent_name}: {e}")

        except Exception as e:
            self.logger.error(f"Error discovering agents: {e}")

    async def _initialize_agents(self) -> None:
        """Initialize all discovered agents."""
        for agent_name, agent in self.agents.items():
            try:
                await agent.initialize()
                self.logger.info(f"Initialized agent: {agent_name}")
            except Exception as e:
                self.logger.error(f"Failed to initialize agent {agent_name}: {e}")

    async def execute_workflow(self, task: Task) -> Result:
        """Execute a workflow task using the appropriate agent."""
        if not self._initialized:
            await self.initialize()

        start_time = time.time()

        try:
            # Find the appropriate agent for this task
            agent = self._find_agent_for_task(task.type)
            if not agent:
                return Result(
                    task_id=task.id,
                    status="error",
                    data={},
                    error_message=f"No agent found for task type: {task.type}",
                )

            # Execute the task
            result = await agent.execute(task)
            result.execution_time = time.time() - start_time

            self.logger.info(
                f"Task {task.id} completed in {result.execution_time:.2f}s"
            )
            return result

        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error(f"Error executing task {task.id}: {e}")

            return Result(
                task_id=task.id,
                status="error",
                data={},
                error_message=str(e),
                execution_time=execution_time,
            )

    def _find_agent_for_task(self, task_type: str) -> Optional[BaseAgent]:
        """Find the appropriate agent for a given task type."""
        for agent in self.agents.values():
            if agent.can_handle(task_type):
                return agent
        return None

    async def execute_parallel_workflow(self, tasks: List[Task]) -> List[Result]:
        """Execute multiple tasks in parallel."""
        if not self._initialized:
            await self.initialize()

        # Group tasks by agent to optimize execution
        task_groups: Dict[str, List[Task]] = {}
        for task in tasks:
            agent = self._find_agent_for_task(task.type)
            if agent:
                agent_name = agent.name
                if agent_name not in task_groups:
                    task_groups[agent_name] = []
                task_groups[agent_name].append(task)

        # Execute tasks in parallel
        results = []
        for agent_name, agent_tasks in task_groups.items():
            agent = self.agents[agent_name]
            agent_results = await asyncio.gather(
                *[agent.execute(task) for task in agent_tasks], return_exceptions=True
            )
            results.extend(agent_results)

        return results

    def get_agent_status(self) -> Dict[str, Any]:
        """Get status information for all agents."""
        return {
            "total_agents": len(self.agents),
            "agents": {
                name: {
                    "initialized": agent._initialized,
                    "capabilities": agent.get_capabilities(),
                }
                for name, agent in self.agents.items()
            },
        }

    async def shutdown(self) -> None:
        """Shutdown the orchestrator and all agents."""
        self.logger.info("Shutting down AgentOrchestrator")
        # Add any cleanup logic here
        self._initialized = False

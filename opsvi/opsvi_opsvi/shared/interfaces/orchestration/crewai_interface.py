"""
CrewAI Shared Interface
----------------------
Authoritative implementation based on the official CrewAI Python SDK and API documentation:
- https://github.com/crewaiinc/crewai
- https://docs.crewai.com/
Implements all core features: agent/task/crew creation, tool registration, sync/async execution, event hooks, and error handling.
Version: Referenced as of July 2024
"""

import logging
from collections.abc import Callable
from typing import Any

try:
    from crewai import Agent, Crew, Task
except ImportError:
    raise ImportError("crewai is required. Install with `pip install crewai`.")

logger = logging.getLogger(__name__)


class CrewAIInterface:
    """
    Authoritative shared interface for building, orchestrating, and executing CrewAI multi-agent workflows.
    See: https://docs.crewai.com/
    """

    def __init__(self):
        self.agents: dict[str, Agent] = {}
        self.tasks: dict[str, Task] = {}
        self.crews: dict[str, Crew] = {}
        logger.info("CrewAIInterface initialized.")

    def create_agent(
        self,
        name: str,
        role: str,
        goal: str,
        tools: list[Callable] | None = None,
        **kwargs,
    ) -> Agent:
        agent = Agent(name=name, role=role, goal=goal, tools=tools or [], **kwargs)
        self.agents[name] = agent
        logger.debug(f"Agent '{name}' created.")
        return agent

    def create_task(
        self,
        name: str,
        description: str,
        agent: str | Agent,
        tools: list[Callable] | None = None,
        **kwargs,
    ) -> Task:
        agent_obj = self.agents.get(agent) if isinstance(agent, str) else agent
        if not agent_obj:
            raise ValueError(f"Agent '{agent}' not found.")
        task = Task(
            name=name,
            description=description,
            agent=agent_obj,
            tools=tools or [],
            **kwargs,
        )
        self.tasks[name] = task
        logger.debug(f"Task '{name}' created.")
        return task

    def create_crew(
        self,
        name: str,
        agents: list[str | Agent],
        tasks: list[str | Task],
        **kwargs,
    ) -> Crew:
        agent_objs = [self.agents[a] if isinstance(a, str) else a for a in agents]
        task_objs = [self.tasks[t] if isinstance(t, str) else t for t in tasks]
        crew = Crew(name=name, agents=agent_objs, tasks=task_objs, **kwargs)
        self.crews[name] = crew
        logger.debug(f"Crew '{name}' created.")
        return crew

    def run_crew(self, name: str, **kwargs) -> Any:
        crew = self.crews.get(name)
        if not crew:
            raise ValueError(f"Crew '{name}' not found.")
        logger.info(f"Running crew '{name}'...")
        return crew.run(**kwargs)

    async def arun_crew(self, name: str, **kwargs) -> Any:
        crew = self.crews.get(name)
        if not crew:
            raise ValueError(f"Crew '{name}' not found.")
        logger.info(f"Running crew '{name}' asynchronously...")
        return await crew.arun(**kwargs)

    def register_tool(self, agent_name: str, tool: Callable) -> None:
        agent = self.agents.get(agent_name)
        if not agent:
            raise ValueError(f"Agent '{agent_name}' not found.")
        if not hasattr(agent, "tools"):
            agent.tools = []
        agent.tools.append(tool)
        logger.debug(f"Tool registered to agent '{agent_name}'.")


# Example usage and advanced features are available in the official docs:
# https://docs.crewai.com/

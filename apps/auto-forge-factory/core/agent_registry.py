"""
Agent registry for the Auto-Forge factory.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Type
from uuid import UUID

from .agents.base_agent import BaseAgent
from .agents.planner_agent import PlannerAgent
from .agents.specifier_agent import SpecifierAgent
from .agents.architect_agent import ArchitectAgent
from .agents.coder_agent import CoderAgent
from .agents.tester_agent import TesterAgent
from .agents.performance_optimizer_agent import PerformanceOptimizerAgent
from .agents.security_validator_agent import SecurityValidatorAgent
from .agents.syntax_fixer_agent import SyntaxFixerAgent
from .agents.critic_agent import CriticAgent
from .agents.meta_orchestrator_agent import MetaOrchestratorAgent
from ..models.schemas import AgentType, AgentConfig, FactoryConfig


class AgentRegistry:
    """Registry for managing all agents in the Auto-Forge factory."""

    def __init__(self, config: FactoryConfig):
        """Initialize the agent registry.

        Args:
            config: Factory configuration
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        self._agents: Dict[AgentType, Type[BaseAgent]] = {}
        self._agent_instances: Dict[UUID, BaseAgent] = {}
        self._register_default_agents()

    def _register_default_agents(self):
        """Register the default set of agents."""
        self.register_agent(AgentType.PLANNER, PlannerAgent)
        self.register_agent(AgentType.SPECIFIER, SpecifierAgent)
        self.register_agent(AgentType.ARCHITECT, ArchitectAgent)
        self.register_agent(AgentType.CODER, CoderAgent)
        self.register_agent(AgentType.TESTER, TesterAgent)
        self.register_agent(AgentType.PERFORMANCE_OPTIMIZER, PerformanceOptimizerAgent)
        self.register_agent(AgentType.SECURITY_VALIDATOR, SecurityValidatorAgent)
        self.register_agent(AgentType.SYNTAX_FIXER, SyntaxFixerAgent)
        self.register_agent(AgentType.CRITIC, CriticAgent)
        self.register_agent(AgentType.META_ORCHESTRATOR, MetaOrchestratorAgent)

        self.logger.info(f"Registered {len(self._agents)} default agents")

    def register_agent(self, agent_type: AgentType, agent_class: Type[BaseAgent]):
        """Register an agent class for a specific type.

        Args:
            agent_type: The agent type
            agent_class: The agent class to register
        """
        self._agents[agent_type] = agent_class
        self.logger.debug(
            f"Registered agent {agent_type.value}: {agent_class.__name__}"
        )

    def get_agent_class(self, agent_type: AgentType) -> Optional[Type[BaseAgent]]:
        """Get the agent class for a specific type.

        Args:
            agent_type: The agent type

        Returns:
            Agent class if registered, None otherwise
        """
        return self._agents.get(agent_type)

    def create_agent_instance(
        self,
        agent_type: AgentType,
        job_id: UUID,
        agent_config: Optional[AgentConfig] = None,
        **kwargs,
    ) -> BaseAgent:
        """Create an agent instance for a specific job.

        Args:
            agent_type: The agent type
            job_id: The job ID this agent will work on
            agent_config: Optional agent-specific configuration
            **kwargs: Additional arguments for the agent

        Returns:
            Agent instance

        Raises:
            ValueError: If agent type is not registered
        """
        agent_class = self.get_agent_class(agent_type)
        if not agent_class:
            raise ValueError(f"No agent registered for type: {agent_type.value}")

        # Use default config if not provided
        if agent_config is None:
            agent_config = self.config.agent_configs.get(agent_type)

        # Create agent instance
        agent = agent_class(
            agent_type=agent_type, job_id=job_id, config=agent_config, **kwargs
        )

        # Store instance
        instance_id = UUID(f"{job_id}-{agent_type.value}")
        self._agent_instances[instance_id] = agent

        self.logger.info(f"Created agent instance {agent_type.value} for job {job_id}")
        return agent

    def get_agent_instance(
        self, job_id: UUID, agent_type: AgentType
    ) -> Optional[BaseAgent]:
        """Get an existing agent instance.

        Args:
            job_id: The job ID
            agent_type: The agent type

        Returns:
            Agent instance if exists, None otherwise
        """
        instance_id = UUID(f"{job_id}-{agent_type.value}")
        return self._agent_instances.get(instance_id)

    def remove_agent_instance(self, job_id: UUID, agent_type: AgentType):
        """Remove an agent instance.

        Args:
            job_id: The job ID
            agent_type: The agent type
        """
        instance_id = UUID(f"{job_id}-{agent_type.value}")
        if instance_id in self._agent_instances:
            del self._agent_instances[instance_id]
            self.logger.debug(
                f"Removed agent instance {agent_type.value} for job {job_id}"
            )

    def list_registered_agents(self) -> List[AgentType]:
        """List all registered agent types.

        Returns:
            List of registered agent types
        """
        return list(self._agents.keys())

    def list_active_instances(self) -> List[Dict[str, Any]]:
        """List all active agent instances.

        Returns:
            List of active instance information
        """
        instances = []
        for instance_id, agent in self._agent_instances.items():
            instances.append(
                {
                    "instance_id": str(instance_id),
                    "agent_type": agent.agent_type.value,
                    "job_id": str(agent.job_id),
                    "status": (
                        agent.status.value if hasattr(agent, "status") else "unknown"
                    ),
                }
            )
        return instances

    def get_agent_config(self, agent_type: AgentType) -> Optional[AgentConfig]:
        """Get configuration for an agent type.

        Args:
            agent_type: The agent type

        Returns:
            Agent configuration if exists, None otherwise
        """
        return self.config.agent_configs.get(agent_type)

    def update_agent_config(self, agent_type: AgentType, config: AgentConfig):
        """Update configuration for an agent type.

        Args:
            agent_type: The agent type
            config: New configuration
        """
        self.config.agent_configs[agent_type] = config
        self.logger.info(f"Updated configuration for agent {agent_type.value}")

    async def cleanup_job_agents(self, job_id: UUID):
        """Clean up all agents for a specific job.

        Args:
            job_id: The job ID
        """
        agents_to_remove = []
        for instance_id, agent in self._agent_instances.items():
            if agent.job_id == job_id:
                agents_to_remove.append(instance_id)

        for instance_id in agents_to_remove:
            agent = self._agent_instances[instance_id]
            # Cleanup agent resources
            if hasattr(agent, "cleanup"):
                await agent.cleanup()
            del self._agent_instances[instance_id]

        self.logger.info(f"Cleaned up {len(agents_to_remove)} agents for job {job_id}")

    def get_agent_status(self, agent_type: AgentType) -> str:
        """Get status of an agent type.

        Args:
            agent_type: The agent type

        Returns:
            Status string
        """
        if agent_type in self._agents:
            config = self.get_agent_config(agent_type)
            if config and config.enabled:
                return "enabled"
            elif config:
                return "disabled"
            else:
                return "configured"
        return "not_registered"

    def get_factory_status(self) -> Dict[str, Any]:
        """Get overall factory status.

        Returns:
            Factory status information
        """
        return {
            "total_registered_agents": len(self._agents),
            "total_active_instances": len(self._agent_instances),
            "agent_statuses": {
                agent_type.value: self.get_agent_status(agent_type)
                for agent_type in AgentType
            },
            "active_instances": self.list_active_instances(),
        }

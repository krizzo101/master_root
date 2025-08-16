"""Agent module for the autonomous software factory."""

from opsvi_auto_forge.agents.architect_agent import ArchitectAgent
from opsvi_auto_forge.agents.base_agent import AgentResponse, BaseAgent
from opsvi_auto_forge.agents.coder_agent import CoderAgent
from opsvi_auto_forge.agents.perf_opt_agent import PerfOptAgent
from opsvi_auto_forge.agents.perf_smoke_agent import PerfSmokeAgent
from opsvi_auto_forge.agents.planner_agent import PlannerAgent
from opsvi_auto_forge.agents.specifier_agent import SpecifierAgent
from opsvi_auto_forge.agents.tester_agent import TesterAgent

__all__ = [
    "BaseAgent",
    "AgentResponse",
    "PlannerAgent",
    "SpecifierAgent",
    "ArchitectAgent",
    "CoderAgent",
    "TesterAgent",
    "PerfSmokeAgent",
    "PerfOptAgent",
]


class AgentRegistry:
    """Registry for managing all available agents."""

    def __init__(self):
        """Initialize the agent registry."""
        self._agents = {}
        self._repair_agents = {}
        self._register_default_agents()

    def _register_default_agents(self):
        """Register the default set of agents."""
        from opsvi_auto_forge.config.models import AgentRole

        # Register core agents
        self.register_agent(AgentRole.PLANNER, PlannerAgent)
        self.register_agent(AgentRole.SPECIFIER, SpecifierAgent)
        self.register_agent(AgentRole.ARCHITECT, ArchitectAgent)
        self.register_agent(AgentRole.CODER, CoderAgent)
        self.register_agent(AgentRole.TESTER, TesterAgent)

        # Register performance agents
        self.register_agent(AgentRole.PERF_SMOKE, PerfSmokeAgent)
        self.register_agent(AgentRole.PERF_OPT, PerfOptAgent)

        # Register repair agents (lazy import to avoid circular dependencies)
        self._register_repair_agents()

    def register_agent(self, role, agent_class):
        """Register an agent class for a specific role.

        Args:
            role: The agent role
            agent_class: The agent class to register
        """
        self._agents[role] = agent_class

    def get_agent(self, role, **kwargs):
        """Get an agent instance for the specified role.

        Args:
            role: The agent role
            **kwargs: Additional arguments to pass to the agent constructor

        Returns:
            Agent instance

        Raises:
            KeyError: If no agent is registered for the role
        """
        if role not in self._agents:
            raise KeyError(f"No agent registered for role: {role}")

        agent_class = self._agents[role]
        return agent_class(**kwargs)

    def list_agents(self):
        """List all registered agents.

        Returns:
            List of registered agent roles
        """
        return list(self._agents.keys())

    def has_agent(self, role):
        """Check if an agent is registered for the role.

        Args:
            role: The agent role to check

        Returns:
            True if an agent is registered for the role
        """
        return role in self._agents

    def register_repair_agent(self, name: str, agent_class):
        """Register a repair agent.

        Args:
            name: The repair agent name
            agent_class: The repair agent class to register
        """
        self._repair_agents[name] = agent_class

    def get_repair_agent(self, name: str, **kwargs):
        """Get a repair agent instance by name.

        Args:
            name: The repair agent name
            **kwargs: Additional arguments to pass to the agent constructor

        Returns:
            Repair agent instance

        Raises:
            KeyError: If no repair agent is registered with the name
        """
        if name not in self._repair_agents:
            raise KeyError(f"No repair agent registered with name: {name}")

        agent_class = self._repair_agents[name]
        return agent_class(**kwargs)

    def get_all_repair_agents(self, **kwargs):
        """Get all registered repair agents.

        Args:
            **kwargs: Additional arguments to pass to agent constructors

        Returns:
            List of repair agent instances
        """
        return [agent_class(**kwargs) for agent_class in self._repair_agents.values()]

    def list_repair_agents(self):
        """List all registered repair agents.

        Returns:
            List of registered repair agent names
        """
        return list(self._repair_agents.keys())

    def has_repair_agent(self, name: str):
        """Check if a repair agent is registered with the name.

        Args:
            name: The repair agent name to check

        Returns:
            True if a repair agent is registered with the name
        """
        return name in self._repair_agents

    def _register_repair_agents(self):
        """Register repair agents with lazy imports."""
        try:
            from opsvi_auto_forge.agents.syntax_fixer import SyntaxFixer
            from opsvi_auto_forge.agents.security_validator import SecurityValidator

            self.register_repair_agent("syntax_fixer", SyntaxFixer)
            self.register_repair_agent("security_validator", SecurityValidator)
        except ImportError as e:
            # Log the error but don't fail - repair agents are optional
            import logging

            logger = logging.getLogger(__name__)
            logger.warning(f"Could not register repair agents: {e}")


# Create a global instance
agent_registry = AgentRegistry()

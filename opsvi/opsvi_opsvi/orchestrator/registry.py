"""Agent registry for dynamic loading of AI agents."""

import importlib
import inspect
import logging
from collections.abc import Callable
from typing import Any

logger = logging.getLogger(__name__)


class AgentRegistry:
    """Registry for managing AI agents with dynamic loading."""

    def __init__(self) -> None:
        """Initialize the agent registry."""
        self._agents: dict[str, Callable] = {}
        self._agent_configs: dict[str, dict[str, Any]] = {}
        self._agent_metadata: dict[str, dict[str, Any]] = {}

    def register_agent(
        self,
        name: str,
        agent_func: Callable,
        config: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Register an agent function."""
        self._agents[name] = agent_func
        self._agent_configs[name] = config or {}
        self._agent_metadata[name] = metadata or {}
        logger.info(f"Registered agent: {name}")

    def register_agent_from_path(
        self,
        name: str,
        dotted_path: str,
        config: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Register an agent from a dotted import path."""
        try:
            # Parse the dotted path
            module_path, func_name = dotted_path.rsplit(".", 1)

            # Import the module
            module = importlib.import_module(module_path)

            # Get the function
            agent_func = getattr(module, func_name)

            # Register the agent
            self.register_agent(name, agent_func, config, metadata)

        except (ImportError, AttributeError) as e:
            logger.error(f"Failed to load agent from path {dotted_path}: {e}")
            raise

    def get_agent(self, name: str) -> Callable | None:
        """Get an agent by name."""
        return self._agents.get(name)

    def get_agent_config(self, name: str) -> dict[str, Any]:
        """Get configuration for an agent."""
        return self._agent_configs.get(name, {})

    def get_agent_metadata(self, name: str) -> dict[str, Any]:
        """Get metadata for an agent."""
        return self._agent_metadata.get(name, {})

    def list_agents(self) -> list[str]:
        """List all registered agent names."""
        return list(self._agents.keys())

    def has_agent(self, name: str) -> bool:
        """Check if an agent is registered."""
        return name in self._agents

    def execute_agent(
        self,
        name: str,
        input_data: dict[str, Any],
        config: dict[str, Any] | None = None,
    ) -> Any:
        """Execute an agent with input data."""
        if not self.has_agent(name):
            raise ValueError(f"Agent '{name}' not found in registry")

        agent_func = self.get_agent(name)
        agent_config = self.get_agent_config(name)

        # Merge configurations
        if config:
            agent_config = {**agent_config, **config}

        # Check if agent is async
        if inspect.iscoroutinefunction(agent_func):
            logger.warning(f"Agent {name} is async but called synchronously")

        try:
            # Execute the agent
            result = agent_func(input_data, **agent_config)
            logger.info(f"Successfully executed agent: {name}")
            return result

        except Exception as e:
            logger.error(f"Failed to execute agent {name}: {e}")
            raise

    async def execute_agent_async(
        self,
        name: str,
        input_data: dict[str, Any],
        config: dict[str, Any] | None = None,
    ) -> Any:
        """Execute an agent asynchronously."""
        if not self.has_agent(name):
            raise ValueError(f"Agent '{name}' not found in registry")

        agent_func = self.get_agent(name)
        agent_config = self.get_agent_config(name)

        # Merge configurations
        if config:
            agent_config = {**agent_config, **config}

        try:
            # Execute the agent
            if inspect.iscoroutinefunction(agent_func):
                result = await agent_func(input_data, **agent_config)
            else:
                result = agent_func(input_data, **agent_config)

            logger.info(f"Successfully executed agent: {name}")
            return result

        except Exception as e:
            logger.error(f"Failed to execute agent {name}: {e}")
            raise

    def get_agent_signature(self, name: str) -> inspect.Signature | None:
        """Get the signature of an agent function."""
        if not self.has_agent(name):
            return None

        agent_func = self.get_agent(name)
        return inspect.signature(agent_func)

    def validate_agent_input(self, name: str, input_data: dict[str, Any]) -> bool:
        """Validate input data against agent signature."""
        signature = self.get_agent_signature(name)
        if not signature:
            return False

        try:
            # This is a basic validation - in practice you might want more sophisticated validation
            signature.bind(input_data)
            return True
        except TypeError:
            return False


# Global registry instance
registry = AgentRegistry()


def register_default_agents() -> None:
    """Register default agents from the code_gen application."""
    try:
        # Register agents from the existing code_gen application
        registry.register_agent_from_path(
            "plan_agent",
            "src.applications.code_gen.ai_agents.extract_requirements_with_ai",
            metadata={
                "type": "plan",
                "description": "Extract requirements from user request",
            },
        )

        registry.register_agent_from_path(
            "spec_agent",
            "src.applications.code_gen.ai_agents.generate_architecture_with_ai",
            metadata={
                "type": "spec",
                "description": "Generate architecture specification",
            },
        )

        registry.register_agent_from_path(
            "code_agent",
            "src.applications.code_gen.ai_code_generator.generate_code",
            metadata={
                "type": "code",
                "description": "Generate code from specification",
            },
        )

        registry.register_agent_from_path(
            "test_agent",
            "src.applications.code_gen.ai_test_generator.generate_tests",
            metadata={"type": "test", "description": "Generate tests for code"},
        )

        registry.register_agent_from_path(
            "doc_agent",
            "src.applications.code_gen.ai_documentation_generator.generate_documentation",
            metadata={"type": "document", "description": "Generate documentation"},
        )

        registry.register_agent_from_path(
            "research_agent",
            "src.applications.code_gen.ai_agents.extract_research_topics_with_ai",
            metadata={"type": "research", "description": "Extract research topics"},
        )

        logger.info("Registered default agents")

    except Exception as e:
        logger.warning(f"Failed to register some default agents: {e}")


# Auto-register default agents on import
register_default_agents()

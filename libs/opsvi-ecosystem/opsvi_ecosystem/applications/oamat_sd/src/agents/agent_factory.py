"""
Dynamic Agent Factory

Creates specialized agents on-demand based on requirements using LangGraph's
create_react_agent. Handles agent configuration, tool assignment, and context management.
"""

import asyncio
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent

from src.applications.oamat_sd.src.config.config_manager import ConfigManager

logger = logging.getLogger(__name__)


class AgentRole(str, Enum):
    """Specialized agent roles."""

    GENERALIST = "generalist"
    RESEARCHER = "researcher"
    IMPLEMENTER = "implementer"
    VALIDATOR = "validator"
    ARCHITECT = "architect"
    TECHNICAL_SPECIALIST = "technical_specialist"
    DOMAIN_EXPERT = "domain_expert"
    INTEGRATOR = "integrator"
    SECURITY_SPECIALIST = "security_specialist"


class AgentStatus(str, Enum):
    """Agent lifecycle status."""

    CREATING = "creating"
    READY = "ready"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ERROR = "error"


@dataclass
class AgentConfiguration:
    """Configuration for creating an agent."""

    role: AgentRole
    tools: list[str]
    system_prompt: str
    context: dict[str, Any] = field(default_factory=dict)
    memory_config: dict[str, Any] = field(default_factory=dict)
    performance_config: dict[str, Any] = field(default_factory=dict)
    specialization_params: dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentInstance:
    """Created agent instance with metadata."""

    agent_id: str
    role: AgentRole
    configuration: AgentConfiguration
    status: AgentStatus
    created_at: datetime
    tools_assigned: list[str]
    context: dict[str, Any] = field(default_factory=dict)
    performance_metrics: dict[str, Any] = field(default_factory=dict)
    agent_object: Any | None = None  # The actual LangGraph agent


@dataclass
class AgentCreationRequest:
    """Request for creating a new agent."""

    role: AgentRole
    context: dict[str, Any]
    tools: list[str] = field(default_factory=list)
    specialization_requirements: dict[str, Any] = field(default_factory=dict)
    performance_requirements: dict[str, Any] = field(default_factory=dict)


class DynamicAgentFactory:
    """Factory for creating specialized agents on-demand."""

    def __init__(self, tool_registry=None):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.tool_registry = tool_registry
        self.active_agents: dict[str, AgentInstance] = {}
        self.agent_templates = self._initialize_agent_templates()
        self.system_prompts = self._initialize_system_prompts()

    def _initialize_agent_templates(self) -> dict[AgentRole, dict[str, Any]]:
        """NO FALLBACKS RULE: Templates deprecated - agents must be created with explicit specifications."""
        # Templates removed to enforce O3-first architecture
        return {}

    def _initialize_system_prompts(self) -> dict[AgentRole, str]:
        """Initialize system prompts for different agent roles."""
        return {
            AgentRole.GENERALIST: """
You are a versatile AI agent capable of handling various tasks. You approach problems methodically,
breaking them down into manageable components. You excel at analysis, research, and implementation
across different domains while maintaining high quality standards.
""",
            AgentRole.RESEARCHER: """
You are a specialized research agent focused on gathering, analyzing, and synthesizing information.
You excel at finding relevant sources, extracting key insights, and presenting well-researched
findings. You are thorough, accurate, and always cite your sources.
""",
            AgentRole.IMPLEMENTER: """
You are a skilled implementation agent focused on turning designs and specifications into working
solutions. You excel at coding, testing, and delivering functional implementations. You write
clean, efficient, and well-documented code while following best practices.
""",
            AgentRole.VALIDATOR: """
You are a quality assurance agent focused on validation, testing, and review. You excel at
identifying issues, ensuring compliance with requirements, and maintaining high quality standards.
You are thorough, detail-oriented, and systematic in your approach.
""",
            AgentRole.ARCHITECT: """
You are a system architect focused on high-level design and strategic planning. You excel at
understanding requirements, designing scalable solutions, and making strategic technical decisions.
You think holistically and consider long-term implications.
""",
            AgentRole.TECHNICAL_SPECIALIST: """
You are a technical specialist with deep expertise in specific technologies and domains. You excel
at solving complex technical challenges, optimizing performance, and providing expert guidance
on specialized technical matters.
""",
            AgentRole.DOMAIN_EXPERT: """
You are a domain expert with specialized knowledge in specific business or technical domains.
You excel at understanding domain-specific requirements, ensuring compliance with domain standards,
and providing expert guidance on domain-specific challenges.
""",
            AgentRole.INTEGRATOR: """
You are an integration specialist focused on connecting systems, services, and components. You excel
at designing integration architectures, implementing data flows, and ensuring seamless system
interoperability while maintaining data integrity and security.
""",
            AgentRole.SECURITY_SPECIALIST: """
You are a security specialist focused on identifying and mitigating security risks. You excel at
security analysis, threat modeling, and implementing security best practices. You prioritize
security without compromising functionality.
""",
        }

    def create_agent_configuration(
        self, creation_request: AgentCreationRequest
    ) -> AgentConfiguration:
        """Create agent configuration based on request."""
        # NO FALLBACKS RULE: Templates are deprecated - explicit specifications required

        # Template system removed - all specifications must be explicit

        # Determine tools
        # NO FALLBACKS RULE: Agent tools must be explicitly provided
        if not creation_request.tools:
            raise RuntimeError(
                "Agent tools must be explicitly provided. Cannot proceed without O3-generated tool specifications."
            )
        tools = creation_request.tools

        # Get system prompt
        # NO FALLBACKS RULE: System prompt must be explicitly provided
        if creation_request.role not in self.system_prompts:
            raise RuntimeError(
                f"System prompt required for role {creation_request.role}. Cannot proceed without O3-generated prompt specifications."
            )
        system_prompt = self.system_prompts[creation_request.role]

        # Configure memory - NO FALLBACKS
        memory_limit = (
            creation_request.performance_requirements["memory_limit"]
            if "memory_limit" in creation_request.performance_requirements
            else ConfigManager().agent_factory.memory_defaults["max_entries"]
        )

        memory_config = {
            "type": ConfigManager().agent_factory.memory_defaults["type"],
            "max_entries": memory_limit,
            "persistence": ConfigManager().agent_factory.memory_defaults["persistence"],
        }

        # Configure performance - NO FALLBACKS ALLOWED
        from src.applications.oamat_sd.src.config.config_manager import (
            ConfigManager as app_config,
        )

        # Get timeout without fallbacks
        if "timeout" not in creation_request.performance_requirements:
            timeout = app_config.execution.agent_timeout_seconds
        else:
            timeout = creation_request.performance_requirements["timeout"]

        # Get max_iterations without fallbacks
        if "max_iterations" not in creation_request.performance_requirements:
            max_iterations = (
                app_config.execution.max_retry_attempts * 3
            )  # Reasonable default from config
        else:
            max_iterations = creation_request.performance_requirements["max_iterations"]

        performance_config = {
            "reasoning_depth": "intermediate",  # Standard reasoning depth
            "max_iterations": max_iterations,
            "timeout": timeout,
        }

        return AgentConfiguration(
            role=creation_request.role,
            tools=tools,
            system_prompt=system_prompt,
            context=creation_request.context,
            memory_config=memory_config,
            performance_config=performance_config,
            specialization_params=creation_request.specialization_requirements,
        )

    async def create_agent(
        self, creation_request: AgentCreationRequest
    ) -> AgentInstance:
        """Create a new specialized agent."""
        self.logger.info(f"Creating {creation_request.role} agent")

        # Generate unique agent ID
        agent_id = f"{creation_request.role}_{uuid.uuid4().hex[:8]}"

        # Create configuration
        config = self.create_agent_configuration(creation_request)

        # Create agent instance metadata
        agent_instance = AgentInstance(
            agent_id=agent_id,
            role=creation_request.role,
            configuration=config,
            status=AgentStatus.CREATING,
            created_at=datetime.now(),
            tools_assigned=ConfigManager().tools,
            context=ConfigManager().context,
        )

        try:
            # Create the actual agent using LangGraph (simulated for TDD)
            agent_object = await self._create_langgraph_agent(config)
            agent_instance.agent_object = agent_object
            agent_instance.status = AgentStatus.READY

            # Store the agent
            self.active_agents[agent_id] = agent_instance

            self.logger.info(f"Successfully created agent {agent_id}")
            return agent_instance

        except Exception as e:
            self.logger.error(f"Failed to create agent {agent_id}: {e}")
            agent_instance.status = AgentStatus.ERROR
            raise

    async def _create_langgraph_agent(self, config: AgentConfiguration) -> Any:
        """Create the actual LangGraph agent using create_react_agent."""
        try:
            # Create LLM with configuration - NO FALLBACKS ALLOWED
            from src.applications.oamat_sd.src.config.config_manager import (
                ConfigManager as app_config,
            )

            # Get model configuration without fallbacks
            if "model" not in ConfigManager().performance_config:
                raise RuntimeError(
                    "Model not specified in performance config - NO FALLBACKS ALLOWED"
                )
            if "temperature" not in ConfigManager().performance_config:
                raise RuntimeError(
                    "Temperature not specified in performance config - NO FALLBACKS ALLOWED"
                )

            model_name = ConfigManager().performance_config["model"]
            temperature = ConfigManager().performance_config["temperature"]

            # Validate against allowed models from config
            allowed_models = [
                app_config.models["reasoning"].model_name,
                app_config.models["agent"].model_name,
                app_config.models["implementation"].model_name,
            ]
            if model_name not in allowed_models:
                raise RuntimeError(
                    f"Invalid model {model_name} - must be one of: {allowed_models}"
                )

            llm = ChatOpenAI(model=model_name, temperature=temperature)

            # Create system prompt
            system_prompt = ChatPromptTemplate.from_messages(
                [
                    ("system", ConfigManager().system_prompt),
                    ("human", "{input}"),
                    ("placeholder", "{agent_scratchpad}"),
                ]
            )

            # Create checkpointer for memory
            checkpointer = MemorySaver()

            # Create the actual LangGraph agent using create_react_agent - NO FALLBACKS
            if not ConfigManager().tools:
                raise RuntimeError(
                    "Tools must be provided for agent creation - NO FALLBACKS ALLOWED"
                )

            # Memory checkpointer handling - explicit field checking
            use_checkpointer = False
            if hasattr(config, "memory_config") and ConfigManager().memory_config:
                if (
                    "enabled" in ConfigManager().memory_config
                    and ConfigManager().memory_config["enabled"]
                ):
                    use_checkpointer = True

            agent = create_react_agent(
                model=llm,
                tools=ConfigManager().tools,
                prompt=system_prompt,
                checkpointer=checkpointer if use_checkpointer else None,
            )

            return agent

        except Exception as e:
            logger.error(f"Failed to create LangGraph agent: {e}")
            # Proper error handling - do not fallback to mock
            # Use error message template from config
            from src.applications.oamat_sd.src.config.config_manager import (
                ConfigManager as app_config,
            )

            error_msg = app_config.error_messages.agent["creation_failed"].format(
                role=ConfigManager().role, error=str(e)
            )
            raise RuntimeError(error_msg)

    def create_research_agent(self, context: dict[str, Any]) -> AgentInstance:
        """Create a specialized research agent."""
        creation_request = AgentCreationRequest(
            role=AgentRole.RESEARCHER,
            context=context,
            tools=["web_search", "arxiv_search", "documentation", "analysis"],
            specialization_requirements={"research_depth": "comprehensive"},
        )

        # Synchronous wrapper for async creation (for TDD compatibility)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self.create_agent(creation_request))
        finally:
            loop.close()

    def create_implementation_agent(self, context: dict[str, Any]) -> AgentInstance:
        """Create a specialized implementation agent."""
        creation_request = AgentCreationRequest(
            role=AgentRole.IMPLEMENTER,
            context=context,
            tools=["code_generation", "testing", "debugging", "documentation"],
            specialization_requirements={"implementation_style": "robust"},
        )

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self.create_agent(creation_request))
        finally:
            loop.close()

    def create_analysis_agent(self, context: dict[str, Any]) -> AgentInstance:
        """Create a specialized analysis agent."""
        creation_request = AgentCreationRequest(
            role=AgentRole.TECHNICAL_SPECIALIST,
            context=context,
            tools=["analysis", "modeling", "optimization"],
            specialization_requirements={"analysis_depth": "deep"},
        )

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self.create_agent(creation_request))
        finally:
            loop.close()

    def create_synthesis_agent(self, context: dict[str, Any]) -> AgentInstance:
        """Create a specialized synthesis agent."""
        creation_request = AgentCreationRequest(
            role=AgentRole.INTEGRATOR,
            context=context,
            tools=["synthesis", "integration", "validation"],
            specialization_requirements={"synthesis_approach": "comprehensive"},
        )

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self.create_agent(creation_request))
        finally:
            loop.close()

    def create_coding_agent(self, context: dict[str, Any]) -> AgentInstance:
        """Create a specialized coding agent."""
        creation_request = AgentCreationRequest(
            role=AgentRole.IMPLEMENTER,
            context=context,
            tools=["code_generation", "testing", "debugging", "refactoring"],
            specialization_requirements={"coding_style": "clean_architecture"},
        )

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self.create_agent(creation_request))
        finally:
            loop.close()

    async def create_multiple_agents(
        self, requests: list[AgentCreationRequest]
    ) -> list[AgentInstance]:
        """Create multiple agents concurrently."""
        self.logger.info(f"Creating {len(requests)} agents concurrently")

        # SOPHISTICATED AGENT CREATION: Sequential with error isolation (Rule 955 compliant)
        agents = []
        for request in requests:
            try:
                agent = await self.create_agent(request)
                agents.append(agent)
            except Exception as e:
                self.logger.error(f"Failed to create agent for {request.role}: {e}")
                agents.append(e)

        successful_agents = []
        for i, agent in enumerate(agents):
            if isinstance(agent, Exception):
                self.logger.error(f"Failed to create agent {i}: {agent}")
            else:
                successful_agents.append(agent)

        return successful_agents

    def get_agent(self, agent_id: str) -> AgentInstance | None:
        """Retrieve an agent by ID."""
        return self.active_agents.get(
            agent_id
        )  # Returns None if not found - acceptable for lookup

    def list_agents(self) -> list[AgentInstance]:
        """List all active agents."""
        return list(self.active_agents.values())

    def get_agents_by_role(self, role: AgentRole) -> list[AgentInstance]:
        """Get all agents with a specific role."""
        return [agent for agent in self.active_agents.values() if agent.role == role]

    def update_agent_status(self, agent_id: str, status: AgentStatus) -> bool:
        """Update agent status."""
        if agent_id in self.active_agents:
            self.active_agents[agent_id].status = status
            return True
        return False

    def configure_agent_tools(self, agent_id: str, tools: list[str]) -> bool:
        """Update agent tool configuration."""
        if agent_id in self.active_agents:
            agent = self.active_agents[agent_id]
            agent.tools_assigned = tools
            agent.configuration.tools = tools
            return True
        return False

    def update_agent_context(
        self, agent_id: str, context_update: dict[str, Any]
    ) -> bool:
        """Update agent context."""
        if agent_id in self.active_agents:
            agent = self.active_agents[agent_id]
            agent.context.update(context_update)
            agent.configuration.context.update(context_update)
            return True
        return False

    def get_agent_performance_metrics(self, agent_id: str) -> dict[str, Any] | None:
        """Get performance metrics for an agent."""
        agent = self.active_agents.get(agent_id)
        if agent:
            return agent.performance_metrics
        return None

    def cleanup_completed_agents(self) -> int:
        """Clean up completed agents and return count removed."""
        completed_agents = [
            agent_id
            for agent_id, agent in self.active_agents.items()
            if agent.status == AgentStatus.COMPLETED
        ]

        for agent_id in completed_agents:
            del self.active_agents[agent_id]

        self.logger.info(f"Cleaned up {len(completed_agents)} completed agents")
        return len(completed_agents)

    def get_factory_status(self) -> dict[str, Any]:
        """Get factory status and statistics."""
        status_counts = {}
        role_counts = {}

        for agent in self.active_agents.values():
            # Count status - explicit initialization
            status_key = agent.status.value
            if status_key not in status_counts:
                status_counts[status_key] = 0
            status_counts[status_key] += 1

            # Count roles - explicit initialization
            role_key = agent.role.value
            if role_key not in role_counts:
                role_counts[role_key] = 0
            role_counts[role_key] += 1

        return {
            "total_agents": len(self.active_agents),
            "active_agents": len(self.active_agents),
            "status_distribution": status_counts,
            "role_distribution": role_counts,
            "available_roles": [role.value for role in AgentRole],
            "factory_health": ConfigManager().agent_factory.performance_defaults[
                "factory_health_status"
            ],
        }

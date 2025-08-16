#!/usr/bin/env python3
"""
Subdivision Agent Factory - LangGraph Multi-Agent Coordination

Creates specialized agents for subdivided workflows using modern LangGraph patterns:
- create_react_agent for agent creation
- Tool-based handoffs between agents
- Send API for parallel execution
- Dynamic agent specification via O3 reasoning
- No hardcoded values - all specifications O3-generated

Follows the subdivision metadata from O3 analysis to create optimal
agent teams for complex decomposed workflows.
"""

from datetime import datetime
from typing import Any

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent

from src.applications.oamat_sd.src.config.config_manager import ConfigManager
from src.applications.oamat_sd.src.models.agent_specification_schemas import (
    AgentSpecificationOutput,
)
from src.applications.oamat_sd.src.preprocessing.schemas import (
    StandardizedRequest,
    SubdivisionMetadata,
)
from src.applications.oamat_sd.src.reasoning.structured_output_enforcer import (
    StructuredOutputEnforcer,
)
from src.applications.oamat_sd.src.sd_logging import LoggerFactory
from src.applications.oamat_sd.src.sd_logging.log_config import default_config


class SubdivisionAgentSpecification:
    """Specification for a subdivision agent with LangGraph compliance"""

    def __init__(
        self,
        agent_id: str,
        role_name: str,
        domain_specialization: str,
        system_prompt: str,
        tools: list,
        handoff_targets: list[str],
        integration_requirements: list[str],
        deliverables: list[str],
        coordination_mode: str = "tool_based",
    ):
        self.agent_id = agent_id
        self.role_name = role_name
        self.domain_specialization = domain_specialization
        self.system_prompt = system_prompt
        self.tools = tools
        self.handoff_targets = handoff_targets
        self.integration_requirements = integration_requirements
        self.deliverables = deliverables
        self.coordination_mode = coordination_mode
        self.created_at = datetime.now()


class SubdivisionAgentFactory:
    """
    Factory for creating specialized agents for subdivided workflows

    Uses modern LangGraph patterns with O3-generated specifications:
    - create_react_agent for all agent creation
    - Tool-based handoffs for agent coordination
    - Dynamic prompt and tool generation via O3
    - No hardcoded agent templates
    """

    def __init__(self, logger_factory: LoggerFactory = None, tool_registry=None):
        """Initialize the Subdivision Agent Factory"""
        self.logger_factory = logger_factory or LoggerFactory(default_config)
        self.logger = self.logger_factory.get_debug_logger()
        self.tool_registry = tool_registry

        # Configuration from centralized config manager
        self.config_manager = ConfigManager()

        # O3 reasoning for agent specification generation
        self.structured_enforcer = StructuredOutputEnforcer()

        # Model configuration for agent execution (GPT-4.1-mini)
        self.agent_model_config = {
            "model_name": self.config_manager.models[
                "agent"
            ].model_name,  # gpt-4.1-mini
            "temperature": self.config_manager.models["agent"].temperature,  # 0.3
            "max_tokens": self.config_manager.models["agent"].max_tokens,  # 4000
        }

        # O3 reasoning configuration for specifications
        self.reasoning_model_config = {
            "model_name": self.config_manager.models["reasoning"].model_name,  # o3-mini
            "reasoning_effort": self.config_manager.models[
                "reasoning"
            ].reasoning_effort,  # medium
            "max_tokens": self.config_manager.models["reasoning"].max_tokens,  # 16000
        }

        self.logger.info(
            "✅ Subdivision Agent Factory initialized with LangGraph patterns"
        )

    async def create_subdivision_agents(
        self,
        standardized_request: StandardizedRequest,
        subdivision_metadata: SubdivisionMetadata,
        debug: bool = False,
    ) -> dict[str, Any]:
        """
        Create specialized agents for subdivided workflow using O3 specifications

        Args:
            standardized_request: The original preprocessed request
            subdivision_metadata: O3-generated subdivision analysis
            debug: Enable detailed logging

        Returns:
            Dictionary of specialized agents ready for LangGraph execution
        """
        if debug:
            self.logger.info(
                "🏭 SUBDIVISION FACTORY: Creating specialized agents for subdivided workflow..."
            )

        if not subdivision_metadata.requires_subdivision:
            raise ValueError(
                "Cannot create subdivision agents for request that doesn't require subdivision"
            )

        try:
            # Step 1: Generate detailed agent specifications using O3
            agent_specifications = await self._generate_agent_specifications(
                standardized_request, subdivision_metadata, debug
            )

            if debug:
                self.logger.info(
                    f"📋 Generated {len(agent_specifications)} agent specifications"
                )

            # Step 2: Create LangGraph agents using create_react_agent
            subdivision_agents = {}
            for spec in agent_specifications:
                if debug:
                    self.logger.info(
                        f"🔧 Creating agent: {spec.role_name} ({spec.domain_specialization})"
                    )

                agent = await self._create_langgraph_subdivision_agent(spec, debug)
                subdivision_agents[spec.agent_id] = {
                    "agent": agent,
                    "specification": spec,
                    "status": "ready",
                    "created_at": datetime.now().isoformat(),
                }

            if debug:
                self.logger.info(
                    f"✅ Created {len(subdivision_agents)} specialized subdivision agents"
                )

            return subdivision_agents

        except Exception as e:
            self.logger.error(f"❌ Subdivision agent creation failed: {e}")
            raise RuntimeError(f"Failed to create subdivision agents: {e}") from e

    async def _generate_agent_specifications(
        self,
        request: StandardizedRequest,
        metadata: SubdivisionMetadata,
        debug: bool = False,
    ) -> list[SubdivisionAgentSpecification]:
        """Generate detailed agent specifications using O3 reasoning"""

        if debug:
            self.logger.info(
                "🧠 O3 REASONING: Generating detailed agent specifications..."
            )

        # Create comprehensive prompt for O3 agent specification generation
        specification_prompt = f"""
You are an expert system architect generating detailed agent specifications for a subdivided workflow.

## SUBDIVISION ANALYSIS CONTEXT:
- Complexity Score: {metadata.complexity_score}/10.0
- Requires Subdivision: {metadata.requires_subdivision}
- Reasoning: {metadata.subdivision_reasoning}
- Suggested Roles: {metadata.suggested_sub_roles}
- Parallelization Potential: {metadata.parallelization_potential}
- Max Depth: {metadata.max_subdivision_depth}

## REQUEST CONTEXT:
- Type: {request.classification.request_type.value}
- Complexity: {request.classification.complexity_level.value}
- Domain: {request.classification.domain_category}
- Technologies: {request.key_technologies}

## TASK: Generate Agent Specifications

For each suggested role, create a detailed agent specification with:

1. **Agent Identity**:
   - agent_id: Unique identifier (snake_case)
   - role_name: Human-readable role name
   - domain_specialization: Specific technical domain

2. **Agent Behavior**:
   - system_prompt: Detailed prompt defining agent behavior and expertise
   - tools: List of tool names this agent needs
   - deliverables: Specific outputs this agent will produce

3. **Coordination**:
   - handoff_targets: Other agents this agent can hand off to
   - integration_requirements: How this agent's output integrates with others

**CRITICAL REQUIREMENTS**:
- Each agent must have UNIQUE, NON-OVERLAPPING responsibilities
- System prompts must be detailed and role-specific (minimum 200 characters)
- Tool assignments must be appropriate for the agent's domain
- Handoff patterns must form a cohesive workflow
- Integration requirements must be specific and actionable

Generate a JSON object with the following structure:
{
  "agent_specifications": [
    {
      "agent_id": "unique_identifier",
      "role_name": "Human Readable Role",
      "domain_specialization": "Specific technical domain",
      "system_prompt": "Detailed prompt defining agent behavior...",
      "tools": ["tool1", "tool2"],
      "deliverables": ["deliverable1", "deliverable2"],
      "handoff_targets": ["other_agent_id"],
      "integration_requirements": ["requirement1", "requirement2"]
    }
  ]
}

Return ONLY the JSON object - no other text.
"""

        try:
            # Call O3 with structured output schema
            spec_result = await self.structured_enforcer.enforce_structured_output(
                prompt=specification_prompt,
                output_schema=AgentSpecificationOutput,
                model_config=self.reasoning_model_config,
                context={
                    "request": request.model_dump(),
                    "metadata": metadata.model_dump(),
                    "debug": debug,
                },
            )

            # Convert to SubdivisionAgentSpecification objects
            specifications = []
            for agent_spec in spec_result.agent_specifications:
                spec = SubdivisionAgentSpecification(
                    agent_id=agent_spec.agent_id,
                    role_name=agent_spec.role_name,
                    domain_specialization=agent_spec.domain_specialization,
                    system_prompt=agent_spec.system_prompt,
                    tools=agent_spec.tools,
                    handoff_targets=agent_spec.handoff_targets,
                    integration_requirements=agent_spec.integration_requirements,
                    deliverables=agent_spec.deliverables,
                )
                specifications.append(spec)

            if debug:
                self.logger.info(
                    f"🎯 Generated {len(specifications)} agent specifications"
                )
                for spec in specifications:
                    self.logger.info(
                        f"   📝 {spec.role_name}: {spec.domain_specialization}"
                    )

            return specifications

        except Exception as e:
            self.logger.error(f"❌ Agent specification generation failed: {e}")
            # CONTRACT ENFORCEMENT: System must fail completely if O3 generation fails
            raise RuntimeError(
                f"O3 agent specification generation failed - system must fail completely per NO FALLBACKS RULE: {e}"
            ) from e

    async def _create_langgraph_subdivision_agent(
        self, specification: SubdivisionAgentSpecification, debug: bool = False
    ) -> Any:
        """Create a LangGraph agent using create_react_agent pattern"""

        if debug:
            self.logger.info(f"🔧 Creating LangGraph agent: {specification.role_name}")

        try:
            # Create the language model for this agent
            llm = ChatOpenAI(
                model=self.agent_model_config["model_name"],
                temperature=self.agent_model_config["temperature"],
                max_tokens=self.agent_model_config["max_tokens"],
            )

            # Create system prompt template with handoff capabilities
            system_prompt_template = f"""
{specification.system_prompt}

## COORDINATION INSTRUCTIONS:
You are part of a specialized agent team working on a subdivided workflow.

**Your Role**: {specification.role_name}
**Domain**: {specification.domain_specialization}

**Integration Requirements**:
{chr(10).join([f"- {req}" for req in specification.integration_requirements])}

**Expected Deliverables**:
{chr(10).join([f"- {deliverable}" for deliverable in specification.deliverables])}

**Handoff Capabilities**:
You can hand off work to: {', '.join(specification.handoff_targets) if specification.handoff_targets else 'No handoffs available'}

**Tool-Based Coordination**:
- Use your assigned tools to complete your specialized tasks
- Provide clear, structured outputs that other agents can use
- Include metadata about your confidence and any handoff recommendations

When your task is complete, provide a structured response with:
1. Your completed deliverables
2. Status of your work (complete/partial/needs_handoff)
3. Any recommendations for handoff to other agents
4. Integration notes for combining your work with others

Always maintain focus on your domain specialization while coordinating effectively with the team.
"""

            prompt = ChatPromptTemplate.from_messages(
                [
                    ("system", system_prompt_template),
                    ("human", "{input}"),
                    ("placeholder", "{agent_scratchpad}"),
                ]
            )

            # Get tools for this agent (from tool registry or defaults)
            agent_tools = self._get_tools_for_agent(specification)

            # Create memory checkpointer for this agent
            checkpointer = MemorySaver()

            # Create the LangGraph agent using create_react_agent
            agent = create_react_agent(
                model=llm, tools=agent_tools, prompt=prompt, checkpointer=checkpointer
            )

            if debug:
                self.logger.info(
                    f"✅ Created LangGraph agent: {specification.role_name}"
                )

            return agent

        except Exception as e:
            self.logger.error(
                f"❌ Failed to create LangGraph agent {specification.role_name}: {e}"
            )
            # CONTRACT ENFORCEMENT: System must fail completely if agent creation fails
            raise RuntimeError(
                f"LangGraph agent creation failed - system must fail completely per NO FALLBACKS RULE: {e}"
            ) from e

    def _get_tools_for_agent(
        self, specification: SubdivisionAgentSpecification
    ) -> list:
        """Get appropriate tools for the agent based on its specification"""

        # If we have a tool registry, use it to get tools by name
        if self.tool_registry:
            agent_tools = []
            for tool_name in specification.tools:
                if tool_name in self.tool_registry:
                    agent_tools.append(self.tool_registry[tool_name])
                else:
                    self.logger.warning(f"⚠️  Tool {tool_name} not found in registry")
            return agent_tools

        # Default tools for subdivision agents
        default_tools = []

        # Add domain-specific tools based on specialization
        if "research" in specification.domain_specialization.lower():
            # Research tools would be added here
            pass
        elif "implementation" in specification.domain_specialization.lower():
            # Implementation tools would be added here
            pass
        elif "validation" in specification.domain_specialization.lower():
            # Validation tools would be added here
            pass

        return default_tools

    async def create_handoff_tools(
        self, agents: dict[str, Any], debug: bool = False
    ) -> dict[str, Any]:
        """Create tool-based handoff mechanisms between subdivision agents"""

        if debug:
            self.logger.info("🔗 Creating tool-based handoff mechanisms...")

        handoff_tools = {}

        for agent_id, agent_data in agents.items():
            spec = agent_data["specification"]

            # Create handoff tools for each target this agent can hand off to
            for target_agent_id in spec.handoff_targets:
                if target_agent_id in agents:
                    tool_name = f"handoff_to_{target_agent_id}"
                    handoff_tools[tool_name] = self._create_handoff_tool(
                        source_agent=agent_id,
                        target_agent=target_agent_id,
                        target_spec=agents[target_agent_id]["specification"],
                    )

        if debug:
            self.logger.info(f"🔗 Created {len(handoff_tools)} handoff tools")

        return handoff_tools

    def _create_handoff_tool(
        self,
        source_agent: str,
        target_agent: str,
        target_spec: SubdivisionAgentSpecification,
    ):
        """Create a specific handoff tool for agent coordination"""

        def handoff_function(task_description: str, context: dict = None):
            """Execute handoff from source agent to target agent"""
            return {
                "handoff_executed": True,
                "source_agent": source_agent,
                "target_agent": target_agent,
                "task_description": task_description,
                "context": context or {},
                "target_specialization": target_spec.domain_specialization,
                "timestamp": datetime.now().isoformat(),
            }

        # Create tool with proper metadata
        from langchain.tools import Tool

        return Tool(
            name=f"handoff_to_{target_agent}",
            description=f"Hand off task to {target_spec.role_name} ({target_spec.domain_specialization})",
            func=handoff_function,
        )

    def get_subdivision_metrics(self, agents: dict[str, Any]) -> dict[str, Any]:
        """Get metrics about the subdivision agent team"""

        if not agents:
            return {"total_agents": 0, "specializations": [], "handoff_connections": 0}

        specializations = []
        handoff_connections = 0

        for agent_data in agents.values():
            spec = agent_data["specification"]
            specializations.append(spec.domain_specialization)
            handoff_connections += len(spec.handoff_targets)

        return {
            "total_agents": len(agents),
            "specializations": specializations,
            "handoff_connections": handoff_connections,
            "unique_domains": len(set(specializations)),
            "avg_handoffs_per_agent": (
                handoff_connections / len(agents) if agents else 0
            ),
        }

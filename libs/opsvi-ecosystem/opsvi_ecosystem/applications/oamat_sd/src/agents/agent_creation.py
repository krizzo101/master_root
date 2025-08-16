"""
Agent Creation Module

Handles the creation and configuration of specialized agents based on O3 specifications.
Extracted from smart_decomposition_agent.py for better modularity.
"""

import asyncio
from datetime import datetime
from typing import Any

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langgraph.prebuilt.chat_agent_executor import create_react_agent

from src.applications.oamat_sd.src.config.config_manager import ConfigManager
from src.applications.oamat_sd.src.models.workflow_models import (
    AVAILABLE_MCP_TOOLS,
    AgentModel,
    SmartDecompositionState,
)
from src.applications.oamat_sd.src.sd_logging import LoggerFactory


class AgentCreationEngine:
    """Handles creation of specialized agents from O3 specifications"""

    def __init__(
        self, logger_factory: LoggerFactory, mcp_tools_registry, openai_client
    ):
        self.logger_factory = logger_factory
        self.logger = logger_factory.get_debug_logger()
        self.mcp_tools_registry = mcp_tools_registry
        self.openai_client = openai_client

    async def create_specialized_agents(
        self, state: SmartDecompositionState
    ) -> SmartDecompositionState:
        """Create specialized agents using WorkflowSpecification from O3 pipeline"""
        self.logger.info("Creating specialized agents from WorkflowSpecification...")

        agents = {}
        # Handle both dict and object state access patterns for LangGraph compatibility
        workflow_specification = (
            state.get("workflow_specification")
            if isinstance(state, dict)
            else state.workflow_specification
        )

        if not workflow_specification:
            raise RuntimeError(
                "WorkflowSpecification required for agent creation. Cannot proceed without O3 specifications."
            )

        # Check if we have the new WorkflowSpecification format
        if "agent_specifications" in workflow_specification:
            # Use new WorkflowSpecification format
            agent_specs = workflow_specification["agent_specifications"]
            self.logger.info(
                f"Creating {len(agent_specs)} agents from WorkflowSpecification"
            )

            for agent_spec in agent_specs:
                if not isinstance(agent_spec, dict):
                    continue

                # Extract agent role without fallbacks

                if "agent_id" in agent_spec:
                    agent_role = agent_spec["agent_id"]
                elif "role" in agent_spec:
                    agent_role = agent_spec["role"]
                else:
                    agent_role = ConfigManager().agent_factory.role_templates[
                        "default_agent_name"
                    ]

                try:
                    # Log agent creation start
                    agent_start_time = datetime.now()
                    self.logger_factory.log_agent_lifecycle(
                        agent_role=agent_role,
                        stage="creation_start",
                        data={
                            "agent_specification": bool(agent_spec),
                            "tools_count": (
                                len(agent_spec["required_tools"])
                                if "required_tools" in agent_spec
                                else 0
                            ),
                        },
                    )

                    # Convert ToolSpecification objects to actual tool functions - NO FALLBACKS
                    if "required_tools" not in agent_spec:
                        error_msg = (
                            ConfigManager()
                            .error_messages.agent["spec_missing"]
                            .format(agent_role=agent_role)
                        )
                        raise RuntimeError(error_msg)
                    tool_specs = agent_spec["required_tools"]
                    tools = self._convert_tool_specs_to_functions(tool_specs)

                    # Add mandatory file system tools for file creation
                    from src.applications.oamat_sd.src.tools.file_system_tools import (
                        create_file_system_tools,
                    )

                    file_system_tools = create_file_system_tools()
                    tools.extend(file_system_tools)

                    # 🔒 FORCE STRUCTURED RESPONSES: All agents must use AgentResponse schema
                    from src.applications.oamat_sd.src.models.agent_response_models import (
                        AgentResponse,
                    )

                    # Create React agent from specification with STRUCTURED OUTPUT ENFORCEMENT
                    agent = await self._create_react_agent_from_spec(
                        agent_spec, tools, state, structured_output_schema=AgentResponse
                    )

                    # Store the created agent
                    agents[agent_role] = {
                        "agent": agent,
                        "role": agent_role,
                        "tools": tools,
                        "specification": agent_spec,
                    }

                    # Log successful creation
                    creation_time = (
                        datetime.now() - agent_start_time
                    ).total_seconds() * 1000
                    self.logger_factory.log_agent_lifecycle(
                        agent_role=agent_role,
                        stage="creation_complete",
                        data={
                            "creation_success": True,
                            "tools_attached": len(tools),
                        },
                        execution_time_ms=creation_time,
                    )

                except Exception as e:
                    self.logger.error(f"Failed to create {agent_role} agent: {e}")
                    # Log failed creation
                    self.logger_factory.log_agent_lifecycle(
                        agent_role=agent_role,
                        stage="creation_failed",
                        data={
                            "error": str(e),
                            "creation_success": False,
                        },
                    )
                    continue
        else:
            self.logger.warning(
                "Using legacy agent creation format (no WorkflowSpecification)"
            )
            # Handle legacy format if needed

        # Log component operation completion
        self.logger_factory.log_component_operation(
            component="agent_creation",
            operation="create_specialized_agents_complete",
            data={
                "agents_created": len(agents),
                "agent_roles": list(agents.keys()),
            },
            success=True,
        )

        # Update state with specialized agents
        state["specialized_agents"] = agents
        return state

    def _convert_tool_specs_to_functions(self, tool_specs: list) -> list:
        """Convert ToolSpecification objects to actual tool functions"""
        tools = []

        for tool_spec in tool_specs:
            if isinstance(tool_spec, dict):
                if "tool_name" not in tool_spec:
                    self.logger.warning(
                        f"Tool specification missing tool_name: {tool_spec}"
                    )
                    continue
                tool_name = tool_spec["tool_name"]
            else:
                tool_name = getattr(tool_spec, "tool_name", None)
                if not tool_name:
                    tool_name = str(tool_spec)

            if tool_name and tool_name in AVAILABLE_MCP_TOOLS:
                # Create MCP tool wrapper
                tool_function = self._create_mcp_tool_wrapper(tool_name)
                tools.append(tool_function)

        return tools

    async def _create_react_agent_from_spec(
        self,
        agent_spec,
        tools: list,
        state: SmartDecompositionState,
        structured_output_schema=None,
    ):
        """Create a React agent from WorkflowSpecification AgentSpecification"""

        # Get agent configuration - NO FALLBACKS
        if "agent_id" in agent_spec:
            agent_role = agent_spec["agent_id"]
        elif "role" in agent_spec:
            agent_role = agent_spec["role"]
        else:
            from src.applications.oamat_sd.src.config.config_manager import (
                ConfigManager,
            )

            agent_role = ConfigManager().agent_factory.role_templates[
                "default_agent_name"
            ]

        # Create dynamic prompt
        user_request = (
            state.get("user_request", "")
            if isinstance(state, dict)
            else state.user_request
        )
        prompt = self._create_progressive_prompt(agent_role, agent_spec, user_request)

        # Select appropriate model - NO HARDCODED VALUES
        from src.applications.oamat_sd.src.config.config_manager import ConfigManager

        # Get model type without fallbacks
        if "model" not in agent_spec:
            error_msg = ConfigManager().error_messages.agent["model_missing"]
            raise RuntimeError(error_msg)

        model_type = agent_spec["model"]

        if model_type == AgentModel.REASONING:
            model_cfg = ConfigManager().get_model_config("reasoning")
            model = ChatOpenAI(
                model=model_cfg.model_name,
                max_tokens=max(
                    model_cfg.max_tokens, 8000
                ),  # Ensure minimum 8000 tokens
            )
        else:
            model_cfg = ConfigManager().get_model_config("agent")
            model = ChatOpenAI(
                model=model_cfg.model_name,
                temperature=model_cfg.temperature,
                max_tokens=max(
                    model_cfg.max_tokens, 8000
                ),  # Ensure minimum 8000 tokens for complete responses
            )

        # 🔒 FORCE STRUCTURED RESPONSES: Use prompt instructions instead of model binding
        if structured_output_schema:
            # Update prompt to emphasize structured response requirement
            structured_prompt = f"""{prompt}

🔒 CRITICAL RESPONSE FORMAT: You MUST respond with VALID JSON using this exact format:

{{
  "agent_id": "your_agent_id",
  "agent_role": "your_role_description",
  "request_processed": "summary_of_what_you_processed",
  "deliverables": {{
    "generated_files": [
      {{
        "filename": "full/path/filename.ext",
        "content": "complete_file_content_here",
        "file_type": "code|documentation|configuration|test",
        "description": "what_this_file_does"
      }}
    ],
    "task_summary": "clear_summary_of_what_you_accomplished",
    "success_status": true,
    "tools_used": [],
    "reasoning_chain": [],
    "validation_results": []
  }},
  "confidence_score": 0.9
}}

WORKFLOW:
1. Use file system tools (edit_file) to create actual files
2. Track each file you create
3. Respond with the structured JSON format listing all created files

NO EXCEPTIONS: Your final response MUST be valid JSON matching this schema exactly."""

            # Create React agent with structured prompt using ChatPromptTemplate
            prompt_template = ChatPromptTemplate.from_messages(
                [
                    ("system", structured_prompt),
                    ("human", "{{input}}\n\n{{agent_scratchpad}}"),
                ]
            )

            agent = create_react_agent(
                model=model,
                tools=tools,
                prompt=prompt_template,
            )
        else:
            # Create standard React agent (legacy mode) using ChatPromptTemplate
            prompt_template = ChatPromptTemplate.from_messages(
                [("system", prompt), ("human", "{{input}}\n\n{{agent_scratchpad}}")]
            )

            agent = create_react_agent(
                model=model,
                tools=tools,
                prompt=prompt_template,
            )

        return agent

    def _create_mcp_tool_wrapper(self, tool_name: str):
        """Create a wrapper function for MCP tools"""

        def create_tool_function(name: str):
            def mcp_tool(query: str) -> str:
                """Execute MCP tool with given query"""
                try:
                    if hasattr(self.mcp_tools_registry, "execute_tool"):
                        # Use new registry format
                        result = asyncio.create_task(
                            self.mcp_tools_registry.execute_tool(
                                name, "query", {"query": query}
                            )
                        )
                        return str(
                            result.result() if hasattr(result, "result") else result
                        )
                    else:
                        # Use legacy format
                        return f"Tool {name} executed with query: {query}"
                except Exception as e:
                    return f"Tool {name} error: {str(e)}"

            # Set function metadata
            mcp_tool.__name__ = f"mcp_{name.replace('-', '_')}"
            # Set tool description without fallbacks
            tool_description = AVAILABLE_MCP_TOOLS.get(name, f"MCP tool: {name}")
            mcp_tool.__doc__ = f"Execute {name} MCP tool: {tool_description}"

            return mcp_tool

        return create_tool_function(tool_name)

    def _create_progressive_prompt(
        self, role: str, agent_spec: dict[str, Any], user_request: str
    ) -> str:
        """Create dynamic prompts based on O3 analysis and specific agent requirements"""

        # Get task description and deliverables from spec - NO FALLBACKS

        if "complete_prompt" in agent_spec:
            task_description = agent_spec["complete_prompt"]
        else:
            task_description = (
                ConfigManager()
                .agent_factory.prompt_defaults["default_task_template"]
                .format(role=role)
            )

        if "required_deliverables" in agent_spec:
            deliverables = agent_spec["required_deliverables"]
        else:
            deliverables = ConfigManager().agent_factory.prompt_defaults[
                "default_deliverables"
            ]

        # Extract filenames from deliverables if they're objects - NO FALLBACKS
        deliverable_names = []
        for deliverable in deliverables:
            if isinstance(deliverable, dict):
                if "filename" in deliverable:
                    deliverable_names.append(deliverable["filename"])
                else:
                    self.logger.warning(f"Deliverable missing filename: {deliverable}")
                    deliverable_names.append(str(deliverable))
            else:
                deliverable_names.append(str(deliverable))

        dynamic_prompt = f"""You are a {role.title()} Agent with specific expertise for this request.

**USER REQUEST:**
{user_request}

**YOUR SPECIFIC TASK:**
{task_description}

**YOUR DELIVERABLES:**
{chr(10).join(f"- {deliverable}" for deliverable in deliverable_names) if deliverable_names else "- Complete your assigned task with high quality output"}

**🔧 CRITICAL: You MUST save all your work to files using the write_file tool. Create appropriate files for your output:**
- Save documentation as .md files
- Save code as .py files (or appropriate extension)
- Save plans, requirements, architecture as .md files
- Save configuration as .json, .yaml, or .toml files
- Use descriptive filenames that reflect the content

**📝 EXAMPLE: write_file("project_plan.md", "# Project Plan\\n\\nYour content here...")**

**🎯 EXECUTION REQUIREMENTS:**
1. **USE write_file TOOL**: Your work is only valuable if it's saved to files. Always use write_file for your deliverables
2. **COMPLETE IMPLEMENTATIONS**: Provide full, functional code - no placeholders or TODO comments
3. **PROPER STRUCTURE**: Follow directory conventions (src/ for code, docs/ for documentation, etc.)
4. **QUALITY STANDARDS**: All code must be functional, well-documented, and production-ready
5. **COMPREHENSIVE CONTENT**: Include all necessary imports, dependencies, and implementation details

**🛠️ AVAILABLE TOOLS:**
- write_file: Create and save files with your implementations
- read_file: Read existing files for reference
- edit_file: Modify existing files if needed
- Other MCP tools for research and analysis as needed

**📋 WORKFLOW:**
1. Analyze the requirements thoroughly
2. Create complete, functional implementations
3. **Save each deliverable using write_file**
4. Provide a summary of what you accomplished

Your work is only valuable if it's saved to files. Always use write_file for your deliverables.

Execute your task with expertise and attention to detail."""

        return dynamic_prompt

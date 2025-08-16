"""
OAMAT Agent Factory - Tools Manager

Refactored LangGraphAgentTools class that delegates to modular tool functions.
Extracted from agent_factory.py for better modularity and maintainability.
"""

import logging
from typing import Annotated, Any, Dict, Optional

from langchain_core.tools import InjectedToolCallId, tool
from langgraph.prebuilt import InjectedState
from langgraph.types import Command

# Import modular tool functions
from src.applications.oamat.agents.agent_factory.tools import (
    create_academic_search_tool,
    create_analysis_tools,
    create_architecture_tools,
    create_automation_tools,
    create_code_generation_tool,
    create_code_review_tool,
    create_completion_tool,
    create_database_operations_tools,
    create_deployment_tools,
    create_design_tools,
    create_diagram_generation_tools,
    create_documentation_tool,
    create_file_system_tools,
    create_knowledge_search_tool,
    create_mcp_research_tools,
    create_monitoring_tools,
    create_planning_frameworks_tools,
    create_quality_assurance_tools,
    create_quality_standards_tools,
    create_security_framework_tools,
    create_state_management_tools,
    create_testing_framework_tools,
    create_web_scraping_tools,
    create_web_search_tool,
)

logger = logging.getLogger("OAMAT.AgentFactory.ToolsManager")


class LangGraphAgentTools:
    """Collection of tools and utilities for LangGraph agents"""

    def __init__(
        self,
        llm_config: Optional[Dict] = None,
        neo4j_client=None,
        mcp_registry=None,
    ):
        self.llm_config = llm_config or {}
        self.neo4j_client = neo4j_client
        self.mcp_registry = mcp_registry
        self.logger = logging.getLogger("LangGraphAgentTools")

        # Initialize rules manager for rule access tools
        from src.applications.oamat.utils.rules_integration import get_rules_manager

        self.rules_manager = get_rules_manager()

        # FIXED: Create a proper base agent for tool operations
        # FAIL-FAST: No try/except. If the base agent fails to initialize,
        # the entire application startup should fail.
        from src.applications.oamat.agents.llm_base_agent import LLMBaseAgent

        # Create a concrete implementation of LLMBaseAgent for tools
        class ToolsBaseAgent(LLMBaseAgent):
            def build_prompt(self, *args, **kwargs) -> str:
                return str(args[0]) if args else ""

            def parse_output(self, output: Any) -> Any:
                return output

            def process_request(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
                """
                Process tool requests using LLM execution

                Args:
                    input_data: Dict with 'task' and 'prompt' keys

                Returns:
                    Dict with 'response' key containing the result
                """
                try:
                    task = input_data.get("task", "general")
                    prompt = input_data.get("prompt", "")

                    if not prompt:
                        raise ValueError("No prompt provided")

                    # Execute task using the inherited execute_task method
                    result = self.execute_task(prompt)

                    return {"response": result}

                except Exception as e:
                    self.logger.error(f"Error in ToolsBaseAgent.process_request: {e}")
                    raise

        # Get model from config or use default
        model = self.llm_config.get("model", "o3-mini")

        self.base_agent = ToolsBaseAgent(
            agent_name="ToolsAgent",
            role="Tool Support Agent",
            expertise=["tool_execution", "utility_functions"],
            model=model,
        )
        self.logger.info("✅ Base agent created for tools")

    def create_handoff_tool(self, agent_name: str, description: str = None):
        """Create a handoff tool for agent-to-agent communication"""

        # Add a default description if not provided
        if description is None:
            description = (
                f"Transfer task to the {agent_name} agent for further processing."
            )

        @tool
        def handoff_tool(
            task_description: str,
            state: Annotated[
                dict, InjectedState
            ],  # FIXED: Use dict instead of MessagesState
            tool_call_id: Annotated[str, InjectedToolCallId],
        ) -> Command:
            """
            Hands off a task to another specialized agent.

            Args:
                task_description: A clear, specific, and actionable description of the task for the target agent.
                state: The current state of the workflow.
                tool_call_id: The ID of the tool call.

            Returns:
                A Command to route to the specified agent.
            """
            self.logger.info(
                f"Handoff tool called. Transferring to '{agent_name}' with task: '{task_description}'"
            )
            return Command(goto=agent_name, update={"task": task_description})

        return handoff_tool

    # Delegate to modular tool functions
    def create_file_system_tools(self):
        """Creates a suite of tools for file system operations."""
        return create_file_system_tools()

    def create_knowledge_search_tool(self):
        """Create a knowledge search tool"""
        return create_knowledge_search_tool(self.neo4j_client)

    def create_web_search_tool(self):
        """Create a web search tool"""
        return create_web_search_tool(self.mcp_registry)

    def create_academic_search_tool(self):
        """Create an academic search tool"""
        return create_academic_search_tool(self.mcp_registry)

    def create_mcp_research_tools(self):
        """Create MCP-based research tools"""
        return create_mcp_research_tools(self.mcp_registry)

    def create_code_generation_tool(self):
        """Create a code generation tool"""
        return create_code_generation_tool(self.base_agent)

    def create_review_tool(self):
        """Create a code review tool"""
        return [create_code_review_tool(base_agent=self.base_agent)]

    def create_documentation_tool(self):
        """Create a documentation generation tool"""
        return create_documentation_tool(self.base_agent)

    def create_completion_tool(self):
        """Create a task completion tool"""
        return create_completion_tool()

    def create_testing_framework_tools(self):
        """Create testing framework tools"""
        return create_testing_framework_tools(base_agent=self.base_agent)

    def create_deployment_tools(self):
        """Create deployment tools"""
        return create_deployment_tools()

    def create_automation_tools(self):
        """Create automation tools"""
        return create_automation_tools()

    def create_quality_assurance_tools(self):
        """Create quality assurance tools"""
        return create_quality_assurance_tools()

    def create_quality_standards_tools(self):
        """Create quality standards tools"""
        return create_quality_standards_tools()

    def create_security_framework_tools(self):
        """Create security framework tools"""
        return create_security_framework_tools()

    def create_state_management_tools(self):
        """Create state management tools"""
        return create_state_management_tools()

    def create_monitoring_tools(self):
        """Create monitoring tools"""
        return create_monitoring_tools()

    def create_diagram_generation_tools(self):
        """Create diagram generation tools"""
        return create_diagram_generation_tools(base_agent=self.base_agent)

    def create_rule_access_tools(self):
        """Creates tools for accessing project rules and standards."""
        return [self.rules_manager.get_rules_retriever_tool()]

    def create_completion_tool(self):
        """Creates a tool that signals the completion of a task."""

        @tool
        def complete(reason: str) -> str:
            """
            Call this tool to signal that the task is complete.
            Provide a reason summarizing the outcome.
            """
            return f"✅ Task marked as complete: {reason}"

        return complete

    def create_analysis_tools(self):
        """Create analysis tools"""
        return create_analysis_tools()

    def create_design_tools(self):
        """Create design tools"""
        return create_design_tools(base_agent=self.base_agent)

    def create_architecture_tools(self):
        """Create architecture tools"""
        return create_architecture_tools(base_agent=self.base_agent)

    def create_quality_validation_tools(self):
        """Create quality validation tools"""
        # This can be an alias for QA tools or have its own implementation
        return create_quality_assurance_tools()

    def create_planning_frameworks_tools(self):
        """Create planning frameworks tools"""
        return create_planning_frameworks_tools(
            mcp_registry=self.mcp_registry, base_agent=self.base_agent
        )

    def create_database_operations_tools(self):
        """Create database operations tools"""
        return create_database_operations_tools(
            mcp_registry=self.mcp_registry,
            neo4j_client=self.neo4j_client,
            base_agent=self.base_agent,
        )

    def create_web_scraping_tools(self):
        """Create web scraping tools"""
        return create_web_scraping_tools(
            mcp_registry=self.mcp_registry, base_agent=self.base_agent
        )

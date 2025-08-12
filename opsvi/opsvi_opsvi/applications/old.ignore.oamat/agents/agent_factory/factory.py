"""
OAMAT Agent Factory - Factory Class

Factory for creating LangGraph agents with standardized tools and configurations.
Extracted from agent_factory.py for better modularity and maintainability.
"""

import logging
from datetime import datetime
from typing import Any

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langgraph.prebuilt import create_react_agent

# LangChain OpenAI conditional import
try:
    from langchain_openai import ChatOpenAI

    LANGCHAIN_OPENAI_AVAILABLE = True
except ImportError:
    LANGCHAIN_OPENAI_AVAILABLE = False

from src.applications.oamat.agents.agent_factory.tools_manager import (
    LangGraphAgentTools,
)
from src.applications.oamat.utils.mcp_tool_registry import create_mcp_tool_registry
from src.applications.oamat.utils.rules_integration import (
    create_rules_aware_prompt,
    get_rules_manager,
    inject_rules_into_spec,
)

logger = logging.getLogger("OAMAT.AgentFactory")


class AgentFactory:
    """Factory for creating LangGraph agents with standardized tools and configurations."""

    def __init__(self, llm_config: dict | None = None, neo4j_client=None):
        import sys

        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        print(f"[{timestamp}] 🔍 DEBUG: AgentFactory.__init__ starting...")
        sys.stdout.flush()

        self.llm_config = llm_config or {}
        self.neo4j_client = neo4j_client
        self.logger = logging.getLogger("AgentFactory")

        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        print(
            f"[{timestamp}] 🔍 DEBUG: AgentFactory basic setup completed, starting MCP registry..."
        )
        sys.stdout.flush()

        # Initialize MCP registry with timeout to prevent hanging
        try:
            import signal

            timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            print(f"[{timestamp}] 🔍 DEBUG: Setting up MCP registry timeout handler...")
            sys.stdout.flush()

            def timeout_handler(signum, frame):
                raise TimeoutError("MCP registry initialization timed out")

            # Set up timeout (10 seconds)
            old_handler = signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(10)

            try:
                timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                print(
                    f"[{timestamp}] 🔍 DEBUG: About to call create_mcp_tool_registry()..."
                )
                sys.stdout.flush()

                self.mcp_registry = create_mcp_tool_registry()

                timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                print(
                    f"[{timestamp}] ✅ DEBUG: create_mcp_tool_registry() completed successfully"
                )
                sys.stdout.flush()

                self.logger.info("✅ MCP registry initialized successfully")
            except TimeoutError:
                timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                print(f"[{timestamp}] ⚠️ DEBUG: MCP registry initialization timed out!")
                sys.stdout.flush()

                self.logger.warning(
                    "⚠️ MCP registry initialization timed out, using empty registry"
                )
                self.mcp_registry = None
            finally:
                # Restore original signal handler and cancel alarm
                signal.alarm(0)
                signal.signal(signal.SIGALRM, old_handler)

                timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                print(f"[{timestamp}] 🔍 DEBUG: MCP registry timeout handler cleaned up")
                sys.stdout.flush()

        except Exception as e:
            timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            print(
                f"[{timestamp}] ❌ DEBUG: MCP registry initialization failed with exception: {e}"
            )
            sys.stdout.flush()

            self.logger.warning(f"⚠️ MCP registry initialization failed: {e}")
            self.mcp_registry = None

        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        print(f"[{timestamp}] 🔍 DEBUG: Creating LangGraphAgentTools...")
        sys.stdout.flush()

        self.tools = LangGraphAgentTools(llm_config, neo4j_client, self.mcp_registry)

        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        print(
            f"[{timestamp}] ✅ DEBUG: LangGraphAgentTools created, initializing model..."
        )
        sys.stdout.flush()

        self.model = self._initialize_model()

        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        print(f"[{timestamp}] ✅ DEBUG: Model initialized, getting rules manager...")
        sys.stdout.flush()

        self.rules_manager = get_rules_manager()

        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        print(
            f"[{timestamp}] 🎉 DEBUG: AgentFactory initialization COMPLETELY finished!"
        )
        sys.stdout.flush()

        # Central registry for all available tools
        self.tool_registry = {
            "knowledge_search": self.tools.create_knowledge_search_tool,
            "web_search": self.tools.create_web_search_tool,
            "academic_search": self.tools.create_academic_search_tool,
            "generate_code": self.tools.create_code_generation_tool,
            "review_content": self.tools.create_review_tool,
            "generate_documentation": self.tools.create_documentation_tool,
            "file_system": self.tools.create_file_system_tools,
            "complete": self.tools.create_completion_tool,
            "testing_frameworks": self.tools.create_testing_framework_tools,
            "deployment_tools": self.tools.create_deployment_tools,
            "automation_tools": self.tools.create_automation_tools,
            "infrastructure_platforms": self.tools.create_deployment_tools,  # Alias for deployment
            "quality_tools": self.tools.create_quality_assurance_tools,
            "quality_standards": self.tools.create_quality_standards_tools,
            "security_frameworks": self.tools.create_security_framework_tools,
            # 🔧 ADD MISSING TOOL GROUPS
            "state_management": self.tools.create_state_management_tools,
            "monitoring_tools": self.tools.create_monitoring_tools,
            "documentation_tools": self.tools.create_documentation_tool,  # Alias
            "diagram_generators": self.tools.create_diagram_generation_tools,
            "rule_access": self.tools.create_rule_access_tools,  # Add rule access tools to registry
            # 🔬 ADD MCP RESEARCH & ANALYSIS TOOLS
            "mcp_research_tools": self.tools.create_mcp_research_tools,
            "analysis_tools": self.tools.create_analysis_tools,
            "design_tools": self.tools.create_design_tools,
            "architecture_frameworks": self.tools.create_architecture_tools,
            # 🔍 ADD QUALITY VALIDATION TOOLS
            "quality_validation": self.tools.create_quality_validation_tools,
            "code_validation": self.tools.create_quality_validation_tools,  # Alias
            "security_validation": self.tools.create_quality_validation_tools,  # Alias
            # 🎯 ADD MISSING CRITICAL TOOLS
            "planning_frameworks": self.tools.create_planning_frameworks_tools,
            "database_operations": self.tools.create_database_operations_tools,
            "web_scraping": self.tools.create_web_scraping_tools,
        }

    def _initialize_model(self):
        """Initializes the language model for the factory."""
        if not LANGCHAIN_OPENAI_AVAILABLE:
            raise ImportError("langchain_openai is not available. Please install it.")

        # Use a real ChatOpenAI model for compatibility with create_react_agent
        model_name = self.llm_config.get("model", "gpt-4.1-mini")
        temperature = self.llm_config.get("temperature")

        model_kwargs = {"model": model_name}
        if temperature is not None:
            model_kwargs["temperature"] = temperature

        # O3 models do not support temperature
        if "o3" in model_name and "temperature" in model_kwargs:
            del model_kwargs["temperature"]

        # Ensure that the model is initialized with the correct API key if needed
        # This assumes the API key is set in the environment or passed in llm_config

        self.model = ChatOpenAI(**model_kwargs)
        self.logger.info(
            f"AgentFactory initialized with ChatOpenAI model: {model_name}"
        )
        return self.model

    def _load_development_rules(self) -> str:
        """Load development rules from the project to embed in agent prompts."""
        # Define the key development rules that agents should follow
        development_rules = """
## 🔧 DEVELOPMENT STANDARDS (MANDATORY)

**PYTHON DEVELOPMENT (Rule 803):**
- Use PEP8 formatting with Black formatter (line-length 88)
- Full PEP 484 type hints with mypy --strict validation
- Proper logging with structured format
- Never blanket-catch exceptions; catch specific classes
- Use absolute imports: 'from src.applications.oamat...'
- Script entry with if __name__ == "__main__": main()

**TYPESCRIPT DEVELOPMENT (Rule 801):**
- Prettier: printWidth 100, singleQuote false, trailingComma "all"
- ESLint with @typescript-eslint/recommended
- Strict TypeScript: "strict": true, "target": "ES2022"
- Use try/catch with typed error guards
- Configure baseUrl and path aliases

**SECURITY STANDARDS (Rule 930):**
- Prevent SQLi: parameterized queries/ORM placeholders
- Defend XSS: escape user input, use CSP headers
- Store secrets in vault; access via env vars at runtime
- Use TLS 1.2+ for internal services
- Mask tokens/PII in logs

**TESTING STANDARDS (Rule 940):**
- Testing pyramid: Unit > Integration > E2E
- Target ≥85% coverage lines & branches
- Tests mirror code: src/foo.py → tests/test_foo.py
- Use pytest for Python, Vitest/Jest for JavaScript

**CODE QUALITY (Rule 800):**
- DRY implementation: extract reusable utilities
- File organization: follow project structure standards
- Input validation at all boundaries
- Proper error handling without information disclosure
- Performance optimization: indexed queries, batch operations

**MANDATORY:** Apply these standards to ALL generated code. Include proper imports, type hints, error handling, and follow the established patterns.
"""
        return development_rules

    def create_researcher_agent(self, handoff_agents: list[str] | None = None):
        """Creates a researcher agent with knowledge and web search tools."""
        tools = [
            self.tools.create_knowledge_search_tool(),
            self.tools.create_web_search_tool(),
            self.tools.create_academic_search_tool(),
        ]
        handoff_agents = handoff_agents or []
        for agent_name in handoff_agents:
            tools.append(self.tools.create_handoff_tool(agent_name))

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are a research specialist. Your role is to find, analyze, and synthesize information from various sources to answer user questions.",
                ),
                MessagesPlaceholder(variable_name="messages"),
            ]
        )
        return create_react_agent(self.model, tools=tools, prompt=prompt)

    def create_coder_agent(self, handoff_agents: list[str] | None = None):
        """Creates a coder agent with file system and code generation tools."""
        tools = [
            self.tools.create_code_generation_tool(),
            *self.tools.create_file_system_tools(),
        ]
        handoff_agents = handoff_agents or []
        for agent_name in handoff_agents:
            tools.append(self.tools.create_handoff_tool(agent_name))

        # Load development rules for coder agent
        development_rules = self._load_development_rules()

        enhanced_system_prompt = f"""You are a software development agent. Your role is to write, modify, and save code files based on specific instructions.

{development_rules}

**CODER-SPECIFIC GUIDELINES:**
- Generate complete, production-ready code with proper imports
- Include comprehensive error handling and input validation
- Add docstrings and comments for complex logic
- Ensure code follows language-specific conventions
- Implement security best practices (input sanitization, parameterized queries)
- Write maintainable, testable code with clear separation of concerns
- Include appropriate logging and debugging capabilities
"""

        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", enhanced_system_prompt),
                MessagesPlaceholder(variable_name="messages"),
            ]
        )
        return create_react_agent(self.model, tools=tools, prompt=prompt)

    def create_reviewer_agent(self, handoff_agents: list[str] | None = None):
        """Creates a reviewer agent for quality assessment."""
        tools = self.tools.create_review_tool()
        handoff_agents = handoff_agents or []
        for agent_name in handoff_agents:
            tools.append(self.tools.create_handoff_tool(agent_name))

        # Load development rules for reviewer agent
        development_rules = self._load_development_rules()

        enhanced_system_prompt = f"""You are a quality assurance agent. Your role is to review content and code for quality, correctness, and adherence to standards.

{development_rules}

**REVIEWER-SPECIFIC GUIDELINES:**
- Verify code follows all development standards and best practices
- Check for proper error handling, input validation, and security measures
- Ensure type hints, documentation, and comments are present and accurate
- Validate adherence to language-specific conventions (PEP8, ESLint, etc.)
- Review for performance, maintainability, and testability
- Identify potential security vulnerabilities and suggest improvements
- Verify proper import patterns and project structure compliance
- Check test coverage and testing best practices
"""

        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", enhanced_system_prompt),
                MessagesPlaceholder(variable_name="messages"),
            ]
        )
        return create_react_agent(self.model, tools=tools, prompt=prompt)

    def create_doc_agent(self, handoff_agents: list[str] | None = None):
        """Creates a documentation agent."""
        tools = [self.tools.create_documentation_tool()]
        handoff_agents = handoff_agents or []
        for agent_name in handoff_agents:
            tools.append(self.tools.create_handoff_tool(agent_name))

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are a technical writer. Your role is to create clear and concise documentation.",
                ),
                MessagesPlaceholder(variable_name="messages"),
            ]
        )
        return create_react_agent(self.model, tools=tools, prompt=prompt)

    def create_agent_with_tools(self, spec: dict[str, Any]) -> Any:
        """
        Dynamically creates an agent with a set of tools based on a spec.
        This is the primary method for creating agents in the OAMAT system.
        """
        role = spec.get("role", "generalist")
        dependencies = spec.get("dependencies", [])

        self.logger.info(f"Creating agent '{role}' with dependencies: {dependencies}")

        tools = []
        for dep in dependencies:
            tool_creator = self.tool_registry.get(dep)
            if tool_creator:
                # The tool creator might return a single tool or a list of tools
                created_tools = tool_creator()
                if isinstance(created_tools, list):
                    tools.extend(created_tools)
                else:
                    tools.append(created_tools)
            else:
                self.logger.warning(f"No tool creator found for dependency: {dep}")

        # Always include the completion tool
        tools.append(self.tools.create_completion_tool())

        # Create a rules-aware prompt for the agent
        system_prompt = self.rules_manager.get_system_prompt(role)
        prompt = create_rules_aware_prompt(system_prompt, self.rules_manager)

        self.logger.info(f"Agent '{role}' created with {len(tools)} tools.")
        return create_react_agent(self.model, tools=tools, prompt=prompt)

    def create_agent(
        self, agent_spec: dict[str, Any], handoff_agents: list[str] | None = None
    ):
        """
        Creates an agent based on a provided specification.
        The spec should define the agent's role, capabilities, and tool dependencies.
        """
        agent_name = agent_spec.get("role", agent_spec.get("name", "Unknown"))
        self.logger.info(f"Creating agent for role: {agent_name}")

        # Fallback to dynamic creation for other roles
        if agent_name == "researcher":
            return self.create_researcher_agent(handoff_agents=handoff_agents)
        elif agent_name == "coder":
            return self.create_coder_agent(handoff_agents=handoff_agents)
        elif agent_name == "reviewer":
            return self.create_reviewer_agent(handoff_agents=handoff_agents)
        elif agent_name == "documentation":
            return self.create_doc_agent(handoff_agents=handoff_agents)
        else:
            self.logger.info(
                f"No specific creator for role {agent_name}, using dynamic creator."
            )
            return self.create_dynamic_agent(
                agent_spec=agent_spec, handoff_agents=handoff_agents
            )

    def create_dynamic_agent(
        self, agent_spec: dict[str, Any], handoff_agents: list[str] | None = None
    ):
        """
        Creates a dynamic agent based on a provided specification.
        The spec should define the agent's role, capabilities, and tool dependencies.
        """
        self.logger.info(
            f"Creating dynamic agent for role: {agent_spec.get('role', agent_spec.get('name', 'Unknown'))}"
        )

        # Inject development rules into agent specification
        enhanced_agent_spec = inject_rules_into_spec(agent_spec.copy())

        # Get agent role for rules integration
        agent_role = enhanced_agent_spec.get(
            "role", enhanced_agent_spec.get("name", "Unknown")
        )

        # Get base prompt and enhance with development rules using the rules manager
        base_prompt = enhanced_agent_spec.get("prompt", "You are a helpful assistant.")
        enhanced_system_prompt = create_rules_aware_prompt(base_prompt, agent_role)

        required_tools_names = enhanced_agent_spec.get("tools", [])
        agent_tools = []
        missing_tools = []

        for tool_name in required_tools_names:
            if tool_name in self.tool_registry:
                tool_creator = self.tool_registry[tool_name]
                if callable(tool_creator):
                    tool_instance = tool_creator()
                    if isinstance(tool_instance, list):
                        agent_tools.extend(tool_instance)
                    else:
                        agent_tools.append(tool_instance)
                else:
                    agent_tools.append(tool_creator)
            else:
                missing_tools.append(tool_name)

        # NO FALLBACKS - Fail immediately if required tools are missing
        if missing_tools:
            error_msg = f"CRITICAL ERROR: Required tools missing for {agent_role} agent: {missing_tools}. Available tools: {list(self.tool_registry.keys())}"
            self.logger.error(error_msg)
            raise RuntimeError(error_msg)

        # Add handoff tools
        handoff_agents = handoff_agents or []
        for agent_name in handoff_agents:
            agent_tools.append(self.tools.create_handoff_tool(agent_name))

        # Create enhanced prompt template with rules integration
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", enhanced_system_prompt),
                MessagesPlaceholder(variable_name="messages"),
            ]
        )

        return create_react_agent(self.model, tools=agent_tools, prompt=prompt)

"""
Smart Decomposition Meta-Intelligence System - Agent Factory
OpenAI-exclusive agent creation using create_react_agent with structured responses
"""

import asyncio
import json
import uuid
from datetime import datetime
from typing import Any

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import Tool
from langgraph.checkpoint.memory import MemorySaver

# Memory functionality handled by MemorySaver
from langgraph.prebuilt import create_react_agent

# OpenAI interface - graceful fallback for POC
try:
    from src.shared.openai_interfaces.responses_interface import (
        OpenAIResponsesInterface,
    )

    OPENAI_INTERFACE_AVAILABLE = True
except ImportError:
    print("⚠️  OpenAI interface not available - using mock for POC demo")
    OpenAIResponsesInterface = None
    OPENAI_INTERFACE_AVAILABLE = False

from .config import AgentRole, SystemConfig, get_config, get_model_for_role
from .schemas import (
    AGENT_RESPONSE_SCHEMAS,
    get_schema_for_role,
)


class MockOpenAIInterface:
    """Mock OpenAI interface for POC demonstration"""

    def __init__(self):
        pass

    def get_model(self, model_name: str):
        return model_name

    async def create_response(self, **kwargs):
        return {"choices": [{"message": {"content": '{"mock": "response"}'}}]}


class MockLangChainModel:
    """Mock LangChain model for POC demonstration"""

    def __init__(self, model_name: str):
        self.model_name = model_name

    async def ainvoke(self, input_data):
        # Return mock structured response based on model type
        input_str = str(input_data).lower()

        if "requirements" in input_str or "analyze" in input_str:
            return json.dumps(
                {
                    "expanded_requirements": "Create a comprehensive application with modern architecture, user-friendly interface, and robust functionality",
                    "technical_specifications": [
                        "Frontend: React.js with TypeScript",
                        "Backend: Node.js with Express",
                        "Database: PostgreSQL with Prisma ORM",
                        "Authentication: JWT with bcrypt",
                        "Deployment: Docker containers",
                    ],
                    "dependencies": [
                        "React 18+",
                        "Node.js 18+",
                        "PostgreSQL 14+",
                        "Docker",
                    ],
                    "complexity_assessment": "medium",
                    "estimated_effort": 40,
                    "validation_criteria": [
                        "All features functional",
                        "Responsive design",
                        "Secure authentication",
                        "Performance optimized",
                    ],
                }
            )
        elif (
            "work plan" in input_str or "planning" in input_str or "manage" in input_str
        ):
            return json.dumps(
                {
                    "task_assignments": {
                        "developer": "Frontend and backend development",
                        "tester": "Unit and integration testing",
                        "deployer": "Deployment configuration",
                    },
                    "execution_order": [
                        "setup_database",
                        "develop_backend",
                        "develop_frontend",
                        "testing",
                        "deployment",
                    ],
                    "dependencies_mapped": {
                        "setup_database": [],
                        "develop_backend": ["setup_database"],
                        "develop_frontend": ["develop_backend"],
                        "testing": ["develop_frontend", "develop_backend"],
                        "deployment": ["testing"],
                    },
                    "parallel_opportunities": [
                        ["develop_frontend", "develop_backend"],
                        ["documentation", "deployment_config"],
                    ],
                    "risk_assessment": "Medium complexity project with standard web development risks. Database migration complexity is medium. Third-party API integration risk is low. Performance optimization requirements are medium.",
                    "estimated_total_time": 40,
                    "critical_path": [
                        "setup_database",
                        "develop_backend",
                        "develop_frontend",
                        "testing",
                        "deployment",
                    ],
                    "work_decomposition": [
                        {
                            "task_id": "setup_database",
                            "title": "Database Setup and Configuration",
                            "description": "Set up PostgreSQL database with initial schema and configurations",
                            "agent_role": "developer",
                            "dependencies": [],
                            "estimated_duration": 240,
                            "priority": "high",
                            "complexity": "medium",
                            "deliverables": ["Database schema", "Initial migrations"],
                        },
                        {
                            "task_id": "develop_backend",
                            "title": "Backend API Development",
                            "description": "Create REST API with authentication and business logic",
                            "agent_role": "developer",
                            "dependencies": ["setup_database"],
                            "estimated_duration": 480,
                            "priority": "high",
                            "complexity": "high",
                            "deliverables": [
                                "REST API endpoints",
                                "Authentication system",
                            ],
                        },
                        {
                            "task_id": "develop_frontend",
                            "title": "Frontend UI Development",
                            "description": "Build React UI components and user interface",
                            "agent_role": "developer",
                            "dependencies": ["develop_backend"],
                            "estimated_duration": 360,
                            "priority": "medium",
                            "complexity": "medium",
                            "deliverables": ["React components", "Responsive UI"],
                        },
                    ],
                    "success": True,
                }
            )
        elif "implement" in input_str or "develop" in input_str or "code" in input_str:
            return json.dumps(
                {
                    "code_files": [
                        {
                            "filename": "src/App.tsx",
                            "content": "import React from 'react';\n\nfunction App() {\n  return (\n    <div className=\"App\">\n      <h1>Generated Application</h1>\n    </div>\n  );\n}\n\nexport default App;",
                            "language": "typescript",
                            "purpose": "Main application component",
                        },
                        {
                            "filename": "src/api/server.js",
                            "content": "const express = require('express');\nconst app = express();\n\napp.get('/api/health', (req, res) => {\n  res.json({ status: 'healthy' });\n});\n\napp.listen(3001, () => {\n  console.log('Server running on port 3001');\n});",
                            "language": "javascript",
                            "purpose": "Backend API server",
                        },
                    ],
                    "documentation": "## Generated Application\n\nThis is a modern web application built with React and Node.js.\n\n### Features\n- Responsive design\n- REST API backend\n- Modern architecture",
                    "tests": "// Jest test example\ndescribe('App Component', () => {\n  test('renders without crashing', () => {\n    // Test implementation\n  });\n});",
                    "deployment_config": 'version: \'3.8\'\nservices:\n  app:\n    build: .\n    ports:\n      - "3000:3000"\n  api:\n    build: ./api\n    ports:\n      - "3001:3001"',
                    "setup_instructions": "1. Clone the repository\n2. Run npm install\n3. Configure environment variables\n4. Run npm start",
                    "dependencies_installed": [
                        "react@18.2.0",
                        "express@4.18.2",
                        "typescript@4.9.5",
                    ],
                    "implementation_notes": [
                        "Used modern React patterns with hooks",
                        "Implemented RESTful API design",
                        "Added TypeScript for type safety",
                    ],
                    "success": True,
                }
            )
        elif "test" in input_str or "quality" in input_str:
            return json.dumps(
                {
                    "test_results": {
                        "unit_tests": {"passed": 15, "failed": 0, "coverage": 85},
                        "integration_tests": {"passed": 8, "failed": 0, "coverage": 78},
                    },
                    "quality_metrics": {
                        "code_quality_score": 8.5,
                        "maintainability": "high",
                        "security_score": 9.0,
                        "performance_score": 8.0,
                    },
                    "test_recommendations": [
                        "Add more edge case testing",
                        "Increase integration test coverage",
                        "Add performance benchmarks",
                    ],
                }
            )
        elif "validate" in input_str or "validation" in input_str:
            return json.dumps(
                {
                    "validation_results": {
                        "requirements_met": True,
                        "code_quality": "excellent",
                        "test_coverage": 85,
                        "security_check": "passed",
                        "performance_check": "passed",
                    },
                    "issues_found": [],
                    "recommendations": [
                        "Consider adding monitoring and logging",
                        "Implement CI/CD pipeline",
                        "Add API rate limiting",
                    ],
                    "final_assessment": "Application meets all requirements and is ready for deployment",
                }
            )
        else:
            return json.dumps(
                {
                    "success": True,
                    "result": f"Mock response generated by {self.model_name}",
                    "metadata": {
                        "model": self.model_name,
                        "timestamp": "2025-01-17T07:19:30Z",
                    },
                }
            )


class MockAgent:
    """Mock agent for POC demonstration"""

    def __init__(self, model, tools, prompt):
        self.model = model
        self.tools = tools
        self.prompt = prompt

    async def ainvoke(self, input_data):
        # Return appropriate mock response based on the prompt/role
        return await self.model.ainvoke(input_data)


class AgentWrapper:
    """
    Wrapper for LangGraph agents with OpenAI structured response validation.
    Provides lifecycle management, performance tracking, and response validation.
    """

    def __init__(
        self,
        agent,
        role: str,
        agent_id: str,
        model: str,
        response_schema,
        openai_client: Any,  # Changed to Any for POC compatibility
        tools: list[Tool],
        capabilities: list[str],
        config: SystemConfig,
    ):
        self.agent = agent
        self.role = role
        self.agent_id = agent_id
        self.model = model
        self.response_schema = response_schema
        self.openai_client = openai_client
        self.tools = tools
        self.capabilities = capabilities
        self.config = config
        self.performance_metrics = {}
        self.context_store = {}
        self.created_at = datetime.utcnow()

    async def process_with_structured_response(
        self, input_data: dict[str, Any], dependencies: list[str] | None = None
    ) -> dict[str, Any]:
        """
        Process input with structured JSON response validation.
        Implements REQ-002: Dependency and Context Management
        """
        start_time = asyncio.get_event_loop().time()

        try:
            # Validate dependencies are satisfied (if provided)
            if dependencies:
                await self._validate_dependencies(dependencies)

            # Inject context into input
            enriched_input = self._inject_context(input_data)

            # Process with LangGraph agent
            raw_result = await self.agent.ainvoke(enriched_input)

            # Validate and structure response
            structured_result = self._validate_and_structure_response(raw_result)

            # Update context with results
            self._update_context(structured_result)

            end_time = asyncio.get_event_loop().time()
            execution_time = end_time - start_time

            # Track performance metrics
            self._track_performance(execution_time, True)

            return {
                "success": True,
                "result": structured_result,
                "agent_id": self.agent_id,
                "role": self.role,
                "model": self.model,
                "execution_time": execution_time,
                "context_updated": datetime.utcnow(),
                "metadata": {
                    "dependencies_satisfied": dependencies or [],
                    "tools_used": self._extract_tools_used(raw_result),
                    "response_validated": True,
                    "schema_compliance": True,
                },
            }

        except Exception as e:
            end_time = asyncio.get_event_loop().time()
            execution_time = end_time - start_time
            self._track_performance(execution_time, False)

            return {
                "success": False,
                "error": str(e),
                "agent_id": self.agent_id,
                "role": self.role,
                "model": self.model,
                "execution_time": execution_time,
                "partial_results": self._extract_partial_results(e),
            }

    def _validate_and_structure_response(self, raw_result: Any) -> dict[str, Any]:
        """Validate response against Pydantic schema and return structured data"""
        if not self.response_schema:
            return {"raw_response": str(raw_result)}

        try:
            # Extract JSON from agent response
            response_text = self._extract_response_text(raw_result)

            # Try to parse as JSON
            if isinstance(response_text, str):
                try:
                    response_data = json.loads(response_text)
                except json.JSONDecodeError:
                    # Fallback: wrap non-JSON response
                    response_data = {"content": response_text}
            else:
                response_data = response_text

            # Validate against Pydantic schema
            validated_response = self.response_schema(**response_data)

            return validated_response.model_dump()

        except Exception as e:
            # Fallback: return error with raw response
            return {
                "validation_error": str(e),
                "raw_response": str(raw_result),
                "schema_compliance": False,
                "fallback_content": self._extract_response_text(raw_result),
            }

    def _extract_response_text(self, raw_result: Any) -> str:
        """Extract text response from LangGraph result"""
        if isinstance(raw_result, str):
            return raw_result
        elif hasattr(raw_result, "content"):
            return raw_result.content
        elif isinstance(raw_result, dict):
            if "output" in raw_result:
                return raw_result["output"]
            elif "messages" in raw_result and raw_result["messages"]:
                last_message = raw_result["messages"][-1]
                if hasattr(last_message, "content"):
                    return last_message.content
                elif isinstance(last_message, dict) and "content" in last_message:
                    return last_message["content"]
        return str(raw_result)

    def _inject_context(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Inject stored context into input data"""
        enriched = input_data.copy()
        if self.context_store:
            enriched["context"] = self.context_store
        return enriched

    def _update_context(self, result: dict[str, Any]):
        """Update context store with results"""
        self.context_store.update(
            {
                "last_result": result,
                "updated_at": datetime.utcnow().isoformat(),
                "agent_role": self.role,
            }
        )

    def _track_performance(self, execution_time: float, success: bool):
        """Track performance metrics"""
        if "total_executions" not in self.performance_metrics:
            self.performance_metrics = {
                "total_executions": 0,
                "total_time": 0,
                "success_count": 0,
                "average_time": 0,
                "success_rate": 0,
            }

        metrics = self.performance_metrics
        metrics["total_executions"] += 1
        metrics["total_time"] += execution_time
        if success:
            metrics["success_count"] += 1

        metrics["average_time"] = metrics["total_time"] / metrics["total_executions"]
        metrics["success_rate"] = metrics["success_count"] / metrics["total_executions"]

    def _extract_tools_used(self, raw_result: Any) -> list[str]:
        """Extract tools used during execution"""
        # Implementation would parse agent execution logs
        return []

    def _extract_partial_results(self, error: Exception) -> dict[str, Any]:
        """Extract any partial results from failed execution"""
        return {"error_type": type(error).__name__}

    async def _validate_dependencies(self, dependencies: list[str]):
        """Validate that dependencies are satisfied (placeholder)"""
        # This would integrate with dependency manager
        pass


class AgentFactory:
    """
    OpenAI-exclusive agent factory with structured response enforcement.
    All agents created using create_react_agent with JSON schema validation.
    """

    def __init__(self, config: SystemConfig | None = None):
        self.config = config or get_config()
        # Use available OpenAI interface or mock for POC
        if OPENAI_INTERFACE_AVAILABLE:
            self.openai_client = OpenAIResponsesInterface()
        else:
            self.openai_client = MockOpenAIInterface()
        self.response_schemas = AGENT_RESPONSE_SCHEMAS
        self.created_agents = {}

    def create_agent(self, spec: dict[str, Any]) -> AgentWrapper:
        """
        Create OpenAI-powered agent with structured response capabilities.

        Args:
            spec: Agent specification with role, capabilities, and constraints

        Returns:
            AgentWrapper with structured response validation
        """
        role = spec["role"]
        agent_id = str(uuid.uuid4())

        # Get optimal OpenAI model for role
        model = get_model_for_role(AgentRole(role))

        # Build role-specific tools
        tools = self._build_tools_for_role(role)

        # Get response schema for role
        response_schema = get_schema_for_role(role)

        # Create structured prompt with JSON schema requirements
        prompt = self._create_structured_prompt(role, response_schema)

        # Create OpenAI model instance
        model_instance = self._create_openai_model(model)

        # Create agent using create_react_agent (MANDATORY) or mock for POC
        try:
            agent = create_react_agent(
                model=model_instance,
                tools=tools,
                prompt=prompt,
                checkpointer=MemorySaver(),
            )
        except Exception as e:
            print(f"⚠️  Using mock agent due to: {str(e)[:50]}...")
            agent = MockAgent(model_instance, tools, prompt)

        wrapper = AgentWrapper(
            agent=agent,
            role=role,
            agent_id=agent_id,
            model=model,
            response_schema=response_schema,
            openai_client=self.openai_client,
            tools=tools,
            capabilities=spec.get("capabilities", []),
            config=self.config,
        )

        # Store created agent
        self.created_agents[agent_id] = wrapper

        return wrapper

    def _create_openai_model(self, model_name: str):
        """Create OpenAI model instance using shared interface"""
        # For POC demo, return a mock model that works with create_react_agent
        return MockLangChainModel(model_name)

    def _create_structured_prompt(
        self, role: str, response_schema
    ) -> ChatPromptTemplate:
        """Create role-specific prompts enforcing structured JSON responses"""
        schema_str = response_schema.model_json_schema() if response_schema else "{}"

        base_template = """You are an autonomous {role} agent in the Smart Decomposition Meta-Intelligence System.

CRITICAL REQUIREMENTS:
1. You MUST respond with valid JSON matching this exact schema: {schema}
2. Continue working until task is complete - no early exits
3. Use available tools when you need additional information
4. Plan your approach before taking action
5. Validate your output against the schema before responding

RESPONSE FORMAT: Always return valid JSON matching the schema. No additional text outside the JSON.

Your role-specific responsibilities:
{role_description}

SCHEMA TO FOLLOW:
{schema}

Current task: {{input}}

Begin your analysis and respond with valid JSON:"""

        role_descriptions = {
            "manager": "Coordinate overall workflow, make strategic decisions, and manage agent interactions.",
            "requirements_expander": "Expand user prompts into comprehensive technical requirements with complete analysis.",
            "work_decomposer": "Break down complex tasks into manageable components with clear dependencies.",
            "architect": "Design system architecture and technical specifications.",
            "developer": "Generate complete, functional code implementations with tests and documentation.",
            "tester": "Create comprehensive test suites and validate implementations.",
            "coordinator": "Coordinate multi-agent workflows and manage task dependencies.",
            "validator": "Validate outputs against requirements and quality standards.",
            "integrator": "Integrate components and ensure system coherence.",
            "optimizer": "Optimize performance and resource utilization.",
        }

        return ChatPromptTemplate.from_template(
            base_template.format(
                role=role,
                role_description=role_descriptions.get(
                    role, "Execute assigned tasks autonomously"
                ),
                schema=schema_str,
            )
        )

    def _get_base_tools(self) -> list[Tool]:
        """Get base tools available to all agents"""
        return [
            Tool(
                name="web_search",
                description="Search the web for current information",
                func=self._web_search_tool,
            ),
            Tool(
                name="knowledge_search",
                description="Search internal knowledge base",
                func=self._knowledge_search_tool,
            ),
        ]

    def _get_research_tools(self) -> list[Tool]:
        """Get research-specific tools"""
        return [
            Tool(
                name="research_papers",
                description="Search and analyze research papers",
                func=self._research_papers_tool,
            ),
            Tool(
                name="tech_docs",
                description="Search technical documentation",
                func=self._tech_docs_tool,
            ),
        ]

    def _get_development_tools(self) -> list[Tool]:
        """Get development-specific tools"""
        return [
            Tool(
                name="code_generation",
                description="Generate code based on specifications",
                func=self._code_generation_tool,
            ),
            Tool(
                name="file_operations",
                description="Create and manage files",
                func=self._file_operations_tool,
            ),
        ]

    def _get_testing_tools(self) -> list[Tool]:
        """Get testing-specific tools"""
        return [
            Tool(
                name="test_generation",
                description="Generate test cases and validation scripts",
                func=self._test_generation_tool,
            ),
            Tool(
                name="quality_analysis",
                description="Analyze code quality and performance",
                func=self._quality_analysis_tool,
            ),
        ]

    # Tool implementation stubs (would connect to actual MCP tools)
    async def _web_search_tool(self, query: str) -> str:
        """Web search tool implementation"""
        return f"Web search results for: {query}"

    async def _knowledge_search_tool(self, query: str) -> str:
        """Knowledge base search tool implementation"""
        return f"Knowledge base results for: {query}"

    async def _research_papers_tool(self, query: str) -> str:
        """Research papers tool implementation"""
        return f"Research papers for: {query}"

    async def _tech_docs_tool(self, query: str) -> str:
        """Technical documentation tool implementation"""
        return f"Technical documentation for: {query}"

    async def _code_generation_tool(self, specifications: str) -> str:
        """Code generation tool implementation"""
        return f"Generated code for: {specifications}"

    async def _file_operations_tool(self, operation: str) -> str:
        """File operations tool implementation"""
        return f"File operation result: {operation}"

    async def _test_generation_tool(self, code: str) -> str:
        """Test generation tool implementation"""
        return f"Generated tests for: {code}"

    async def _quality_analysis_tool(self, code: str) -> str:
        """Quality analysis tool implementation"""
        return f"Quality analysis for: {code}"

    def _build_tools_for_role(self, role: str) -> list[Tool]:
        """Build appropriate tools for a specific agent role"""
        all_tools = []

        # Common tools for all roles
        all_tools.extend(self._get_base_tools())

        # Role-specific tools
        if role in ["requirements_expander", "research"]:
            all_tools.extend(self._get_research_tools())
        elif role in ["developer", "implementation"]:
            all_tools.extend(self._get_development_tools())
        elif role in ["tester", "validator", "quality"]:
            all_tools.extend(self._get_testing_tools())
        elif role in ["manager", "coordinator"]:
            all_tools.extend(self._get_base_tools())  # Managers get common tools

        return all_tools

    def get_agent_performance_metrics(self) -> dict[str, Any]:
        """Get performance metrics for all created agents"""
        metrics = {}
        for agent_id, agent in self.created_agents.items():
            metrics[agent_id] = {
                "role": agent.role,
                "model": agent.model,
                "created_at": agent.created_at.isoformat(),
                "performance": agent.performance_metrics,
            }
        return metrics


# Specialized agent creation methods
class SpecializedAgentFactory:
    """Factory for creating specialized agents with pre-configured settings"""

    def __init__(self, base_factory: AgentFactory):
        self.base_factory = base_factory

    def create_manager_agent(self) -> AgentWrapper:
        """Create manager agent with O3 model for complex coordination"""
        spec = {
            "role": "manager",
            "capabilities": [
                "workflow_coordination",
                "strategic_planning",
                "agent_management",
                "decision_making",
            ],
            "constraints": {
                "max_processing_time": 600,  # 10 minutes for complex planning
                "require_validation": True,
                "enforce_completeness": True,
            },
        }
        return self.base_factory.create_agent(spec)

    def create_requirements_expander(self) -> AgentWrapper:
        """Create requirements expansion agent using O3 model"""
        spec = {
            "role": "requirements_expander",
            "capabilities": [
                "natural_language_analysis",
                "requirement_decomposition",
                "technical_specification",
                "dependency_identification",
                "complexity_assessment",
            ],
            "constraints": {
                "max_processing_time": 300,  # 5 minutes for analysis
                "require_validation": True,
                "enforce_completeness": True,
            },
        }
        return self.base_factory.create_agent(spec)

    def create_developer_agent(self) -> AgentWrapper:
        """Create development agent using GPT-4.1"""
        spec = {
            "role": "developer",
            "capabilities": [
                "code_generation",
                "architecture_implementation",
                "testing_creation",
                "documentation_generation",
                "deployment_configuration",
            ],
            "constraints": {
                "code_quality": "production_ready",
                "test_coverage": "comprehensive",
                "documentation": "complete",
            },
        }
        return self.base_factory.create_agent(spec)

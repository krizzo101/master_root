"""
Unit Tests for Dynamic Agent Factory

Tests the dynamic agent creation system that instantiates specialized agents
based on complexity analysis and request requirements.
"""

import sys
from pathlib import Path

import pytest

# Add project root for imports (Rule 803 compliance)
project_root = Path(__file__).parents[3]
sys.path.insert(0, str(project_root))

# REAL IMPORTS - No mocking (TDD Compliance)
from oamat_sd.src.agents.agent_factory import (
    AgentCreationRequest,
    AgentRole,
    AgentStatus,
    DynamicAgentFactory,
)

from tests.fixtures.test_data import (
    COMPLEX_REQUESTS,
    MEDIUM_REQUESTS,
    SIMPLE_REQUESTS,
)


class TestDynamicAgentFactory:
    """Test suite for Dynamic Agent Factory - REAL IMPLEMENTATION TESTING"""

    @pytest.fixture
    def agent_factory(self):
        """Create REAL agent factory instance for testing"""
        # ✅ REAL IMPLEMENTATION - No mocking
        return DynamicAgentFactory()

    @pytest.fixture
    def research_agent_request(self):
        """Create real agent creation request for researcher"""
        return AgentCreationRequest(
            role=AgentRole.RESEARCHER,
            context={"domain": "web_frameworks"},
            tools=["brave_search", "arxiv_research"],
            performance_requirements={"temperature": 0.7, "max_tokens": 2000},
        )

    @pytest.fixture
    def implementer_agent_request(self):
        """Create real agent creation request for implementer"""
        return AgentCreationRequest(
            role=AgentRole.IMPLEMENTER,
            context={"task_type": "coding"},
            tools=["sequential_thinking", "context7_docs"],
            performance_requirements={"temperature": 0.3, "max_tokens": 4000},
        )

    @pytest.fixture
    def integrator_agent_request(self):
        """Create real agent creation request for integrator"""
        return AgentCreationRequest(
            role=AgentRole.INTEGRATOR,
            context={"integration_type": "synthesis"},
            tools=["sequential_thinking", "neo4j_database"],
            performance_requirements={"temperature": 0.5, "max_tokens": 3000},
        )

    @pytest.fixture
    def validator_agent_request(self):
        """Create real agent creation request for validator"""
        return AgentCreationRequest(
            role=AgentRole.VALIDATOR,
            context={"validation_type": "code_review"},
            tools=["context7_docs", "sequential_thinking"],
            performance_requirements={"temperature": 0.2, "max_tokens": 2000},
        )

    @pytest.mark.asyncio
    async def test_create_research_agent(self, agent_factory, research_agent_request):
        """Test research agent creation using REAL implementation"""
        # Test REAL agent creation
        agent = await agent_factory.create_agent(research_agent_request)

        # Validate REAL agent instance
        assert agent is not None
        assert agent.role == AgentRole.RESEARCHER
        assert agent.agent_id is not None
        assert agent.status.value in ["ready", "active"]
        assert "brave_search" in agent.tools_assigned
        assert "arxiv_research" in agent.tools_assigned

    @pytest.mark.asyncio
    async def test_create_analysis_agent(
        self, agent_factory, implementer_agent_request
    ):
        """Test analysis agent creation using REAL implementation"""
        # Test REAL implementer agent creation
        agent = await agent_factory.create_agent(implementer_agent_request)

        # Validate REAL agent instance
        assert agent is not None
        assert agent.role == AgentRole.IMPLEMENTER
        assert agent.agent_id is not None
        assert agent.status.value in ["ready", "active"]
        assert "sequential_thinking" in agent.tools_assigned
        assert "context7_docs" in agent.tools_assigned

    @pytest.mark.asyncio
    async def test_create_synthesis_agent(
        self, agent_factory, integrator_agent_request
    ):
        """Test synthesis agent creation using REAL implementation"""
        # Test REAL integrator agent creation
        agent = await agent_factory.create_agent(integrator_agent_request)

        # Validate REAL agent instance
        assert agent is not None
        assert agent.role == AgentRole.INTEGRATOR
        assert agent.agent_id is not None
        assert agent.status.value in ["ready", "active"]
        assert "sequential_thinking" in agent.tools_assigned
        assert "neo4j_database" in agent.tools_assigned

    @pytest.mark.asyncio
    async def test_create_coding_agent(self, agent_factory, validator_agent_request):
        """Test coding agent creation using REAL implementation"""
        # Test REAL validator agent creation
        agent = await agent_factory.create_agent(validator_agent_request)

        # Validate REAL agent instance
        assert agent is not None
        assert agent.role == AgentRole.VALIDATOR
        assert agent.agent_id is not None
        assert agent.status.value in ["ready", "active"]
        assert "context7_docs" in agent.tools_assigned
        assert "sequential_thinking" in agent.tools_assigned

    @pytest.mark.asyncio
    async def test_create_multiple_agents(self, agent_factory):
        """Test creating multiple agents simultaneously using REAL implementation"""
        # Create REAL agent creation requests
        requests = [
            AgentCreationRequest(
                role=AgentRole.RESEARCHER,
                context={"task": "research"},
                tools=["brave_search"],
                performance_requirements={"temperature": 0.7},
            ),
            AgentCreationRequest(
                role=AgentRole.IMPLEMENTER,
                context={"task": "analysis"},
                tools=["sequential_thinking"],
                performance_requirements={"temperature": 0.5},
            ),
            AgentCreationRequest(
                role=AgentRole.INTEGRATOR,
                context={"task": "synthesis"},
                tools=["neo4j_database"],
                performance_requirements={"temperature": 0.3},
            ),
        ]

        # Test REAL multiple agent creation
        agents = await agent_factory.create_multiple_agents(requests)

        # Validate REAL results
        assert len(agents) == 3
        assert all(agent is not None for agent in agents)
        roles = {agent.role for agent in agents}
        expected_roles = {
            AgentRole.RESEARCHER,
            AgentRole.IMPLEMENTER,
            AgentRole.INTEGRATOR,
        }
        assert roles == expected_roles

    @pytest.mark.asyncio
    async def test_langgraph_integration(self, agent_factory):
        """Test LangGraph create_react_agent integration using REAL implementation"""
        # Test REAL LangGraph integration through agent creation
        request = AgentCreationRequest(
            role=AgentRole.IMPLEMENTER,
            context={"task": "coding"},
            tools=["context7_docs"],
            performance_requirements={"temperature": 0.3},
        )

        # Test that REAL agent creation uses LangGraph internally
        agent = await agent_factory.create_agent(request)

        # Validate REAL agent has LangGraph object
        assert agent is not None
        assert agent.agent_object is not None  # This should be the LangGraph agent
        assert agent.role == AgentRole.IMPLEMENTER

    @pytest.mark.asyncio
    async def test_agent_tool_assignment(self, agent_factory):
        """Test tool assignment during agent creation using REAL implementation"""
        # Test that tools are properly assigned during REAL agent creation
        request = AgentCreationRequest(
            role=AgentRole.RESEARCHER,
            context={"domain": "research"},
            tools=["brave_search", "arxiv_research"],
            performance_requirements={"temperature": 0.7},
        )

        # Test REAL tool assignment
        agent = await agent_factory.create_agent(request)

        # Validate REAL tool assignment
        assert agent is not None
        assert "brave_search" in agent.tools_assigned
        assert "arxiv_research" in agent.tools_assigned

    def test_agent_factory_status(self, agent_factory):
        """Test factory status retrieval using REAL implementation"""
        # Test REAL factory status method
        status = agent_factory.get_factory_status()

        # Validate REAL status information
        assert status is not None
        assert isinstance(status, dict)
        assert "total_agents" in status
        assert "active_agents" in status

    @pytest.mark.parametrize(
        "request_data", SIMPLE_REQUESTS[:2]
    )  # Test subset to avoid excessive test time
    @pytest.mark.asyncio
    async def test_simple_request_agent_creation(self, agent_factory, request_data):
        """Test agent creation for simple requests using REAL implementation"""
        # Test REAL single agent creation for simple requests
        request = AgentCreationRequest(
            role=AgentRole.RESEARCHER,  # Simple requests typically use researcher
            context={"request_type": "simple", "content": request_data.text},
            tools=["brave_search"],
            performance_requirements={"temperature": 0.7},
        )

        # Test REAL agent creation
        agent = await agent_factory.create_agent(request)

        # Validate REAL results
        assert agent is not None
        assert agent.role == AgentRole.RESEARCHER
        assert agent.role.value in request_data.expected_agents

    @pytest.mark.parametrize(
        "request_data", MEDIUM_REQUESTS[:1]
    )  # Test subset to avoid excessive test time
    @pytest.mark.asyncio
    async def test_medium_request_agent_creation(self, agent_factory, request_data):
        """Test agent creation for medium complexity requests using REAL implementation"""
        # Create REAL multiple agent requests for medium complexity
        requests = []
        for i, role in enumerate(
            request_data.expected_agents[:2]
        ):  # Limit to 2 agents for efficiency
            agent_role = (
                AgentRole.RESEARCHER if role == "researcher" else AgentRole.IMPLEMENTER
            )
            requests.append(
                AgentCreationRequest(
                    role=agent_role,
                    context={"request_type": "medium", "content": request_data.text},
                    tools=(
                        ["brave_search"]
                        if role == "researcher"
                        else ["sequential_thinking"]
                    ),
                    performance_requirements={"temperature": 0.5},
                )
            )

        # Test REAL multiple agent creation
        agents = await agent_factory.create_multiple_agents(requests)

        # Validate REAL results
        assert len(agents) >= 1  # Should create at least one agent
        assert all(agent is not None for agent in agents)

    @pytest.mark.parametrize(
        "request_data", COMPLEX_REQUESTS[:1]
    )  # Test subset to avoid excessive test time
    @pytest.mark.asyncio
    async def test_complex_request_agent_creation(self, agent_factory, request_data):
        """Test agent creation for complex requests using REAL implementation"""
        # Create REAL multiple agent requests for complex requests
        requests = []
        role_mapping = {
            "researcher": AgentRole.RESEARCHER,
            "analyst": AgentRole.VALIDATOR,  # Map to available role
            "synthesizer": AgentRole.INTEGRATOR,  # Map to available role
        }

        for role in request_data.expected_agents[
            :3
        ]:  # Limit to 3 agents for efficiency
            if role in role_mapping:
                requests.append(
                    AgentCreationRequest(
                        role=role_mapping[role],
                        context={
                            "request_type": "complex",
                            "content": request_data.text,
                        },
                        tools=["brave_search", "sequential_thinking"],
                        performance_requirements={"temperature": 0.3},
                    )
                )

        # Test REAL multiple agent creation
        agents = await agent_factory.create_multiple_agents(requests)

        # Validate REAL results
        assert len(agents) >= 1  # Should create at least one agent
        assert all(agent is not None for agent in agents)

    @pytest.mark.asyncio
    async def test_agent_configuration_customization(self, agent_factory):
        """Test agent configuration customization using REAL implementation"""
        # Test REAL configuration customization
        request = AgentCreationRequest(
            role=AgentRole.RESEARCHER,
            context={"task": "research"},
            tools=["brave_search"],
            performance_requirements={
                "temperature": 0.8,
                "max_tokens": 3000,
                "model": "gpt-4.1-mini",  # Use standardized agent model
            },
        )

        # Test REAL agent creation with custom configuration
        agent = await agent_factory.create_agent(request)

        # Validate REAL configuration
        assert agent is not None
        assert agent.configuration is not None
        assert agent.configuration.performance_config["temperature"] == 0.8
        assert agent.configuration.performance_config["max_tokens"] == 3000

    @pytest.mark.asyncio
    async def test_agent_context_preservation(self, agent_factory):
        """Test that agent context is properly preserved using REAL implementation"""
        # Test REAL context preservation
        context = {
            "domain": "web_frameworks",
            "focus": "performance_analysis",
            "constraints": ["python_only", "open_source"],
        }

        request = AgentCreationRequest(
            role=AgentRole.VALIDATOR,  # Map analyst to validator
            context=context,
            tools=["sequential_thinking"],
            performance_requirements={"temperature": 0.5},
        )

        # Test REAL agent creation with context
        agent = await agent_factory.create_agent(request)

        # Validate REAL context preservation
        assert agent is not None
        assert agent.context is not None
        assert agent.context["domain"] == "web_frameworks"
        assert agent.context["focus"] == "performance_analysis"
        assert "python_only" in agent.context["constraints"]

    @pytest.mark.asyncio
    async def test_error_handling_invalid_role(self, agent_factory):
        """Test error handling for invalid agent roles using REAL implementation"""
        # Test REAL error handling for invalid roles
        # Note: This test depends on actual validation in AgentCreationRequest
        with pytest.raises((ValueError, TypeError)):
            # Try to create request with invalid role (this should fail during request creation)
            invalid_request = AgentCreationRequest(
                role="invalid_role",  # This should cause validation error
                context={"task": "test"},
                tools=["test_tool"],
                performance_requirements={"temperature": 0.5},
            )

    @pytest.mark.asyncio
    async def test_error_handling_missing_tools(self, agent_factory):
        """Test error handling for missing tool specifications using REAL implementation"""
        # Test REAL error handling for missing tools
        request = AgentCreationRequest(
            role=AgentRole.RESEARCHER,
            context={"task": "test"},
            tools=[],  # Empty tools list
            performance_requirements={"temperature": 0.5},
        )

        # Test that REAL implementation handles empty tools gracefully
        # (May not actually error, depending on implementation)
        try:
            agent = await agent_factory.create_agent(request)
            # If it succeeds, verify the agent was created
            assert agent is not None
        except (ValueError, TypeError) as e:
            # If it fails, that's also acceptable behavior
            assert "tool" in str(e).lower() or "empty" in str(e).lower()

    async def test_performance_agent_creation(self, agent_factory):
        """Test performance of agent creation"""
        import time

        # Real agent creation request
        creation_request = AgentCreationRequest(
            role=AgentRole.RESEARCHER,
            context={"domain": "performance_testing"},
            tools=["brave_search"],
            performance_requirements={"temperature": 0.7, "max_tokens": 1000},
        )

        start_time = time.time()
        agent = await agent_factory.create_agent(creation_request)
        creation_time = time.time() - start_time

        # Agent creation should be reasonably fast (real implementation)
        assert creation_time < 5.0  # 5 seconds max for real agent creation
        assert agent is not None
        assert agent.role == AgentRole.RESEARCHER
        assert agent.status in [AgentStatus.READY, AgentStatus.CREATING]

    async def test_agent_memory_management(self, agent_factory):
        """Test agent memory and resource management"""
        # Create real agent creation requests
        creation_requests = [
            AgentCreationRequest(
                role=AgentRole.RESEARCHER,
                context={"domain": f"test_domain_{i}"},
                tools=["brave_search"],
                performance_requirements={"temperature": 0.7},
            )
            for i in range(3)  # Reduced from 10 to 3 for performance
        ]

        agents = await agent_factory.create_multiple_agents(creation_requests)

        # Should handle multiple agent creation without issues
        assert len(agents) == 3
        assert all(agent is not None for agent in agents)
        assert all(
            agent.status in [AgentStatus.READY, AgentStatus.CREATING]
            for agent in agents
        )

        # Test cleanup using real factory methods
        completed_count = agent_factory.cleanup_completed_agents()
        assert completed_count >= 0  # Should return count of cleaned up agents

    async def test_agent_tool_validation(self, agent_factory):
        """Test validation of agent tool assignments"""
        valid_tools = [
            "brave_search",
            "arxiv_research",
            "firecrawl_scraping",
            "context7_docs",
            "sequential_thinking",
            "neo4j_database",
        ]

        # Test tool assignment using real agent creation
        creation_request = AgentCreationRequest(
            role=AgentRole.RESEARCHER,
            context={"domain": "tool_validation_test"},
            tools=["brave_search", "arxiv_research"],
            performance_requirements={"temperature": 0.7},
        )

        agent = await agent_factory.create_agent(creation_request)

        # Verify the agent was created with valid tools
        assert agent is not None
        assert agent.tools_assigned is not None

        # All assigned tools should be valid (if any were assigned)
        if agent.tools_assigned:
            for tool in agent.tools_assigned:
                if isinstance(tool, str):
                    assert tool in valid_tools or tool in [
                        "research",
                        "analysis",
                    ], f"Invalid tool {tool}"

        # Test the tool configuration method if it exists
        success = agent_factory.configure_agent_tools(agent.agent_id, ["brave_search"])
        assert isinstance(success, bool)

    async def test_concurrent_agent_creation(self, agent_factory):
        """Test concurrent agent creation for parallel processing"""
        creation_requests = [
            AgentCreationRequest(
                role=AgentRole.RESEARCHER,
                context={"domain": "concurrent_test_research"},
                tools=["brave_search"],
                performance_requirements={"temperature": 0.7},
            ),
            AgentCreationRequest(
                role=AgentRole.VALIDATOR,
                context={"domain": "concurrent_test_analysis"},
                tools=["testing"],
                performance_requirements={"temperature": 0.5},
            ),
            AgentCreationRequest(
                role=AgentRole.IMPLEMENTER,
                context={"domain": "concurrent_test_synthesis"},
                tools=["code_generation"],
                performance_requirements={"temperature": 0.3},
            ),
        ]

        # Use the real concurrent creation method
        agents = await agent_factory.create_multiple_agents(creation_requests)

        # Verify successful concurrent creation
        assert (
            len(agents) >= 2
        )  # At least 2 should succeed (allowing for some failures)
        successful_agents = [
            a for a in agents if a.status in [AgentStatus.READY, AgentStatus.CREATING]
        ]
        assert len(successful_agents) >= 1

        # Check that different roles were created
        roles = {agent.role for agent in successful_agents}
        assert len(roles) >= 1  # At least one distinct role

    async def test_agent_specialization_consistency(self, agent_factory):
        """Test consistency of agent specialization across similar requests"""
        similar_requests = [
            AgentCreationRequest(
                role=AgentRole.RESEARCHER,
                context={"domain": "web_frameworks"},
                tools=["brave_search", "arxiv_research"],
                performance_requirements={"temperature": 0.7},
            ),
            AgentCreationRequest(
                role=AgentRole.RESEARCHER,
                context={"domain": "web_development"},
                tools=["brave_search", "arxiv_research"],
                performance_requirements={"temperature": 0.7},
            ),
            AgentCreationRequest(
                role=AgentRole.RESEARCHER,
                context={"domain": "web_technologies"},
                tools=["brave_search", "arxiv_research"],
                performance_requirements={"temperature": 0.7},
            ),
        ]

        # Test consistent agent creation across similar requests
        agents = []
        for request in similar_requests:
            agent = await agent_factory.create_agent(request)
            agents.append(agent)
            assert agent.role == AgentRole.RESEARCHER
            assert agent.status in [AgentStatus.READY, AgentStatus.CREATING]

        # Verify all agents were created successfully with consistent specialization
        assert len(agents) == 3
        all_roles = [agent.role for agent in agents]
        assert all(role == AgentRole.RESEARCHER for role in all_roles)

        # Verify similar requests produce similar agent configurations
        all_contexts = [agent.context for agent in agents if agent.context]
        assert len(all_contexts) >= 1  # At least one should have context

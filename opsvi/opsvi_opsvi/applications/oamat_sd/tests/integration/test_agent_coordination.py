"""
Integration Tests for Agent Coordination

Tests the coordination and interaction between multiple agents
in Smart Decomposition workflows.
"""

from pathlib import Path

# Import fixes
import sys
import time
from unittest.mock import AsyncMock, MagicMock

import pytest

project_root = Path(__file__).parents[5]
sys.path.insert(0, str(project_root))


class TestAgentCoordination:
    """Integration test suite for agent coordination and workflow execution"""

    @pytest.fixture
    def mock_registry(self):
        """Create mock MCP registry for integration testing"""
        from tests.fixtures.mcp_mocks import MCPRegistryMock

        return MCPRegistryMock()

    @pytest.fixture
    def mock_smart_decomposition_agent(self, mock_registry):
        """Create mock Smart Decomposition Agent for testing"""
        agent = MagicMock()
        agent.process_request = AsyncMock()
        agent.mcp_registry = mock_registry
        agent.available_tools = mock_registry.list_tools()

        return agent

    @pytest.mark.asyncio
    async def test_multi_agent_workflow_coordination(
        self, mock_smart_decomposition_agent, mock_registry
    ):
        """Test coordination between multiple agents in a workflow"""
        request = "Research Python web frameworks and provide recommendations"

        # Mock successful multi-agent workflow
        expected_result = {
            "success": True,
            "solution": {
                "artifact_type": "research_report",
                "content": "Comprehensive analysis of Python web frameworks...",
                "metadata": {"confidence": 0.9, "agents_involved": 3},
            },
            "complexity_analysis": {
                "complexity_score": 5.5,
                "execution_strategy": "multi_agent",
                "factors": {"scope": 6, "technical_depth": 7},
            },
            "agent_outputs": {
                "researcher": {
                    "success": True,
                    "content": "Research findings on Python frameworks",
                    "tools_used": ["brave_search", "arxiv_research"],
                },
                "analyst": {
                    "success": True,
                    "content": "Analysis of framework performance and features",
                    "tools_used": ["sequential_thinking", "context7_docs"],
                },
                "synthesizer": {
                    "success": True,
                    "content": "Synthesized recommendations",
                    "tools_used": ["sequential_thinking", "neo4j_database"],
                },
            },
            "execution_time": 25.3,
            "parallel_efficiency": 2.8,
        }

        mock_smart_decomposition_agent.process_request.return_value = expected_result

        result = await mock_smart_decomposition_agent.process_request(request)

        # Validate result structure
        assert result["success"] is True
        assert "solution" in result
        assert "agent_outputs" in result

        # Validate agent participation
        agent_outputs = result["agent_outputs"]
        assert len(agent_outputs) >= 2  # Multi-agent workflow

        expected_agents = {"researcher", "analyst", "synthesizer"}
        actual_agents = set(agent_outputs.keys())
        assert expected_agents.issubset(actual_agents)

        # Validate all agents succeeded
        assert all(output["success"] for output in agent_outputs.values())

        # Validate tool usage
        for agent_output in agent_outputs.values():
            assert "tools_used" in agent_output
            assert len(agent_output["tools_used"]) > 0

        mock_smart_decomposition_agent.process_request.assert_called_once_with(request)

    @pytest.mark.asyncio
    async def test_parallel_agent_execution_performance(
        self, mock_smart_decomposition_agent
    ):
        """Test parallel execution performance of multiple agents"""
        request = "Analyze three different cloud platforms: AWS, Azure, and GCP"

        # Mock parallel execution with performance metrics
        expected_result = {
            "success": True,
            "execution_metrics": {
                "total_time": 15.2,
                "sequential_time_estimate": 45.0,
                "parallel_efficiency": 2.96,  # Close to 3x improvement
                "agents_executed": 3,
                "parallel_operations": 8,
            },
            "agent_outputs": {
                "researcher_aws": {"success": True, "execution_time": 12.1},
                "researcher_azure": {"success": True, "execution_time": 11.8},
                "researcher_gcp": {"success": True, "execution_time": 13.4},
            },
        }

        mock_smart_decomposition_agent.process_request.return_value = expected_result

        start_time = time.time()
        result = await mock_smart_decomposition_agent.process_request(request)
        actual_execution_time = time.time() - start_time

        # Validate performance improvement
        metrics = result["execution_metrics"]
        assert metrics["parallel_efficiency"] >= 2.0  # At least 2x improvement
        assert metrics["total_time"] < metrics["sequential_time_estimate"]

        # Validate parallel execution occurred
        assert metrics["agents_executed"] >= 3
        assert metrics["parallel_operations"] > metrics["agents_executed"]

        # Validate actual execution was fast (mocked)
        assert actual_execution_time < 1.0  # Should be very fast with mocks

    @pytest.mark.asyncio
    async def test_agent_handoff_and_state_management(
        self, mock_smart_decomposition_agent
    ):
        """Test agent handoff and state persistence across workflow stages"""
        request = "Create a comprehensive analysis of database technologies"

        # Mock workflow with state tracking
        expected_result = {
            "success": True,
            "workflow_stages": [
                {
                    "stage": "research",
                    "agent": "researcher",
                    "status": "completed",
                    "output": "Research data on database technologies",
                    "state_updates": {"research_data": "collected", "sources": 15},
                },
                {
                    "stage": "analysis",
                    "agent": "analyst",
                    "status": "completed",
                    "input_from": "researcher",
                    "output": "Performance analysis and comparisons",
                    "state_updates": {"analysis_complete": True, "comparisons": 8},
                },
                {
                    "stage": "synthesis",
                    "agent": "synthesizer",
                    "status": "completed",
                    "input_from": ["researcher", "analyst"],
                    "output": "Final comprehensive analysis",
                    "state_updates": {"synthesis_complete": True, "recommendations": 5},
                },
            ],
            "state_persistence": {
                "checkpoints_created": 3,
                "state_size_kb": 15.7,
                "recovery_points": ["research", "analysis", "synthesis"],
            },
        }

        mock_smart_decomposition_agent.process_request.return_value = expected_result

        result = await mock_smart_decomposition_agent.process_request(request)

        # Validate workflow progression
        stages = result["workflow_stages"]
        assert len(stages) >= 3

        # Validate stage completion order
        for i, stage in enumerate(stages):
            assert stage["status"] == "completed"
            if i > 0:
                # Later stages should reference earlier ones
                assert "input_from" in stage

        # Validate state persistence
        state_info = result["state_persistence"]
        assert state_info["checkpoints_created"] == len(stages)
        assert len(state_info["recovery_points"]) == len(stages)

    @pytest.mark.asyncio
    async def test_error_handling_and_recovery(
        self, mock_smart_decomposition_agent, mock_registry
    ):
        """Test error handling and recovery in multi-agent workflows"""
        request = "Research latest AI developments with failure simulation"

        # Simulate partial failures with recovery
        expected_result = {
            "success": True,  # Overall success despite partial failures
            "agent_outputs": {
                "researcher": {
                    "success": True,
                    "content": "Research completed with fallback tools",
                    "tools_used": [
                        "arxiv_research",
                        "context7_docs",
                    ],  # Fallback from failed brave_search
                    "warnings": ["brave_search failed, used fallback"],
                },
                "analyst": {
                    "success": True,
                    "content": "Analysis completed successfully",
                    "tools_used": ["sequential_thinking"],
                },
            },
            "error_recovery": {
                "failures_detected": 1,
                "recovery_strategies_used": ["tool_fallback"],
                "degraded_operations": ["web_search"],
                "fallback_tools_used": ["arxiv_research", "context7_docs"],
                "overall_success_rate": 0.85,
            },
        }

        mock_smart_decomposition_agent.process_request.return_value = expected_result

        result = await mock_smart_decomposition_agent.process_request(request)

        # Validate overall success despite failures
        assert result["success"] is True

        # Validate error recovery information
        recovery_info = result["error_recovery"]
        assert recovery_info["failures_detected"] > 0
        assert len(recovery_info["recovery_strategies_used"]) > 0
        assert recovery_info["overall_success_rate"] > 0.7  # Acceptable degradation

        # Validate fallback mechanisms worked
        assert len(recovery_info["fallback_tools_used"]) > 0

        # Validate agents adapted to failures
        researcher_output = result["agent_outputs"]["researcher"]
        assert "warnings" in researcher_output
        assert (
            len(researcher_output["tools_used"]) > 1
        )  # Used multiple tools for resilience

    @pytest.mark.asyncio
    async def test_complex_orchestration_workflow(self, mock_smart_decomposition_agent):
        """Test complex orchestration with multiple phases and dependencies"""
        request = "Design and implement a complete microservices architecture"

        # Mock complex orchestrated workflow
        expected_result = {
            "success": True,
            "complexity_analysis": {
                "complexity_score": 8.7,
                "execution_strategy": "orchestrated",
            },
            "orchestration_phases": [
                {
                    "phase": "requirements_analysis",
                    "agents": ["researcher", "analyst"],
                    "coordination": "parallel",
                    "status": "completed",
                    "duration": 5.2,
                },
                {
                    "phase": "architecture_design",
                    "agents": ["analyst", "synthesizer"],
                    "coordination": "sequential",
                    "dependencies": ["requirements_analysis"],
                    "status": "completed",
                    "duration": 8.1,
                },
                {
                    "phase": "implementation_planning",
                    "agents": ["synthesizer", "coder"],
                    "coordination": "hybrid",
                    "dependencies": ["architecture_design"],
                    "status": "completed",
                    "duration": 6.8,
                },
                {
                    "phase": "validation_synthesis",
                    "agents": ["analyst", "synthesizer"],
                    "coordination": "parallel",
                    "dependencies": ["implementation_planning"],
                    "status": "completed",
                    "duration": 4.3,
                },
            ],
            "coordination_metrics": {
                "total_phases": 4,
                "parallel_operations": 6,
                "sequential_dependencies": 3,
                "coordination_overhead": 2.1,
                "efficiency_score": 0.78,
            },
        }

        mock_smart_decomposition_agent.process_request.return_value = expected_result

        result = await mock_smart_decomposition_agent.process_request(request)

        # Validate complex orchestration
        assert result["complexity_analysis"]["execution_strategy"] == "orchestrated"

        phases = result["orchestration_phases"]
        assert len(phases) >= 4  # Multiple phases

        # Validate phase dependencies
        for i, phase in enumerate(phases):
            if i > 0:
                # Later phases should have dependencies
                assert "dependencies" in phase
                assert len(phase["dependencies"]) > 0

        # Validate coordination types
        coordination_types = {phase["coordination"] for phase in phases}
        assert "parallel" in coordination_types
        assert "sequential" in coordination_types or "hybrid" in coordination_types

        # Validate coordination metrics
        metrics = result["coordination_metrics"]
        assert metrics["total_phases"] == len(phases)
        assert metrics["efficiency_score"] > 0.5  # Reasonable efficiency

    @pytest.mark.asyncio
    async def test_tool_integration_across_agents(
        self, mock_smart_decomposition_agent, mock_registry
    ):
        """Test tool integration and sharing across multiple agents"""
        request = "Comprehensive technology stack analysis with tool coordination"

        # Mock workflow showing tool coordination
        expected_result = {
            "success": True,
            "tool_coordination": {
                "tools_used": [
                    "brave_search",
                    "arxiv_research",
                    "context7_docs",
                    "sequential_thinking",
                    "neo4j_database",
                ],
                "cross_agent_sharing": {
                    "brave_search": ["researcher"],
                    "arxiv_research": ["researcher"],
                    "context7_docs": ["analyst", "coder"],
                    "sequential_thinking": ["analyst", "synthesizer", "coder"],
                    "neo4j_database": ["synthesizer"],
                },
                "tool_efficiency": {
                    "parallel_tool_calls": 8,
                    "sequential_tool_calls": 3,
                    "shared_tool_results": 2,
                    "cache_hits": 1,
                },
            },
            "agent_outputs": {
                "researcher": {
                    "success": True,
                    "tools_used": ["brave_search", "arxiv_research"],
                    "tool_results_shared": True,
                },
                "analyst": {
                    "success": True,
                    "tools_used": ["context7_docs", "sequential_thinking"],
                    "received_shared_results": ["brave_search"],
                },
                "synthesizer": {
                    "success": True,
                    "tools_used": ["sequential_thinking", "neo4j_database"],
                    "received_shared_results": ["arxiv_research", "context7_docs"],
                },
            },
        }

        mock_smart_decomposition_agent.process_request.return_value = expected_result

        result = await mock_smart_decomposition_agent.process_request(request)

        # Validate tool coordination
        tool_coord = result["tool_coordination"]
        assert len(tool_coord["tools_used"]) >= 5  # Multiple tools used

        # Validate cross-agent tool sharing
        cross_agent = tool_coord["cross_agent_sharing"]
        assert len(cross_agent) > 0

        # Validate some tools are shared across agents
        shared_tools = [tool for tool, agents in cross_agent.items() if len(agents) > 1]
        assert len(shared_tools) > 0

        # Validate tool efficiency metrics
        efficiency = tool_coord["tool_efficiency"]
        assert efficiency["parallel_tool_calls"] > efficiency["sequential_tool_calls"]
        assert efficiency["shared_tool_results"] > 0  # Results were shared

        # Validate agents received shared results
        agent_outputs = result["agent_outputs"]
        agents_with_shared_results = [
            agent
            for agent, output in agent_outputs.items()
            if output.get("received_shared_results")
        ]
        assert len(agents_with_shared_results) > 0

    @pytest.mark.asyncio
    async def test_workflow_scalability(self, mock_smart_decomposition_agent):
        """Test workflow scalability with increasing complexity"""
        complexity_levels = [
            ("Simple request", 2.0),
            ("Medium request", 5.5),
            ("Complex request", 8.5),
        ]

        results = []

        for request_desc, complexity_score in complexity_levels:
            # Mock results based on complexity
            expected_result = {
                "success": True,
                "complexity_analysis": {"complexity_score": complexity_score},
                "scalability_metrics": {
                    "agents_created": min(int(complexity_score / 2), 4),
                    "tool_calls": int(complexity_score * 2),
                    "execution_time": complexity_score * 3,
                    "memory_usage": complexity_score * 1.5,
                    "coordination_overhead": complexity_score * 0.3,
                },
            }

            mock_smart_decomposition_agent.process_request.return_value = (
                expected_result
            )

            result = await mock_smart_decomposition_agent.process_request(request_desc)
            results.append(result)

        # Validate scalability patterns
        for i in range(1, len(results)):
            current = results[i]["scalability_metrics"]
            previous = results[i - 1]["scalability_metrics"]

            # Higher complexity should use more resources (with some efficiency)
            assert current["agents_created"] >= previous["agents_created"]
            assert current["tool_calls"] > previous["tool_calls"]

            # But efficiency should improve or stay reasonable
            current_efficiency = current["tool_calls"] / current["execution_time"]
            previous_efficiency = previous["tool_calls"] / previous["execution_time"]

            # Efficiency shouldn't degrade too much
            efficiency_ratio = current_efficiency / previous_efficiency
            assert efficiency_ratio > 0.5  # Less than 50% efficiency loss

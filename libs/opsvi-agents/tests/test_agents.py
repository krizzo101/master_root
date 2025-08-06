"""
Test suite for opsvi-agents library.

Comprehensive tests for agent orchestration components.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from opsvi_core.agents.base_agent import BaseAgent
from opsvi_core.exceptions import ValidationError, InitializationError

from opsvi_agents import (
    CrewAdapter,
    GraphAdapter,
    BaseOrchestrator,
    AgentRegistry,
)


class MockAgent(BaseAgent):
    """Mock agent for testing."""

    def __init__(self, agent_id: str = "test-agent", **kwargs):
        super().__init__(agent_id, **kwargs)
        self._active = False

    async def _initialize(self) -> None:
        """Initialize mock agent."""
        self._active = True

    async def _cleanup(self) -> None:
        """Cleanup mock agent."""
        self._active = False

    async def process(self, message: str) -> str:
        """Process message."""
        return f"processed: {message}"

    def is_active(self) -> bool:
        """Check if agent is active."""
        return self._active


class TestCrewAdapter:
    """Test CrewAdapter functionality."""

    @pytest.fixture
    def crew_adapter(self):
        """Create CrewAdapter instance for testing."""
        return CrewAdapter()

    @pytest.fixture
    def mock_agents(self):
        """Create mock agents for testing."""
        return [
            MockAgent("agent-1"),
            MockAgent("agent-2"),
        ]

    @pytest.mark.asyncio
    async def test_create_crew_success(self, crew_adapter, mock_agents):
        """Test successful crew creation."""
        # Activate agents
        for agent in mock_agents:
            await agent.activate()

        tasks = [
            {"id": "task-1", "description": "Test task 1"},
            {"id": "task-2", "description": "Test task 2"},
        ]

        result = await crew_adapter.create_crew("test-crew", mock_agents, tasks)

        assert result["id"] == "test-crew"
        assert result["status"] == "created"
        assert len(result["agents"]) == 2
        assert len(result["tasks"]) == 2
        assert result["agents"][0]["active"] is True

    @pytest.mark.asyncio
    async def test_create_crew_no_agents(self, crew_adapter):
        """Test crew creation with no agents."""
        with pytest.raises(ValidationError, match="At least one agent is required"):
            await crew_adapter.create_crew("test-crew", [], [{"task": "test"}])

    @pytest.mark.asyncio
    async def test_create_crew_no_tasks(self, crew_adapter, mock_agents):
        """Test crew creation with no tasks."""
        with pytest.raises(ValidationError, match="At least one task is required"):
            await crew_adapter.create_crew("test-crew", mock_agents, [])

    @pytest.mark.asyncio
    async def test_get_crew(self, crew_adapter, mock_agents):
        """Test getting crew information."""
        # Activate agents
        for agent in mock_agents:
            await agent.activate()

        tasks = [{"id": "task-1", "description": "Test task"}]
        await crew_adapter.create_crew("test-crew", mock_agents, tasks)

        crew_info = await crew_adapter.get_crew("test-crew")
        assert crew_info is not None
        assert crew_info["id"] == "test-crew"

        # Test non-existent crew
        assert await crew_adapter.get_crew("non-existent") is None

    @pytest.mark.asyncio
    async def test_delete_crew(self, crew_adapter, mock_agents):
        """Test crew deletion."""
        # Activate agents
        for agent in mock_agents:
            await agent.activate()

        tasks = [{"id": "task-1", "description": "Test task"}]
        await crew_adapter.create_crew("test-crew", mock_agents, tasks)

        # Delete existing crew
        assert await crew_adapter.delete_crew("test-crew") is True
        assert await crew_adapter.get_crew("test-crew") is None

        # Delete non-existent crew
        assert await crew_adapter.delete_crew("non-existent") is False


class TestGraphAdapter:
    """Test GraphAdapter functionality."""

    @pytest.fixture
    def graph_adapter(self):
        """Create GraphAdapter instance for testing."""
        return GraphAdapter()

    @pytest.mark.asyncio
    async def test_create_graph_success(self, graph_adapter):
        """Test successful graph creation."""
        nodes = [
            {"id": "node-1", "type": "start"},
            {"id": "node-2", "type": "process"},
            {"id": "node-3", "type": "end"},
        ]
        edges = [
            {"from": "node-1", "to": "node-2"},
            {"from": "node-2", "to": "node-3"},
        ]

        result = await graph_adapter.create_graph("test-graph", nodes, edges)

        assert result["id"] == "test-graph"
        assert result["status"] == "created"
        assert result["node_count"] == 3
        assert result["edge_count"] == 2

    @pytest.mark.asyncio
    async def test_create_graph_no_nodes(self, graph_adapter):
        """Test graph creation with no nodes."""
        with pytest.raises(ValidationError, match="At least one node is required"):
            await graph_adapter.create_graph("test-graph", [], [])

    @pytest.mark.asyncio
    async def test_create_graph_invalid_node(self, graph_adapter):
        """Test graph creation with invalid node."""
        nodes = [{"type": "start"}]  # Missing 'id'

        with pytest.raises(ValidationError, match="missing required 'id' field"):
            await graph_adapter.create_graph("test-graph", nodes, [])

    @pytest.mark.asyncio
    async def test_execute_graph(self, graph_adapter):
        """Test graph execution."""
        nodes = [{"id": "node-1", "type": "start"}]
        edges = []

        await graph_adapter.create_graph("test-graph", nodes, edges)

        input_data = {"test": "data"}
        result = await graph_adapter.execute_graph("test-graph", input_data)

        assert result["graph_id"] == "test-graph"
        assert result["input"] == input_data
        assert result["status"] == "completed"

    @pytest.mark.asyncio
    async def test_execute_nonexistent_graph(self, graph_adapter):
        """Test executing non-existent graph."""
        with pytest.raises(ValidationError, match="Graph .* not found"):
            await graph_adapter.execute_graph("non-existent", {})


class TestAgentRegistry:
    """Test AgentRegistry functionality."""

    @pytest.fixture
    def registry(self):
        """Create AgentRegistry instance for testing."""
        return AgentRegistry()

    def test_register_agent_type(self, registry):
        """Test agent type registration."""
        registry.register_agent_type(
            "mock_agent",
            MockAgent,
            "test_framework",
            {"description": "Test agent"}
        )

        types = registry.list_agent_types()
        assert len(types) == 1
        assert types[0]["type"] == "mock_agent"
        assert types[0]["framework"] == "test_framework"

    def test_register_duplicate_type(self, registry):
        """Test registering duplicate agent type."""
        registry.register_agent_type("mock_agent", MockAgent)

        with pytest.raises(ValidationError, match="already registered"):
            registry.register_agent_type("mock_agent", MockAgent)

    @pytest.mark.asyncio
    async def test_create_agent(self, registry):
        """Test agent creation."""
        registry.register_agent_type("mock_agent", MockAgent)

        agent = await registry.create_agent("mock_agent", "test-instance")

        assert isinstance(agent, MockAgent)
        assert agent.agent_id == "test-instance"
        assert agent.is_active()

    @pytest.mark.asyncio
    async def test_create_unknown_agent_type(self, registry):
        """Test creating agent with unknown type."""
        with pytest.raises(ValidationError, match="Unknown agent type"):
            await registry.create_agent("unknown_type", "test-instance")

    @pytest.mark.asyncio
    async def test_create_duplicate_agent_id(self, registry):
        """Test creating agent with duplicate ID."""
        registry.register_agent_type("mock_agent", MockAgent)
        await registry.create_agent("mock_agent", "test-instance")

        with pytest.raises(ValidationError, match="already exists"):
            await registry.create_agent("mock_agent", "test-instance")

    @pytest.mark.asyncio
    async def test_remove_agent(self, registry):
        """Test agent removal."""
        registry.register_agent_type("mock_agent", MockAgent)
        await registry.create_agent("mock_agent", "test-instance")

        assert registry.get_agent("test-instance") is not None

        # Remove agent
        assert await registry.remove_agent("test-instance") is True
        assert registry.get_agent("test-instance") is None

        # Remove non-existent agent
        assert await registry.remove_agent("non-existent") is False

    def test_get_stats(self, registry):
        """Test registry statistics."""
        stats = registry.get_stats()

        assert "total_types" in stats
        assert "total_instances" in stats
        assert "active_instances" in stats
        assert "frameworks" in stats

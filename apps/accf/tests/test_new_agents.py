"""
Tests for newly migrated agents.
"""

import pytest
from accf_agents import Settings
from accf_agents.agents import Task, MemoryAgent, CollaborationAgent


class TestMemoryAgent:
    """Test the MemoryAgent."""

    def test_memory_agent_creation(self):
        """Test that MemoryAgent can be created."""
        settings = Settings()
        agent = MemoryAgent("test-memory", settings)
        assert agent.name == "test-memory"

    def test_memory_agent_capabilities(self):
        """Test that MemoryAgent has correct capabilities."""
        settings = Settings()
        agent = MemoryAgent("test-memory", settings)
        capabilities = agent.get_capabilities()
        assert "memory_store" in capabilities
        assert "memory_retrieve" in capabilities
        assert "memory_answer" in capabilities

    @pytest.mark.asyncio
    async def test_memory_agent_store_and_retrieve(self):
        """Test that MemoryAgent can store and retrieve data."""
        settings = Settings()
        agent = MemoryAgent("test-memory", settings)

        # Store data
        store_task = Task(
            id="store-task",
            type="memory_store",
            parameters={"key": "test_key", "value": "test_value"},
        )

        store_result = await agent.execute(store_task)
        assert store_result.status == "success"
        assert store_result.data["stored"] is True

        # Retrieve data
        retrieve_task = Task(
            id="retrieve-task", type="memory_retrieve", parameters={"key": "test_key"}
        )

        retrieve_result = await agent.execute(retrieve_task)
        assert retrieve_result.status == "success"
        assert retrieve_result.data["value"] == "test_value"
        assert retrieve_result.data["found"] is True


class TestCollaborationAgent:
    """Test the CollaborationAgent."""

    def test_collaboration_agent_creation(self):
        """Test that CollaborationAgent can be created."""
        settings = Settings()
        agent = CollaborationAgent("test-collab", settings)
        assert agent.name == "test-collab"

    def test_collaboration_agent_capabilities(self):
        """Test that CollaborationAgent has correct capabilities."""
        settings = Settings()
        agent = CollaborationAgent("test-collab", settings)
        capabilities = agent.get_capabilities()
        assert "collaborate" in capabilities
        assert "add_collaborator" in capabilities
        assert "list_collaborators" in capabilities

    @pytest.mark.asyncio
    async def test_collaboration_agent_add_collaborator(self):
        """Test that CollaborationAgent can add collaborators."""
        settings = Settings()
        agent = CollaborationAgent("test-collab", settings)

        # Add collaborator
        add_task = Task(
            id="add-task",
            type="add_collaborator",
            parameters={"collaborator_name": "test_collaborator"},
        )

        add_result = await agent.execute(add_task)
        assert add_result.status == "success"
        assert add_result.data["added"] is True
        assert add_result.data["total_collaborators"] == 1

        # List collaborators
        list_task = Task(id="list-task", type="list_collaborators", parameters={})

        list_result = await agent.execute(list_task)
        assert list_result.status == "success"
        assert "test_collaborator" in list_result.data["collaborators"]

    @pytest.mark.asyncio
    async def test_collaboration_agent_collaborate(self):
        """Test that CollaborationAgent can handle collaboration."""
        settings = Settings()
        agent = CollaborationAgent("test-collab", settings)

        # Handle collaboration
        collab_task = Task(
            id="collab-task",
            type="collaborate",
            parameters={"message": {"content": "test collaboration"}},
        )

        collab_result = await agent.execute(collab_task)
        assert collab_result.status == "success"
        assert "Collaboration handled" in collab_result.data["response"]


if __name__ == "__main__":
    pytest.main([__file__])

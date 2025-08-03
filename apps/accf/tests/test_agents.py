"""
Tests for the ACCF agents package.
"""

import pytest
import asyncio
from accf_agents import Settings, AgentOrchestrator
from accf_agents.agents import Task, Result, ConsultAgent, KnowledgeAgent


class TestSettings:
    """Test the Settings class."""

    def test_settings_creation(self):
        """Test that settings can be created."""
        settings = Settings()
        assert settings.log_level == "INFO"
        assert settings.debug is False
        assert settings.host == "0.0.0.0"
        assert settings.port == 8000

    def test_settings_optional_fields(self):
        """Test that optional fields work correctly."""
        settings = Settings()
        # These should be None by default for testing
        assert settings.neo4j_password is None
        assert settings.openai_api_key is None


class TestTaskAndResult:
    """Test Task and Result models."""

    def test_task_creation(self):
        """Test that tasks can be created."""
        task = Task(id="test-task", type="test", parameters={"test": "data"})
        assert task.id == "test-task"
        assert task.type == "test"
        assert task.parameters == {"test": "data"}

    def test_result_creation(self):
        """Test that results can be created."""
        result = Result(task_id="test-task", status="success", data={"result": "test"})
        assert result.task_id == "test-task"
        assert result.status == "success"
        assert result.data == {"result": "test"}


class TestConsultAgent:
    """Test the ConsultAgent."""

    def test_consult_agent_creation(self):
        """Test that ConsultAgent can be created."""
        settings = Settings()
        agent = ConsultAgent("test-consult", settings)
        assert agent.name == "test-consult"
        assert agent.model == "o3"
        assert agent.assistant_name == "Architect_o3"

    def test_consult_agent_capabilities(self):
        """Test that ConsultAgent has correct capabilities."""
        settings = Settings()
        agent = ConsultAgent("test-consult", settings)
        capabilities = agent.get_capabilities()
        assert "consult" in capabilities
        assert "prompt_generation" in capabilities
        assert "architect" in capabilities

    def test_consult_agent_can_handle(self):
        """Test that ConsultAgent can handle correct task types."""
        settings = Settings()
        agent = ConsultAgent("test-consult", settings)
        assert agent.can_handle("consult") is True
        assert agent.can_handle("prompt_generation") is True
        assert agent.can_handle("unknown") is False

    @pytest.mark.asyncio
    async def test_consult_agent_execute(self):
        """Test that ConsultAgent can execute tasks."""
        settings = Settings()
        agent = ConsultAgent("test-consult", settings)

        task = Task(
            id="test-task", type="consult", parameters={"prompt": "test prompt"}
        )

        result = await agent.execute(task)
        assert result.task_id == "test-task"
        assert result.status == "success"
        assert "session_id" in result.data


class TestKnowledgeAgent:
    """Test the KnowledgeAgent."""

    def test_knowledge_agent_creation(self):
        """Test that KnowledgeAgent can be created."""
        settings = Settings()
        agent = KnowledgeAgent("test-knowledge", settings)
        assert agent.name == "test-knowledge"

    def test_knowledge_agent_capabilities(self):
        """Test that KnowledgeAgent has correct capabilities."""
        settings = Settings()
        agent = KnowledgeAgent("test-knowledge", settings)
        capabilities = agent.get_capabilities()
        assert "knowledge_search" in capabilities
        assert "knowledge_store" in capabilities
        assert "knowledge_retrieve" in capabilities
        assert "knowledge_manage" in capabilities

    @pytest.mark.asyncio
    async def test_knowledge_agent_search(self):
        """Test that KnowledgeAgent can search."""
        settings = Settings()
        agent = KnowledgeAgent("test-knowledge", settings)

        task = Task(
            id="test-task",
            type="knowledge_search",
            parameters={"query": "test query", "limit": 5},
        )

        result = await agent.execute(task)
        assert result.task_id == "test-task"
        assert result.status == "success"
        assert "results" in result.data
        assert len(result.data["results"]) <= 5


class TestAgentOrchestrator:
    """Test the AgentOrchestrator."""

    @pytest.mark.asyncio
    async def test_orchestrator_creation(self):
        """Test that AgentOrchestrator can be created."""
        settings = Settings()
        orchestrator = AgentOrchestrator(settings)
        assert orchestrator.settings == settings

    @pytest.mark.asyncio
    async def test_orchestrator_initialization(self):
        """Test that AgentOrchestrator can be initialized."""
        settings = Settings()
        orchestrator = AgentOrchestrator(settings)
        await orchestrator.initialize()
        assert orchestrator._initialized is True

    @pytest.mark.asyncio
    async def test_orchestrator_agent_status(self):
        """Test that AgentOrchestrator can provide agent status."""
        settings = Settings()
        orchestrator = AgentOrchestrator(settings)
        await orchestrator.initialize()

        status = orchestrator.get_agent_status()
        assert "total_agents" in status
        assert "agents" in status
        assert isinstance(status["total_agents"], int)
        assert isinstance(status["agents"], dict)


if __name__ == "__main__":
    pytest.main([__file__])

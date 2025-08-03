"""
Test the ConsultAgent with the new 'design' artifact type.

This test verifies that the ConsultAgent can handle design-related requests
and properly applies the design artifact guidance.
"""

import pytest
from accf_agents.agents.consult_agent import ConsultAgent
from accf_agents.agents.base import Task
from accf_agents import Settings


class TestConsultAgentDesign:
    """Test ConsultAgent with design artifact type."""

    @pytest.fixture
    def consult_agent(self):
        """Create a ConsultAgent instance for testing."""
        settings = Settings()
        return ConsultAgent("test_consult", settings)

    def test_consult_agent_can_handle_design(self, consult_agent):
        """Test that ConsultAgent can handle 'design' task type."""
        assert consult_agent.can_handle("design") is True
        assert "design" in consult_agent.get_capabilities()

    def test_design_artifact_guidance_exists(self, consult_agent):
        """Test that design artifact guidance is properly defined."""
        guidance = consult_agent._get_artifact_guidance("design")
        assert guidance is not None
        assert len(guidance) > 0
        assert "ARTIFACT TYPE: DESIGN" in guidance
        assert "SOLUTION ARCHITECT" in guidance
        assert "System design, architecture" in guidance

    @pytest.mark.asyncio
    async def test_design_task_execution(self, consult_agent):
        """Test executing a design task."""
        task = Task(
            id="test-design-1",
            type="design",
            parameters={
                "prompt": "Design a microservices architecture for an e-commerce platform",
                "session_id": "test-session",
                "artifact_type": "design",
            },
        )

        result = await consult_agent.execute(task)

        assert result.status == "success"
        assert result.task_id == "test-design-1"
        assert "artifact_type" in result.data
        assert result.data["artifact_type"] == "design"
        assert "enhanced_prompt" in result.data
        assert "ARTIFACT TYPE: DESIGN" in result.data["enhanced_prompt"]

    def test_build_enhanced_prompt_with_design(self, consult_agent):
        """Test building enhanced prompt with design artifact type."""
        prompt = "Create a system design for a real-time chat application"
        enhanced_prompt = consult_agent._build_enhanced_prompt(
            prompt=prompt, artifact_type="design", file_paths=["requirements.md"]
        )

        assert "ARTIFACT TYPE: DESIGN" in enhanced_prompt
        assert "SOLUTION ARCHITECT" in enhanced_prompt
        assert prompt in enhanced_prompt
        assert "Attached files: requirements.md" in enhanced_prompt

    def test_all_artifact_types_available(self, consult_agent):
        """Test that all artifact types are available."""
        artifact_types = [
            "answer",
            "plan",
            "code",
            "prompt",
            "test",
            "doc",
            "design",
            "diagram",
            "query",
            "rule",
            "config",
            "schema",
            "workflow",
            "docker",
            "env",
        ]

        for artifact_type in artifact_types:
            guidance = consult_agent._get_artifact_guidance(artifact_type)
            assert guidance is not None
            assert len(guidance) > 0
            # Check for the artifact type in the guidance (allowing for variations)
            assert "ARTIFACT TYPE:" in guidance
            assert (
                artifact_type.upper() in guidance
                or f" {artifact_type.upper()}" in guidance
            )

    def test_invalid_artifact_type_handling(self, consult_agent):
        """Test handling of invalid artifact type."""
        guidance = consult_agent._get_artifact_guidance("invalid_type")
        assert guidance == ""

    @pytest.mark.asyncio
    async def test_design_task_with_file_paths(self, consult_agent):
        """Test design task with file paths."""
        task = Task(
            id="test-design-2",
            type="design",
            parameters={
                "prompt": "Design a database schema for a user management system",
                "session_id": "test-session",
                "artifact_type": "design",
                "file_paths": ["database_requirements.md", "api_spec.yaml"],
            },
        )

        result = await consult_agent.execute(task)

        assert result.status == "success"
        assert result.data["file_paths"] == [
            "database_requirements.md",
            "api_spec.yaml",
        ]
        assert "database_requirements.md" in result.data["enhanced_prompt"]
        assert "api_spec.yaml" in result.data["enhanced_prompt"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

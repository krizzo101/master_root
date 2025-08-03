"""
Test model parameter validation for ConsultAgent.

This test verifies that the ConsultAgent properly validates model parameters
against @953-openai-api-standards.mdc and rejects unauthorized models.
"""

import pytest
from accf_agents.agents.consult_agent import ConsultAgent
from accf_agents.agents.base import Task
from accf_agents import Settings


class TestConsultAgentModelValidation:
    """Test ConsultAgent model parameter validation."""

    @pytest.fixture
    def consult_agent(self):
        """Create a ConsultAgent instance for testing."""
        settings = Settings()
        return ConsultAgent("test_consult", settings)

    @pytest.mark.asyncio
    async def test_approved_models_accepted(self, consult_agent):
        """Test that all approved models are accepted."""
        approved_models = ["o4-mini", "o3", "gpt-4.1-mini", "gpt-4.1", "gpt-4.1-nano"]

        for model in approved_models:
            task = Task(
                id=f"test-{model}",
                type="consult",
                parameters={
                    "prompt": "Test prompt",
                    "model": model,
                },
            )

            # Should not raise an error
            result = await consult_agent.execute(task)
            assert result.status == "success"
            assert result.data["model"] == model

    @pytest.mark.asyncio
    async def test_unauthorized_models_rejected(self, consult_agent):
        """Test that unauthorized models are rejected with clear error."""
        unauthorized_models = [
            "gpt-4o",
            "gpt-4o-mini",
            "gpt-4o-2024-07-01",
            "claude-3",
            "claude-3-opus",
            "claude-3-sonnet",
            "gemini-pro",
            "gemini-1.5-pro",
            "llama-3",
            "mistral-large",
            "mixtral-8x7b",
        ]

        for model in unauthorized_models:
            task = Task(
                id=f"test-{model}",
                type="consult",
                parameters={
                    "prompt": "Test prompt",
                    "model": model,
                },
            )

            # Should return error status with clear error message
            result = await consult_agent.execute(task)
            assert result.status == "error"
            assert "UNAUTHORIZED MODEL" in result.error_message
            assert model in result.error_message
            assert "Only approved models are allowed" in result.error_message

    @pytest.mark.asyncio
    async def test_default_model_when_none_provided(self, consult_agent):
        """Test that default model is used when no model is provided."""
        task = Task(
            id="test-default",
            type="consult",
            parameters={
                "prompt": "Test prompt",
                # No model parameter
            },
        )

        result = await consult_agent.execute(task)
        assert result.status == "success"
        assert result.data["model"] == "o3"  # Default model

    @pytest.mark.asyncio
    async def test_model_parameter_in_response(self, consult_agent):
        """Test that the selected model is included in the response."""
        task = Task(
            id="test-model-response",
            type="consult",
            parameters={
                "prompt": "Test prompt",
                "model": "gpt-4.1-mini",
            },
        )

        result = await consult_agent.execute(task)
        assert result.status == "success"
        assert result.data["model"] == "gpt-4.1-mini"

    @pytest.mark.asyncio
    async def test_case_sensitive_model_names(self, consult_agent):
        """Test that model names are case-sensitive."""
        invalid_case_models = [
            "O4-MINI",
            "O3",
            "GPT-4.1-MINI",
            "GPT-4.1",
            "GPT-4.1-NANO",
        ]

        for model in invalid_case_models:
            task = Task(
                id=f"test-case-{model}",
                type="consult",
                parameters={
                    "prompt": "Test prompt",
                    "model": model,
                },
            )

            result = await consult_agent.execute(task)
            assert result.status == "error"
            assert "UNAUTHORIZED MODEL" in result.error_message
            assert model in result.error_message

    @pytest.mark.asyncio
    async def test_empty_string_model_rejected(self, consult_agent):
        """Test that empty string model is rejected."""
        task = Task(
            id="test-empty-model",
            type="consult",
            parameters={
                "prompt": "Test prompt",
                "model": "",
            },
        )

        result = await consult_agent.execute(task)
        assert result.status == "error"
        assert "UNAUTHORIZED MODEL" in result.error_message
        assert "Only approved models are allowed" in result.error_message

    @pytest.mark.asyncio
    async def test_whitespace_only_model_rejected(self, consult_agent):
        """Test that whitespace-only model is rejected."""
        task = Task(
            id="test-whitespace-model",
            type="consult",
            parameters={
                "prompt": "Test prompt",
                "model": "   ",
            },
        )

        result = await consult_agent.execute(task)
        assert result.status == "error"
        assert "UNAUTHORIZED MODEL" in result.error_message
        assert "Only approved models are allowed" in result.error_message


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

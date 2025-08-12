"""Test model validation and approved models enforcement."""

from unittest.mock import Mock, patch

import pytest
from local_shared.openai_interfaces.model_selector import APPROVED_MODELS, ModelSelector
from local_shared.openai_interfaces.responses_interface import OpenAIResponsesInterface


class TestModelValidation:
    """Test model validation and enforcement."""

    def test_approved_models_only(self):
        """Test that only approved models are used."""
        selector = ModelSelector()

        # Test all task types return approved models
        task_types = ["reasoning", "execution", "structured", "general"]

        for task_type in task_types:
            model = selector.select_optimal_model(
                task_type=task_type,
                require_structured_outputs=True,
                prefer_cost_effective=True,
            )
            assert (
                model in APPROVED_MODELS
            ), f"Model {model} not in approved list for {task_type}"

    def test_unauthorized_models_blocked(self):
        """Test that unauthorized models are blocked."""
        unauthorized_models = [
            "gpt-4o",
            "gpt-4o-mini",
            "gpt-4o-2024-08-06",
            "claude-3",
            "gemini-pro",
            "llama-2",
        ]

        selector = ModelSelector()

        # Should never return unauthorized models
        for _ in range(100):  # Test multiple selections
            model = selector.select_optimal_model()
            assert (
                model not in unauthorized_models
            ), f"Unauthorized model {model} returned"

    def test_model_selector_parameters(self):
        """Test ModelSelector parameter handling."""
        selector = ModelSelector()

        # Test reasoning tasks
        reasoning_model = selector.select_optimal_model(
            task_type="reasoning", complexity="standard"
        )
        assert reasoning_model in ["o4-mini", "o3"]

        # Test execution tasks
        execution_model = selector.select_optimal_model(
            task_type="execution", require_structured_outputs=True
        )
        assert execution_model in ["gpt-4.1", "gpt-4.1-mini"]

        # Test cost-effective preference
        cost_effective = selector.select_optimal_model(prefer_cost_effective=True)
        assert cost_effective in ["gpt-4.1-mini", "gpt-4.1-nano", "o4-mini"]

    def test_responses_interface_models(self):
        """Test that responses interface uses approved models."""
        interface = OpenAIResponsesInterface()

        # Check default models
        assert interface.default_model in APPROVED_MODELS

        # Test structured response model selection
        from pydantic import BaseModel

        class TestSchema(BaseModel):
            test_field: str

        with patch.object(interface.client, "chat") as mock_chat:
            mock_chat.return_value.completions.parse.return_value = Mock(
                parsed=TestSchema(test_field="test")
            )

            # Should use approved model
            interface.create_structured_response(
                prompt="test", response_model=TestSchema
            )

            # Verify approved model was used
            call_args = mock_chat.return_value.completions.parse.call_args
            if call_args:
                model_used = call_args[1].get("model", interface.default_model)
                assert model_used in APPROVED_MODELS


class TestModelConstraints:
    """Test model constraint enforcement."""

    def test_no_fallback_to_unauthorized(self):
        """Test that there are no fallbacks to unauthorized models."""
        selector = ModelSelector()

        # Even with invalid task types, should return approved models
        model = selector.select_optimal_model(task_type="invalid_type")
        assert model in APPROVED_MODELS

    def test_reasoning_model_selection(self):
        """Test reasoning model selection logic."""
        selector = ModelSelector()

        # Standard complexity should use o4-mini
        model = selector.select_optimal_model(
            task_type="reasoning", complexity="standard"
        )
        assert model == "o4-mini"

        # High complexity should use o3
        model = selector.select_optimal_model(task_type="reasoning", complexity="high")
        assert model == "o3"

    def test_execution_model_selection(self):
        """Test execution model selection logic."""
        selector = ModelSelector()

        # Cost-effective execution
        model = selector.select_optimal_model(
            task_type="execution", prefer_cost_effective=True
        )
        assert model in ["gpt-4.1-nano", "gpt-4.1-mini"]

        # Performance execution
        model = selector.select_optimal_model(
            task_type="execution", prefer_cost_effective=False
        )
        assert model in ["gpt-4.1", "gpt-4.1-mini"]

    def test_structured_output_models(self):
        """Test structured output model selection."""
        selector = ModelSelector()

        model = selector.select_optimal_model(
            task_type="structured", require_structured_outputs=True
        )
        assert model in ["gpt-4.1", "gpt-4.1-mini"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

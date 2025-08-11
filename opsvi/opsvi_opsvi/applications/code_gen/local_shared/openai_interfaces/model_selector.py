"""
OpenAI Model Selection and Validation

This module validates and selects OpenAI models according to organizational rules.
Updated for July 2025 with structured outputs support.
"""

from typing import Set, Optional
import logging

logger = logging.getLogger(__name__)

# Approved OpenAI models (Rule 953 compliant) - STRICT ENFORCEMENT
# ONLY APPROVED MODELS - NO GPT-4O VARIANTS ALLOWED
APPROVED_MODELS: Set[str] = {
    # Approved reasoning models
    "o4-mini",
    "o3",
    # Approved execution models
    "gpt-4.1",
    "gpt-4.1-mini",
    "gpt-4.1-nano",
}

# Models specifically supporting structured outputs (subset of approved)
STRUCTURED_OUTPUTS_MODELS: Set[str] = {
    "gpt-4.1",
    "gpt-4.1-mini",
}

# Model categories for different use cases - APPROVED MODELS ONLY
REASONING_MODELS = [
    "o4-mini",  # Primary reasoning model
    "o3",  # Advanced reasoning
]

EXECUTION_MODELS = [
    "gpt-4.1-mini",  # Primary agent execution
    "gpt-4.1",  # Advanced execution
    "gpt-4.1-nano",  # Fast responses
]

STRUCTURED_OUTPUT_MODELS = [
    "gpt-4.1",  # Best for structured outputs
    "gpt-4.1-mini",  # Cost-effective structured outputs
]

REALTIME_MODELS = [
    "gpt-4.1-nano",  # Fast responses
    "gpt-4.1-mini",  # Efficient realtime
]

# Specific model configurations
AVAILABLE_MODELS = {
    "reasoning": ["o4-mini", "o3"],
    "execution": ["gpt-4.1-mini", "gpt-4.1", "gpt-4.1-nano"],
    "structured": ["gpt-4.1", "gpt-4.1-mini"],
}

# Default model selections - APPROVED MODELS ONLY
DEFAULT_STRUCTURED_MODEL = "gpt-4.1"
DEFAULT_SIMPLE_MODEL = "gpt-4.1-mini"
DEFAULT_REASONING_MODEL = "o3"  # For complex reasoning tasks


def validate_model_constraints(model: str) -> bool:
    """
    Validate that a model meets organizational constraints.

    Args:
        model: Model identifier to validate

    Returns:
        True if the model is approved, False otherwise
    """
    if model not in APPROVED_MODELS:
        logger.warning(
            f"Model {model} is not in approved list: {sorted(APPROVED_MODELS)}"
        )
        return False

    logger.debug(f"Model {model} validated successfully")
    return True


def supports_structured_outputs(model: str) -> bool:
    """
    Check if a model supports OpenAI's structured outputs feature.

    Args:
        model: Model identifier to check

    Returns:
        True if the model supports structured outputs, False otherwise
    """
    return model in STRUCTURED_OUTPUTS_MODELS


class ModelSelector:
    """Model selection and validation class."""

    def select_optimal_model(
        self,
        task_type: str = "general",
        require_structured_outputs: bool = False,
        prefer_cost_effective: bool = True,
        complexity: str = "standard",
    ) -> str:
        """Select the most appropriate model for the given task."""

        # Task-based selection with approved models only
        if task_type in ["reasoning", "planning", "analysis"]:
            return "o4-mini" if complexity == "standard" else "o3"

        elif task_type in ["execution", "coding", "implementation"]:
            if require_structured_outputs:
                return "gpt-4.1-mini" if prefer_cost_effective else "gpt-4.1"
            return "gpt-4.1-nano" if prefer_cost_effective else "gpt-4.1-mini"

        elif task_type == "structured":
            return "gpt-4.1-mini" if prefer_cost_effective else "gpt-4.1"

        elif require_structured_outputs:
            return "gpt-4.1-mini" if prefer_cost_effective else "gpt-4.1"

        else:
            # General purpose - fast execution model
            return "gpt-4.1-mini"


def get_model_info(model: str) -> dict:
    """
    Get information about a specific model.

    Args:
        model: Model identifier

    Returns:
        Dictionary with model information
    """
    info = {
        "model": model,
        "approved": validate_model_constraints(model),
        "supports_structured_outputs": supports_structured_outputs(model),
        "recommended_for": [],
    }

    # Add recommendations
    if model == DEFAULT_STRUCTURED_MODEL:
        info["recommended_for"].append("structured_outputs")
        info["recommended_for"].append("general_use")
    elif model == DEFAULT_SIMPLE_MODEL:
        info["recommended_for"].append("cost_effective")
        info["recommended_for"].append("simple_tasks")
    elif model == DEFAULT_REASONING_MODEL:
        info["recommended_for"].append("complex_reasoning")

    return info


def list_available_models() -> dict:
    """
    List all available models with their capabilities.

    Returns:
        Dictionary mapping model names to their information
    """
    return {model: get_model_info(model) for model in sorted(APPROVED_MODELS)}

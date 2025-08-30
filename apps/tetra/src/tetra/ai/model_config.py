"""
Model configuration with STRICT 2025 compliance.
NO FORBIDDEN MODELS. NO EXCEPTIONS. NO FALLBACKS.
"""

import logging
from enum import Enum
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class ModelConfig:
    """
    STRICT model configuration following 2025 OpenAI standards.
    ZERO TOLERANCE for forbidden models.
    """

    # APPROVED MODELS ONLY - 2025 Standards
    APPROVED_MODELS: Dict[str, List[str]] = {
        "reasoning": ["o4-mini", "o3"],  # O-series for reasoning
        "execution": ["gpt-5-mini", "gpt-5", "gpt-5-nano"],  # GPT-5 series for execution
    }

    # FORBIDDEN PATTERNS - ZERO TOLERANCE
    FORBIDDEN_PATTERNS = [
        "gpt-4o",  # ALL gpt-4o variants FORBIDDEN
        "gpt-4-turbo",  # FORBIDDEN
        "gpt-3.5",  # FORBIDDEN
        "claude",  # Third-party FORBIDDEN for OpenAI operations
        "gemini",  # Third-party FORBIDDEN
        "llama",  # Third-party FORBIDDEN
        "mistral",  # Third-party FORBIDDEN
        "gpt-4-",  # ANY gpt-4 variant FORBIDDEN
        "text-",  # Legacy models FORBIDDEN
        "davinci",  # Legacy models FORBIDDEN
        "curie",  # Legacy models FORBIDDEN
        "babbage",  # Legacy models FORBIDDEN
        "ada",  # Legacy models FORBIDDEN
    ]

    def __init__(self):
        """Initialize with STRICT validation."""
        self.validate_configuration()
        logger.info("✅ ModelConfig initialized with STRICT 2025 compliance")

    def get_model_for_task(self, task_type: str) -> str:
        """
        Get approved model for task type.
        NO FALLBACKS to forbidden models.

        Args:
            task_type: Type of task ("reasoning" or "execution")

        Returns:
            Approved model name

        Raises:
            ValueError: If no approved model available
        """
        if task_type not in self.APPROVED_MODELS:
            raise ValueError(f"Unknown task type: {task_type}. Use 'reasoning' or 'execution'")

        models = self.APPROVED_MODELS[task_type]
        if not models:
            raise ValueError(f"No approved models configured for {task_type}")

        # Use first available approved model
        model = models[0]

        # STRICT validation before returning
        self._validate_not_forbidden(model)

        logger.info(f"Selected approved model for {task_type}: {model}")
        return model

    def validate_configuration(self) -> None:
        """
        Validate ALL configured models against STRICT standards.
        FAILS FAST if any forbidden model detected.
        """
        logger.info("Running STRICT model validation...")

        for task_type, models in self.APPROVED_MODELS.items():
            for model in models:
                self._validate_not_forbidden(model)
                logger.info(f"✅ {task_type}: {model} - APPROVED")

        logger.info("✅ All models passed STRICT validation")

    def _validate_not_forbidden(self, model: str) -> None:
        """
        Validate model is NOT forbidden.
        ZERO TOLERANCE policy.

        Args:
            model: Model name to validate

        Raises:
            ValueError: If model is forbidden
        """
        model_lower = model.lower()

        for pattern in self.FORBIDDEN_PATTERNS:
            if pattern in model_lower:
                error_msg = f"""
❌ FORBIDDEN MODEL DETECTED: {model}
Pattern matched: {pattern}

This model is EXPLICITLY FORBIDDEN by 2025 OpenAI standards.
Only the following models are approved:
- Reasoning: o3, o4-mini
- Execution: gpt-5, gpt-5-mini, gpt-5-nano

NO EXCEPTIONS. NO FALLBACKS. NO WORKAROUNDS.
"""
                logger.error(error_msg)
                raise ValueError(error_msg)

    def is_model_approved(self, model: str) -> bool:
        """
        Check if model is approved.

        Args:
            model: Model name to check

        Returns:
            True if approved, False otherwise
        """
        try:
            self._validate_not_forbidden(model)

            # Check if in approved lists
            for models in self.APPROVED_MODELS.values():
                if model in models:
                    return True

            # Check if matches approved patterns
            approved_prefixes = ["o3", "o4-mini", "gpt-5"]
            for prefix in approved_prefixes:
                if model.startswith(prefix):
                    return True

            return False

        except ValueError:
            return False

    def get_all_approved_models(self) -> Dict[str, List[str]]:
        """Get all approved models by category."""
        return self.APPROVED_MODELS.copy()

    def add_approved_model(self, task_type: str, model: str) -> None:
        """
        Add a new approved model (with STRICT validation).

        Args:
            task_type: Task type for the model
            model: Model name to add

        Raises:
            ValueError: If model is forbidden
        """
        # STRICT validation first
        self._validate_not_forbidden(model)

        if task_type not in self.APPROVED_MODELS:
            self.APPROVED_MODELS[task_type] = []

        if model not in self.APPROVED_MODELS[task_type]:
            self.APPROVED_MODELS[task_type].append(model)
            logger.info(f"✅ Added approved model {model} for {task_type}")
        else:
            logger.info(f"Model {model} already approved for {task_type}")


# Global instance for easy access
_model_config: Optional[ModelConfig] = None


def get_model_config() -> ModelConfig:
    """Get global ModelConfig instance with STRICT validation."""
    global _model_config
    if _model_config is None:
        _model_config = ModelConfig()
    return _model_config

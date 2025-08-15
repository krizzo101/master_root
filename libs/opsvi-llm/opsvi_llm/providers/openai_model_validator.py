"""
OpenAI Model Validator - Enforces 2025 API Standards

Implements strict model validation per rule 953-openai-api-standards.mdc
"""

import logging
from typing import Set, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class ModelType(Enum):
    """Task-based model categorization"""
    REASONING = "reasoning"
    EXECUTION = "execution"
    FAST_RESPONSE = "fast_response"
    STRUCTURED_OUTPUT = "structured_output"


class OpenAIModelValidator:
    """
    Enforces strict OpenAI model constraints per 2025 standards.
    
    CRITICAL: Only approved models are allowed.
    """
    
    # APPROVED MODELS ONLY (2025 Standards)
    APPROVED_OPENAI_MODELS: Set[str] = {
        # O-series (Reasoning focused)
        "o4-mini",      # Primary reasoning model
        "o3",           # Advanced reasoning
        
        # GPT-5 series (Execution focused)
        "gpt-5-mini",   # Primary execution model
        "gpt-5",        # Advanced execution
        "gpt-5-nano",   # Fast responses
    }
    
    # FORBIDDEN MODELS - ZERO TOLERANCE
    FORBIDDEN_PATTERNS: Set[str] = {
        "gpt-4o",       # All gpt-4o variants prohibited
        "gpt-4o-mini",
        "gpt-4o-2024",
        "gpt-3.5",      # Legacy models prohibited
        "gpt-4",        # Old GPT-4 prohibited (except gpt-4-turbo for specific legacy cases)
    }
    
    # Task-based model selection
    TASK_MODEL_MAPPING = {
        ModelType.REASONING: ["o4-mini", "o3"],
        ModelType.EXECUTION: ["gpt-5-mini", "gpt-5"],
        ModelType.FAST_RESPONSE: ["gpt-5-nano", "gpt-5-mini"],
        ModelType.STRUCTURED_OUTPUT: ["gpt-5", "gpt-5-mini"],
    }
    
    @classmethod
    def validate_model(cls, model_name: str) -> bool:
        """
        Validate if a model is approved for use.
        
        Args:
            model_name: The model identifier to validate
            
        Returns:
            True if model is approved
            
        Raises:
            ValueError: If model is forbidden or unauthorized
        """
        if not model_name:
            raise ValueError("Model name cannot be empty")
        
        # Check if model is explicitly approved
        if model_name in cls.APPROVED_OPENAI_MODELS:
            logger.debug(f"✅ Model '{model_name}' is approved")
            return True
        
        # Check for forbidden patterns
        for forbidden in cls.FORBIDDEN_PATTERNS:
            if forbidden in model_name.lower():
                error_msg = (
                    f"❌ UNAUTHORIZED MODEL DETECTED: {model_name}\n"
                    f"This model is FORBIDDEN per 2025 OpenAI standards.\n"
                    f"Approved models only: {', '.join(sorted(cls.APPROVED_OPENAI_MODELS))}"
                )
                logger.error(error_msg)
                raise ValueError(error_msg)
        
        # Model not in approved list
        error_msg = (
            f"❌ UNAUTHORIZED MODEL: {model_name}\n"
            f"Only approved models are allowed: {', '.join(sorted(cls.APPROVED_OPENAI_MODELS))}"
        )
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    @classmethod
    def select_model_for_task(cls, task_type: ModelType, complexity: str = "standard") -> str:
        """
        Select optimal model based on task type and complexity.
        
        Args:
            task_type: Type of task (reasoning, execution, etc.)
            complexity: Task complexity level ("simple", "standard", "complex")
            
        Returns:
            Recommended model name
        """
        available_models = cls.TASK_MODEL_MAPPING.get(task_type, ["gpt-5-mini"])
        
        if complexity == "simple" and len(available_models) > 1:
            # Use lighter model for simple tasks
            return available_models[0]
        elif complexity == "complex" and len(available_models) > 1:
            # Use more powerful model for complex tasks
            return available_models[-1]
        else:
            # Default to first available model
            return available_models[0]
    
    @classmethod
    def get_model_config(cls, model_name: str) -> dict:
        """
        Get optimal configuration for a specific model.
        
        Args:
            model_name: The model to configure
            
        Returns:
            Configuration dictionary with model-specific optimizations
        """
        # Validate model first
        cls.validate_model(model_name)
        
        # O-series models (reasoning focused)
        if model_name in ["o3", "o4-mini"]:
            return {
                "model": model_name,
                "reasoning_effort": "high",  # Thorough analysis
                "verbosity": "concise",      # Controlled output
                # O-series models reason internally, no chain-of-thought needed
                "avoid_prompts": [
                    "Think step by step",
                    "Let's break this down",
                    "First, let me analyze"
                ]
            }
        
        # GPT-5 series (execution focused)
        elif model_name in ["gpt-5", "gpt-5-mini", "gpt-5-nano"]:
            return {
                "model": model_name,
                "include_reasoning": True,   # Explicit reasoning steps
                "detailed_guidance": True,   # Comprehensive instructions
                "persistence": "complete",   # Continue until resolved
            }
        
        # Default configuration
        return {"model": model_name}
    
    @classmethod
    def enforce_compliance(cls, config: dict) -> dict:
        """
        Enforce compliance on a configuration dictionary.
        
        Args:
            config: Configuration dictionary potentially containing model settings
            
        Returns:
            Validated and compliant configuration
        """
        if "model" in config:
            cls.validate_model(config["model"])
        
        if "default_model" in config:
            cls.validate_model(config["default_model"])
        
        if "fallback_model" in config:
            # NO FALLBACKS ALLOWED per standards
            logger.warning("Removing fallback_model - fallbacks are prohibited")
            del config["fallback_model"]
        
        return config
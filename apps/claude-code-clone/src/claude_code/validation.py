"""Model validation for Claude Code Clone - 2025 OpenAI Standards Compliance."""

from typing import Set


class ModelValidationError(Exception):
    """Error raised when unauthorized models are detected."""
    pass


class ModelValidator:
    """Validates model usage according to 2025 OpenAI standards."""
    
    # ✅ APPROVED MODELS ONLY - 2025 STANDARDS
    APPROVED_MODELS: Set[str] = {
        "o4-mini",      # ✅ APPROVED - Reasoning
        "o3",           # ✅ APPROVED - Advanced reasoning  
        "gpt-5-mini",   # ✅ APPROVED - Agent execution
        "gpt-5",        # ✅ APPROVED - Advanced execution
        "gpt-5-nano",   # ✅ APPROVED - Fast responses
    }
    
    # ❌ FORBIDDEN MODELS - ZERO TOLERANCE
    FORBIDDEN_MODELS: Set[str] = {
        "gpt-4o", "gpt-4o-mini", "gpt-4o-2024", "gpt-4o-*",
        "claude-3", "claude-*", "anthropic/*",
        "gemini-pro", "gemini-*", "google/*",
        "llama-*", "mistral-*"
    }
    
    @classmethod
    def validate_model(cls, model_name: str) -> bool:
        """Validate model is approved - MANDATORY check."""
        if model_name not in cls.APPROVED_MODELS:
            raise ModelValidationError(
                f"UNAUTHORIZED MODEL: {model_name}\n"
                f"APPROVED MODELS ONLY: {', '.join(sorted(cls.APPROVED_MODELS))}\n"
                f"🔐 NO OVERRIDES - NO EXCEPTIONS - NO COMPATIBILITY EXCUSES"
            )
        return True
    
    @classmethod
    def validate_config(cls, config) -> bool:
        """Validate entire configuration for compliance."""
        # Validate model
        cls.validate_model(config.model)
        
        # Additional validations can be added here
        return True
    
    @classmethod
    def get_optimal_model(cls, task_type: str, complexity: str = "standard") -> str:
        """Dynamically select optimal approved model for task."""
        if task_type in ["reasoning", "planning", "analysis"]:
            return "o4-mini" if complexity == "standard" else "o3"
        elif task_type in ["execution", "coding", "generation"]:
            return "gpt-5-mini" if complexity == "standard" else "gpt-5"
        else:
            # Default fallback to approved model
            return "gpt-5-mini"

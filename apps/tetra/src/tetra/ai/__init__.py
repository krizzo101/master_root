"""AI adapters and controllers for Tetra."""

from .claude_adapter import ClaudeAdapter
from .hybrid_controller import HybridController
from .model_config import ModelConfig, get_model_config
from .openai_adapter import OpenAIAdapter

# Legacy alias for compatibility
HybridAIController = HybridController

__all__ = [
    "ClaudeAdapter",
    "HybridController",
    "HybridAIController",  # Legacy alias
    "OpenAIAdapter",
    "ModelConfig",
    "get_model_config",
]

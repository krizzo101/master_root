"""
Configuration for opsvi-llm.

Extends foundation configuration with LLM-specific settings.
"""

from opsvi_foundation import FoundationConfig
from pydantic import BaseModel, Field


class LLMConfig(BaseModel):
    """Configuration for opsvi-llm."""

    # Inherit foundation settings
    foundation: FoundationConfig = Field(default_factory=FoundationConfig.from_env)

    # Domain-specific settings can be added here

    @classmethod
    def from_env(cls) -> "LLMConfig":
        """Create configuration from environment variables."""
        return cls(
            foundation=FoundationConfig.from_env(),
        )


# Global configuration instance
config = LLMConfig.from_env()

"""
Configuration for opsvi-core.

Extends foundation configuration with core-specific settings.
"""

from opsvi_foundation import FoundationConfig
from pydantic import BaseModel, Field


class CoreConfig(BaseModel):
    """Configuration for opsvi-core."""

    # Inherit foundation settings
    foundation: FoundationConfig = Field(default_factory=FoundationConfig.from_env)

    # Core-specific settings
    agent_timeout: int = Field(default=120, description="Agent operation timeout")
    max_agents: int = Field(default=10, description="Maximum concurrent agents")

    @classmethod
    def from_env(cls) -> "CoreConfig":
        """Create configuration from environment variables."""
        return cls(
            foundation=FoundationConfig.from_env(),
        )


# Global configuration instance
config = CoreConfig.from_env()

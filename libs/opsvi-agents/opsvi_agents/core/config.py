"""
Configuration for opsvi-agents.

Extends foundation configuration with Agents-specific settings.
"""

from typing import Optional
from pydantic import BaseModel, Field
from opsvi_foundation import FoundationConfig


class AgentsConfig(BaseModel):
    """Configuration for opsvi-agents."""
    
    # Inherit foundation settings
    foundation: FoundationConfig = Field(default_factory=FoundationConfig.from_env)
    
    # Domain-specific settings can be added here
    
    @classmethod
    def from_env(cls) -> "AgentsConfig":
        """Create configuration from environment variables."""
        return cls(
            foundation=FoundationConfig.from_env(),
        )


# Global configuration instance
config = AgentsConfig.from_env()

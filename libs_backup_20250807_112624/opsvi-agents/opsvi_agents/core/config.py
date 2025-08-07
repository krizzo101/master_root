"""
Configuration management for opsvi-agents.

Provides configuration loading, validation, and management for all opsvi-agents components.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from pydantic import BaseModel, Field

from opsvi_foundation.config.settings import BaseSettings


class AgentsConfig(BaseSettings):
    """Configuration for opsvi-agents components."""
    
    # Add library-specific configuration fields here
    enabled: bool = Field(default=True, description="Enable opsvi-agents functionality")
    debug: bool = Field(default=False, description="Enable debug mode")
    
    class Config:
        env_prefix = "OPSVI-AGENTS_"


class AgentsSettings(BaseSettings):
    """Global settings for opsvi-agents."""
    
    config: AgentsConfig = Field(default_factory=AgentsConfig)
    
    class Config:
        env_prefix = "OPSVI-AGENTS_"


# Global settings instance
settings = AgentsSettings()
